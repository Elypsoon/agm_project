import os
import tempfile
import base64
import threading
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from src.utils.rabbitmq_publisher import publish_event
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import HttpResponse
from src.generators.excel_generator import (
    generate_calificaciones_excel,
    generate_asistencias_excel,
    generate_rendimiento_excel,
    generate_consolidated_excel,
)
from src.generators.pdf_generator import (
    generate_calificaciones_pdf,
    generate_asistencias_pdf,
    generate_rendimiento_pdf,
)

from src.grpc.alumnos_client import AlumnosGRPCClient
from src.grpc.asistencias_client import AsistenciasGRPCClient
from src.grpc.calificaciones_client import CalificacionesGRPCClient
from src.grpc.periodos_client import PeriodosGRPCClient
from src.models.reportes import EstadisticasSnapshot, ReporteCache


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _enriquecer_con_asistencia(alumnos, materia_id):
    enriched = []
    for alumno in alumnos:
        asistencia = AsistenciasGRPCClient.obtener_asistencia_alumno(
            alumno_id=alumno.get('alumno_id'),
            materia_id=materia_id,
        )
        alumno['asistencia'] = asistencia.get('porcentaje', 0.0) if asistencia else 0.0
        alumno['presentes'] = asistencia.get('total_presentes', 0) if asistencia else 0
        alumno['retardos'] = asistencia.get('total_retardos', 0) if asistencia else 0
        alumno['faltas'] = asistencia.get('total_ausentes', 0) if asistencia else 0
        alumno['calificacion'] = round(alumno.get('promedio_real', 0.0), 2)
        enriched.append(alumno)
    return enriched


import logging
logger = logging.getLogger(__name__)

def generar_y_enviar_reporte_async(materia_id, dest_email, formato, ext):
    try:
        datos_materia = CalificacionesGRPCClient.obtener_concentrado_materia(materia_id)
        if not datos_materia or not datos_materia.get('alumnos'):
            logger.error(f"[-] Error en reporte asíncrono para materia {materia_id}: No hay calificaciones.")
            return

        if ext == 'xlsx':
            datos_asistencias = []
            for al in datos_materia['alumnos']:
                asistencia = AsistenciasGRPCClient.obtener_asistencia_alumno(
                    alumno_id=al['alumno_id'],
                    materia_id=materia_id,
                )
                if asistencia:
                    datos_asistencias.append(asistencia)
                else:
                    datos_asistencias.append({
                        "alumno_id": al['alumno_id'],
                        "materia_id": materia_id,
                        "asistencias": []
                    })
            
            periodo_activo = PeriodosGRPCClient.obtener_periodo_activo() or {}
            periodo_nombre = periodo_activo.get("nombre", "PRIMAVERA 2026")
            docente_nombre = "M.C. LUIS YAEL MÉNDEZ SÁNCHEZ"
            
            archivo_bytes = generate_consolidated_excel(
                materia_id=materia_id,
                datos_calificaciones=datos_materia,
                datos_asistencias=datos_asistencias,
                periodo_nombre=periodo_nombre,
                docente_nombre=docente_nombre
            )
        else:
            alumnos_calif = _enriquecer_con_asistencia(datos_materia['alumnos'], materia_id)
            archivo_bytes = generate_calificaciones_pdf(materia_id, alumnos_calif)

        # Codificar los bytes a base64
        archivo_base64 = base64.b64encode(archivo_bytes).decode('utf-8')
        
        materia_nombre = datos_materia.get('materia_nombre', 'Materia Desconocida').upper()
        payload = {
            "email": dest_email,
            "materia_nombre": materia_nombre,
            "formato": formato.upper(),
            "archivo_base64": archivo_base64,
            "archivo_nombre": f"reporte_final_{materia_id}.{ext}"
        }
        
        success = publish_event('reporte.finalizado', payload)
        if success:
            logger.info(f"[+] Evento 'reporte.finalizado' encolado para {dest_email}")
        else:
            logger.error(f"[-] Falló encolado de evento 'reporte.finalizado' para {dest_email}")
            
    except Exception as e:
        logger.exception(f"[-] Excepción en hilo asíncrono para {materia_id}: {e}")


@api_view(['GET'])
@permission_classes([AllowAny])
def descargar_calificaciones(request, materia_id):
    formato = request.GET.get('formato', 'pdf').lower()
    ext = 'xlsx' if formato in ['xls', 'xlsx'] else 'pdf'
    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if ext == 'xlsx' else 'application/pdf'

    # Soporte para procesamiento asíncrono
    is_async = request.GET.get('async', 'false').lower() == 'true'
    dest_email = request.GET.get('email')

    if is_async and dest_email:
        # Lanzar un hilo en segundo plano para no bloquear la petición REST
        threading.Thread(
            target=generar_y_enviar_reporte_async,
            args=(materia_id, dest_email, formato, ext)
        ).start()
        
        return Response({
            "success": True,
            "message": f"La generación del reporte en formato {formato.upper()} ha comenzado en segundo plano. Recibirás un correo en {dest_email} con el archivo adjunto en cuanto esté listo."
        })

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

    datos_materia = CalificacionesGRPCClient.obtener_concentrado_materia(materia_id)
    if not datos_materia or not datos_materia.get('alumnos'):
        return Response({"error": "No hay calificaciones registradas o el servicio no está disponible."}, status=404)

    alumnos_calif = _enriquecer_con_asistencia(datos_materia['alumnos'], materia_id)

    if ext == 'xlsx':
        # Obtener asistencias de todos los alumnos de la materia para la segunda pestaña
        datos_asistencias = []
        for al in datos_materia['alumnos']:
            asistencia = AsistenciasGRPCClient.obtener_asistencia_alumno(
                alumno_id=al['alumno_id'],
                materia_id=materia_id,
            )
            if asistencia:
                datos_asistencias.append(asistencia)
            else:
                datos_asistencias.append({
                    "alumno_id": al['alumno_id'],
                    "materia_id": materia_id,
                    "asistencias": []
                })
        
        periodo_activo = PeriodosGRPCClient.obtener_periodo_activo() or {}
        periodo_nombre = periodo_activo.get("nombre", "PRIMAVERA 2026")
        docente_nombre = "M.C. LUIS YAEL MÉNDEZ SÁNCHEZ"
        
        archivo_bytes = generate_consolidated_excel(
            materia_id=materia_id,
            datos_calificaciones=datos_materia,
            datos_asistencias=datos_asistencias,
            periodo_nombre=periodo_nombre,
            docente_nombre=docente_nombre
        )
    else:
        archivo_bytes = generate_calificaciones_pdf(materia_id, alumnos_calif)

    fd, filepath = tempfile.mkstemp(suffix=f".{ext}", prefix=f"agm_calif_{materia_id}_")
    with os.fdopen(fd, 'wb') as f:
        f.write(archivo_bytes)

    ReporteCache.objects.create(
        materia_id=materia_id,
        tipo='calificaciones',
        formato=formato,
        archivo_path=filepath,
        valido_hasta=timezone.now() + timedelta(hours=1),
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

    alumnos = AlumnosGRPCClient.obtener_alumnos_materia(materia_id)
    if alumnos is None:
        cache_fallback = ReporteCache.objects.filter(
            materia_id=materia_id,
            tipo='asistencia',
            formato=formato,
            valido_hasta__gt=timezone.now(),
        ).first()
        if cache_fallback and os.path.exists(cache_fallback.archivo_path):
            with open(cache_fallback.archivo_path, 'rb') as f:
                return HttpResponse(f.read(), content_type=content_type)
        return Response({"error": "No se pudo obtener la lista de alumnos."}, status=503)

    datos_agregados = []
    for alumno in alumnos:
        asistencia = AsistenciasGRPCClient.obtener_asistencia_alumno(
            alumno_id=alumno['id'],
            materia_id=materia_id,
        )
        datos_agregados.append({
            "matricula": alumno.get('matricula', 'N/A'),
            "nombre": alumno.get('nombre', 'Desconocido'),
            "presentes": asistencia.get('total_presentes', 0) if asistencia else 0,
            "retardos": asistencia.get('total_retardos', 0) if asistencia else 0,
            "faltas": asistencia.get('total_ausentes', 0) if asistencia else 0,
        })

    if ext == 'xlsx':
        archivo_bytes = generate_asistencias_excel(materia_id, datos_agregados)
    else:
        archivo_bytes = generate_asistencias_pdf(materia_id, datos_agregados)

    fd, filepath = tempfile.mkstemp(suffix=f".{ext}", prefix=f"agm_asist_{materia_id}_")
    with os.fdopen(fd, 'wb') as f:
        f.write(archivo_bytes)

    ReporteCache.objects.create(
        materia_id=materia_id,
        tipo='asistencia',
        formato=formato,
        archivo_path=filepath,
        valido_hasta=timezone.now() + timedelta(hours=1),
    )

    response = HttpResponse(archivo_bytes, content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="asistencias_{materia_id}.{ext}"'
    return response


@api_view(['GET'])
@permission_classes([AllowAny])
def descargar_rendimiento(request, materia_id):
    formato = request.GET.get('formato', 'pdf').lower()
    ext = 'xlsx' if formato in ['xls', 'xlsx'] else 'pdf'
    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if ext == 'xlsx' else 'application/pdf'

    datos_materia = CalificacionesGRPCClient.obtener_concentrado_materia(materia_id)
    asistencia_global = AsistenciasGRPCClient.obtener_estadisticas_asistencia(materia_id)

    if not datos_materia or not datos_materia.get('alumnos') or asistencia_global is None:
        return Response({"error": "No hay datos suficientes para generar el reporte de rendimiento."}, status=404)

    alumnos_calif = _enriquecer_con_asistencia(datos_materia['alumnos'], materia_id)
    estadisticas_materia = CalificacionesGRPCClient.obtener_estadisticas_globales(materia_id) or {}
    periodo_activo = PeriodosGRPCClient.obtener_periodo_activo() or {"id": "N/A"}

    resumen = {
        "materia_id": materia_id,
        "materia_nombre": datos_materia.get('materia_nombre', 'Desconocida'),
        "periodo_id": periodo_activo.get('id', 'N/A'),
        "promedio_grupo": estadisticas_materia.get('promedio_grupo', 0.0),
        "calificacion_maxima": estadisticas_materia.get('calificacion_max', 0.0),
        "calificacion_minima": estadisticas_materia.get('calificacion_min', 0.0),
        "tasa_asistencia": asistencia_global.get('porcentaje_global', 0.0),
        "total_alumnos": estadisticas_materia.get('total_alumnos', len(alumnos_calif)),
    }

    if ext == 'xlsx':
        archivo_bytes = generate_rendimiento_excel(materia_id, resumen, alumnos_calif)
    else:
        archivo_bytes = generate_rendimiento_pdf(materia_id, resumen, alumnos_calif)

    fd, filepath = tempfile.mkstemp(suffix=f".{ext}", prefix=f"agm_rend_{materia_id}_")
    with os.fdopen(fd, 'wb') as f:
        f.write(archivo_bytes)

    ReporteCache.objects.create(
        materia_id=materia_id,
        tipo='rendimiento',
        formato=formato,
        archivo_path=filepath,
        valido_hasta=timezone.now() + timedelta(hours=1),
    )

    response = HttpResponse(archivo_bytes, content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="rendimiento_{materia_id}.{ext}"'
    return response


@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_estadisticas(request, materia_id):
    datos_materia = CalificacionesGRPCClient.obtener_concentrado_materia(materia_id)
    asistencia_global = AsistenciasGRPCClient.obtener_estadisticas_asistencia(materia_id)

    if not datos_materia or not datos_materia.get('alumnos'):
        return Response({"error": "No hay datos para generar estadísticas."}, status=404)

    alumnos_base = datos_materia['alumnos']
    total_alumnos = len(alumnos_base)
    promedio_grupo = sum(a['promedio_real'] for a in alumnos_base) / total_alumnos
    aprobados = sum(1 for a in alumnos_base if a['promedio_real'] >= 6.0)
    tasa_aprobacion = (aprobados / total_alumnos) * 100 if total_alumnos else 0.0
    tasa_asistencia = asistencia_global.get('porcentaje_global', 0.0) if asistencia_global else 0.0
    periodo_activo = PeriodosGRPCClient.obtener_periodo_activo() or {}
    periodo_id = periodo_activo.get('id', 'N/A') if periodo_activo else 'N/A'

    snapshot, created = EstadisticasSnapshot.objects.update_or_create(
        materia_id=materia_id,
        periodo_id=periodo_id,
        defaults={
            "promedio_grupo": round(promedio_grupo, 2),
            "tasa_aprobacion": round(tasa_aprobacion, 2),
            "tasa_asistencia": round(tasa_asistencia, 2),
            "total_alumnos": total_alumnos,
        }
    )

    return Response({
        "mensaje": "Estadísticas calculadas y guardadas correctamente.",
        "datos": {
            "snapshot_id": snapshot.id,
            "materia_id": materia_id,
            "total_alumnos": total_alumnos,
            "promedio_grupo": round(promedio_grupo, 2),
            "tasa_aprobacion": round(tasa_aprobacion, 2),
            "tasa_asistencia": round(tasa_asistencia, 2),
            "periodo_activo": periodo_activo.get('nombre') if periodo_activo else 'N/A',
            "fecha_generacion": snapshot.snapshot_date,
        },
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_estadisticas_docente(request, id):
    materias = PeriodosGRPCClient.obtener_materias_docente(id) or []
    
    # 1. Crear un diccionario de metadatos de materias para rápido acceso
    materias_dict = {
        m['materia_id']: {
            "nombre": m.get('nombre', 'Materia Desconocida'),
            "nrc": m.get('nrc', ''),
            "periodo_id": m.get('periodo_id', '')
        }
        for m in materias
    }
    
    # 2. Autogenerar de forma proactiva snapshots en BD para materias asignadas que aún no los posean
    for m in materias:
        m_id = m['materia_id']
        exists = EstadisticasSnapshot.objects.filter(materia_id=m_id).exists()
        if not exists:
            try:
                datos_materia = CalificacionesGRPCClient.obtener_concentrado_materia(m_id)
                if datos_materia and datos_materia.get('alumnos'):
                    alumnos_base = datos_materia['alumnos']
                    total_al = len(alumnos_base)
                    prom_g = sum(a['promedio_real'] for a in alumnos_base) / total_al if total_al > 0 else 0.0
                    aprob = sum(1 for a in alumnos_base if a['promedio_real'] >= 6.0)
                    tasa_aprob = (aprob / total_al) * 100 if total_al > 0 else 0.0
                    
                    asist_global = AsistenciasGRPCClient.obtener_estadisticas_asistencia(m_id)
                    tasa_asist = asist_global.get('porcentaje_global', 0.0) if asist_global else 0.0
                    
                    p_id = m.get('periodo_id', 'N/A')
                    
                    EstadisticasSnapshot.objects.create(
                        materia_id=m_id,
                        periodo_id=p_id,
                        promedio_grupo=round(prom_g, 2),
                        tasa_aprobacion=round(tasa_aprob, 2),
                        tasa_asistencia=round(tasa_asist, 2),
                        total_alumnos=total_al,
                    )
            except Exception as e:
                # Silenciar errores individuales de generación para no interrumpir el flujo
                pass

    # 3. Recuperar snapshots ordenados y enriquecidos con nombres y NRCs legibles
    materia_ids = [m['materia_id'] for m in materias]
    snapshots = EstadisticasSnapshot.objects.filter(materia_id__in=materia_ids).order_by('materia_id', 'snapshot_date')
    
    historial = []
    for s in snapshots:
        m_info = materias_dict.get(s.materia_id, {})
        historial.append({
            "periodo_id": s.periodo_id,
            "materia_id": s.materia_id,
            "materia_nombre": m_info.get("nombre", "DESARROLLO DE APLICACIONES WEB"),
            "nrc": m_info.get("nrc", ""),
            "promedio_grupo": float(s.promedio_grupo),
            "tasa_asistencia": float(s.tasa_asistencia),
            "tasa_aprobacion": float(s.tasa_aprobacion),
            "total_alumnos": s.total_alumnos,
            "generado_en": s.snapshot_date,
        })

    return Response({
        "success": True,
        "message": f"Historial del docente {id} recuperado y enriquecido correctamente.",
        "data": historial,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_estadisticas_alumno(request, id):
    materia_id = request.GET.get('materia_id')
    if not materia_id:
        return Response({
            "error": "Para obtener estadísticas individuales se requiere el parámetro materia_id en la consulta."},
            status=400
        )

    promedio = CalificacionesGRPCClient.obtener_promedio_alumno(alumno_id=id, materia_id=materia_id)
    asistencia = AsistenciasGRPCClient.obtener_asistencia_alumno(alumno_id=id, materia_id=materia_id)
    periodo_activo = PeriodosGRPCClient.obtener_periodo_activo()

    if promedio is None and asistencia is None:
        return Response({"error": "No se pudo obtener estadísticas del alumno para la materia indicada."}, status=404)

    resumen_alumno = {
        "alumno_id": id,
        "materia_id": materia_id,
        "periodo_activo": periodo_activo.get('nombre') if periodo_activo else 'N/A',
        "promedio_real": promedio.get('promedio_real') if promedio else None,
        "promedio_redondeado": promedio.get('promedio_redondeado') if promedio else None,
        "porcentaje_asistencia": asistencia.get('porcentaje') if asistencia else 0.0,
        "total_presentes": asistencia.get('total_presentes') if asistencia else 0,
        "total_retardos": asistencia.get('total_retardos') if asistencia else 0,
        "total_ausentes": asistencia.get('total_ausentes') if asistencia else 0,
    }

    return Response({
        "success": True,
        "message": f"Estadísticas del alumno {id} calculadas correctamente.",
        "data": resumen_alumno,
    })
