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

    alumnos_base = AlumnosGRPCClient.get_calificaciones(materia_id) 

    if not alumnos_base:
        return Response({"error": "No hay alumnos inscritos en esta materia."}, status=404)

    datos_asistencias = []
    for alumno in alumnos_base:
        datos_asistencias.append({
            "matricula": alumno['matricula'],
            "nombre": alumno['nombre'],
            "presentes": random.randint(20, 30),
            "retardos": random.randint(0, 5),
            "faltas": random.randint(0, 3)
        })

    # 3. Generar archivo
    if formato in ['xls', 'xlsx']:
        excel_bytes = generate_asistencias_excel(materia_id, datos_asistencias)
        response = HttpResponse(excel_bytes, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="asistencias_{materia_id}.xlsx"'
        return response

    elif formato == 'pdf':
        pdf_bytes = generate_asistencias_pdf(materia_id, datos_asistencias)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="asistencias_{materia_id}.pdf"'
        return response

    return Response({"error": "Formato no soportado"}, status=400)

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