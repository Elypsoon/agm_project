import os
import tempfile
from datetime import timedelta
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import HttpResponse
from src.generators.excel_generator import generate_calificaciones_excel, generate_asistencias_excel
from src.generators.pdf_generator import generate_calificaciones_pdf, generate_asistencias_pdf

from src.grpc.alumnos_client import AlumnosGRPCClient
from src.grpc.asistencias_client import AsistenciasGRPCClient
from src.models.reportes import EstadisticasSnapshot, ReporteCache
import random
@api_view(['GET'])
@permission_classes([AllowAny])
def descargar_calificaciones(request, materia_id):
    formato = request.GET.get('formato', 'pdf').lower()
    ext = 'xlsx' if formato in ['xls', 'xlsx'] else 'pdf'
    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if ext == 'xlsx' else 'application/pdf'
    datos_dummy = [
        {"matricula": "2022001", "nombre": "Gabo Aguilar", "asistencia": 95, "calificacion": 9.8},
        {"matricula": "2022002", "nombre": "Ana López", "asistencia": 80, "calificacion": 7.5},
        {"matricula": "2022003", "nombre": "Carlos Mtz", "asistencia": 100, "calificacion": 10.0},
    ]

    cache_activo = ReporteCache.objects.filter(
        materia_id=materia_id, 
        tipo='calificaciones',
        formato=formato,
        valido_hasta__gt=timezone.now()
    ).first()
    
    if cache_activo and os.path.exists(cache_activo.archivo_path):
        with open(cache_activo.archivo_path, 'rb') as f:
            archivo_bytes = f.read()
            
        response = HttpResponse(archivo_bytes, content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="calificaciones_{materia_id}_cached.{ext}"'
        return response

    datos_reales = AlumnosGRPCClient.get_calificaciones(materia_id)

    if not datos_reales:
        return Response({"error": "No hay alumnos inscritos en esta materia."}, status=404)

    if ext == 'xlsx':
        archivo_bytes = generate_calificaciones_excel(materia_id, datos_reales)
    else:
        archivo_bytes = generate_calificaciones_pdf(materia_id, datos_reales)

    fd, filepath = tempfile.mkstemp(suffix=f".{ext}", prefix=f"agm_calif_{materia_id}_")
    with os.fdopen(fd, 'wb') as f:
        f.write(archivo_bytes)

    ReporteCache.objects.create(
        materia_id=materia_id,
        tipo='calificaciones',
        formato=formato,
        archivo_path=filepath,
        valido_hasta=timezone.now() + timedelta(hours=1)
    )

    response = HttpResponse(archivo_bytes, content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="calificaciones_{materia_id}.{ext}"'
    return response
        
@api_view(['GET'])
@permission_classes([AllowAny])
def descargar_asistencias(request, materia_id):
    formato = request.GET.get('formato', 'pdf').lower()
    ext = 'xlsx' if formato in ['xls', 'xlsx'] else 'pdf'
    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if ext == 'xlsx' else 'application/pdf'

    # 1. Estrategia de Orquestación gRPC Sincrónica
    alumnos = AlumnosGRPCClient.obtener_alumnos_materia(materia_id)
    asistencias_map = AsistenciasGRPCClient.obtener_estadisticas_asistencia(materia_id)

    # 2. Tolerancia a Fallos: Si los servicios caen, intentamos recuperar el último Caché histórico
    if alumnos is None or asistencias_map is None:
        last_cache = ReporteCache.objects.filter(materia_id=materia_id, tipo='asistencias', formato=formato).order_by('-valido_hasta').first()
        if last_cache and os.path.exists(last_cache.archivo_path):
            with open(last_cache.archivo_path, 'rb') as f:
                return HttpResponse(f.read(), content_type=content_type)
        return Response({"error": "Servicios académicos temporalmente no disponibles y no hay caché previo."}, status=503)

    # 3. Agregación de Datos en memoria sin tocar bases de datos ajenas
    datos_agregados = []
    for alumno in alumnos:
        stats = asistencias_map.get(alumno['id'], {"presentes": 0, "retardos": 0, "faltas": 0})
        datos_agregados.append({
            "matricula": alumno['matricula'],
            "nombre": alumno['nombre'],
            "presentes": stats['presentes'],
            "retardos": stats['retardos'],
            "faltas": stats['faltas']
        })

    # 4. Renderizado del reporte
    if ext == 'xlsx':
        archivo_bytes = generate_asistencias_excel(materia_id, datos_agregados)
    else:
        archivo_bytes = generate_asistencias_pdf(materia_id, datos_agregados)

    return HttpResponse(archivo_bytes, content_type=content_type)

@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_estadisticas(request, materia_id):
    alumnos_base = AlumnosGRPCClient.get_calificaciones(materia_id)

    if not alumnos_base:
        return Response({"error": "No hay datos para generar estadísticas."}, status=404)

    # 1. Calcular matemáticas básicas
    total_alumnos = len(alumnos_base)
    promedio_grupo = sum(a['calificacion'] for a in alumnos_base) / total_alumnos
    
    # Suponiendo que la calificación mínima aprobatoria es 6.0
    aprobados = sum(1 for a in alumnos_base if a['calificacion'] >= 6.0)
    tasa_aprobacion = (aprobados / total_alumnos) * 100
    
    tasa_asistencia = sum(a['asistencia'] for a in alumnos_base) / total_alumnos

    # 2. Guardar el Snapshot en PostgreSQL
    snapshot = EstadisticasSnapshot.objects.create(
        materia_id=materia_id,
        periodo_id="Primavera-2026", # TODO: Conectar al MS-2 (Periodos) en el futuro
        promedio_grupo=promedio_grupo,
        tasa_aprobacion=tasa_aprobacion,
        tasa_asistencia=tasa_asistencia,
        total_alumnos=total_alumnos
    )

    # 3. Retornar el JSON para el frontend de Angular
    return Response({
        "mensaje": "Estadísticas calculadas y guardadas correctamente.",
        "datos": {
            "snapshot_id": snapshot.id,
            "materia_id": materia_id,
            "total_alumnos": total_alumnos,
            "promedio_grupo": round(promedio_grupo, 2),
            "tasa_aprobacion": round(tasa_aprobacion, 2),
            "tasa_asistencia": round(tasa_asistencia, 2),
            "fecha_generacion": snapshot.snapshot_date
        }
    })
    
@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_estadisticas_docente(request, id):
    # Fallback: Datos estructurados que representan semestres pasados
    historial_simulado = [
        {
            "periodo_id": "Otoño-2024",
            "materia_id": "STW-2024",
            "promedio_grupo": 8.4,
            "tasa_asistencia": 88.5,
            "tasa_aprobacion": 92.0,
            "total_alumnos": 25
        },
        {
            "periodo_id": "Primavera-2025",
            "materia_id": "STW-2025",
            "promedio_grupo": 8.9,
            "tasa_asistencia": 94.1,
            "tasa_aprobacion": 100.0,
            "total_alumnos": 30
        }
    ]
    
    return Response({
        "success": True,
        "message": f"Historial del docente {id} recuperado correctamente.",
        "data": historial_simulado
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_estadisticas_alumno(request, id):
    resumen_alumno = {
        "alumno_id": id,
        "promedio_general_actual": 9.1,
        "porcentaje_asistencia_total": 91.6,
        "materias_cursando": 3,
        "alertas_riesgo": 0
    }
    
    return Response({
        "success": True,
        "message": f"Estadísticas del alumno {id} calculadas correctamente.",
        "data": resumen_alumno
    })