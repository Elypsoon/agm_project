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

def generar_y_enviar_reporte_async(materia_id, dest_email, formato, ext, tipo_reporte):
    try:
        expiration_time = None
        # 1. Comprobar si ya existe un reporte válido en el caché
        try:
            cache_activo = ReporteCache.objects.filter(
                materia_id=materia_id,
                tipo=tipo_reporte if tipo_reporte == 'calificaciones' else 'asistencia',
                formato=formato,
                valido_hasta__gt=timezone.now()
            ).first()
        except Exception as e:
            logger.warning(f"[-] Database error while reading cache in background thread: {e}")
            cache_activo = None

        if cache_activo and os.path.exists(cache_activo.archivo_path):
            logger.info(f"[+] Hilo asíncrono (tipo: {tipo_reporte}) - Cache Hit para materia {materia_id}")
            with open(cache_activo.archivo_path, 'rb') as f:
                archivo_bytes = f.read()
            archivo_nombre = os.path.basename(cache_activo.archivo_path)
            expiration_time = cache_activo.valido_hasta
        else:
            logger.info(f"[+] Hilo asíncrono (tipo: {tipo_reporte}) - Cache Miss para materia {materia_id}")
            datos_materia = CalificacionesGRPCClient.obtener_concentrado_materia(materia_id)
            if not datos_materia or not datos_materia.get('alumnos'):
                logger.error(f"[-] Error en reporte asíncrono para materia {materia_id}: No hay calificaciones.")
                return

            periodo_activo = PeriodosGRPCClient.obtener_periodo_activo() or {}
            periodo_nombre = periodo_activo.get("nombre", "PRIMAVERA 2026")
            docente_nombre = "M.C. LUIS YAEL MÉNDEZ SÁNCHEZ"

            if tipo_reporte == 'calificaciones':
                if ext == 'xlsx':
                    archivo_bytes = generate_calificaciones_excel(
                        materia_id=materia_id,
                        datos_calificaciones=datos_materia,
                        periodo_nombre=periodo_nombre,
                        docente_nombre=docente_nombre
                    )
                else:
                    alumnos_calif = _enriquecer_con_asistencia(datos_materia['alumnos'], materia_id)
                    archivo_bytes = generate_calificaciones_pdf(materia_id, alumnos_calif)
                archivo_nombre = f"calificaciones_{materia_id}.{ext}"
            else:  # asistencias
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
                if ext == 'xlsx':
                    archivo_bytes = generate_asistencias_excel(
                        materia_id=materia_id,
                        datos_calificaciones=datos_materia,
                        datos_asistencias=datos_asistencias,
                        periodo_nombre=periodo_nombre,
                        docente_nombre=docente_nombre
                    )
                else:
                    datos_agregados = []
                    for al in datos_materia['alumnos']:
                        asist_sum = None
                        for sa in datos_asistencias:
                            if str(sa.get("alumno_id")) == str(al['alumno_id']):
                                asist_sum = sa
                                break
                        datos_agregados.append({
                            "matricula": al.get('matricula', 'N/A'),
                            "nombre": al.get('alumno_nombre', 'Desconocido'),
                            "presentes": asist_sum.get('total_presentes', 0) if asist_sum else 0,
                            "retardos": asist_sum.get('total_retardos', 0) if asist_sum else 0,
                            "faltas": asist_sum.get('total_ausentes', 0) if asist_sum else 0,
                        })
                    archivo_bytes = generate_asistencias_pdf(materia_id, datos_agregados)
                archivo_nombre = f"asistencias_{materia_id}.{ext}"

            # Guardar en caché local por 24 horas (timedelta(days=1))
            prefix_val = "agm_calif_" if tipo_reporte == 'calificaciones' else "agm_asist_"
            fd, filepath = tempfile.mkstemp(suffix=f".{ext}", prefix=f"{prefix_val}{materia_id}_")
            with os.fdopen(fd, 'wb') as f:
                f.write(archivo_bytes)

            valido_hasta = timezone.now() + timedelta(days=1)
            try:
                ReporteCache.objects.create(
                    materia_id=materia_id,
                    tipo=tipo_reporte if tipo_reporte == 'calificaciones' else 'asistencia',
                    formato=formato,
                    archivo_path=filepath,
                    valido_hasta=valido_hasta, # Válido por 24 horas (1 día)
                )
            except Exception as e:
                logger.warning(f"[-] Database error while writing cache in background thread: {e}")
            archivo_nombre = os.path.basename(filepath)
            expiration_time = valido_hasta

        # Formatear la fecha y hora local de expiración
        if expiration_time:
            try:
                from django.utils.timezone import localtime
                local_exp = localtime(expiration_time)
                fecha_expiracion_str = local_exp.strftime("%d/%m/%Y a las %H:%M")
            except Exception:
                fecha_expiracion_str = expiration_time.strftime("%d/%m/%Y a las %H:%M")
        else:
            try:
                from django.utils.timezone import localtime
                fecha_expiracion_str = (localtime(timezone.now()) + timedelta(days=1)).strftime("%d/%m/%Y a las %H:%M")
            except Exception:
                fecha_expiracion_str = (timezone.now() + timedelta(days=1)).strftime("%d/%m/%Y a las %H:%M")

        # Codificar los bytes a base64
        archivo_base64 = base64.b64encode(archivo_bytes).decode('utf-8')
        
        materia_nombre = "Materia Desconocida"
        try:
            datos_materia = CalificacionesGRPCClient.obtener_concentrado_materia(materia_id)
            if datos_materia:
                materia_nombre = datos_materia.get('materia_nombre', 'Materia Desconocida')
        except Exception:
            pass

        materia_nombre = materia_nombre.upper()
        formato_display = f"{formato.upper()} DE {tipo_reporte.upper()}"
        payload = {
            "email": dest_email,
            "materia_nombre": materia_nombre,
            "formato": formato_display,
            "archivo_base64": archivo_base64,
            "archivo_nombre": archivo_nombre,
            "fecha_expiracion": fecha_expiracion_str
        }
        
        success = publish_event('reporte.finalizado', payload)
        if success:
            logger.info(f"[+] Evento 'reporte.finalizado' (tipo: {tipo_reporte}) encolado para {dest_email}")
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
            args=(materia_id, dest_email, formato, ext, 'calificaciones')
        ).start()
        
        return Response({
            "success": True,
            "message": f"La generación del reporte de calificaciones en formato {formato.upper()} ha comenzado en segundo plano. Recibirás un correo en {dest_email} con el archivo adjunto en cuanto esté listo."
        })

    try:
        cache_activo = ReporteCache.objects.filter(
            materia_id=materia_id,
            tipo='calificaciones',
            formato=formato,
            valido_hasta__gt=timezone.now()
        ).first()
    except Exception as e:
        logger.warning(f"[-] Database error while reading cache: {e}")
        cache_activo = None

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
        periodo_activo = PeriodosGRPCClient.obtener_periodo_activo() or {}
        periodo_nombre = periodo_activo.get("nombre", "PRIMAVERA 2026")
        docente_nombre = "M.C. LUIS YAEL MÉNDEZ SÁNCHEZ"
        
        archivo_bytes = generate_calificaciones_excel(
            materia_id=materia_id,
            datos_calificaciones=datos_materia,
            periodo_nombre=periodo_nombre,
            docente_nombre=docente_nombre
        )
    else:
        archivo_bytes = generate_calificaciones_pdf(materia_id, alumnos_calif)

    fd, filepath = tempfile.mkstemp(suffix=f".{ext}", prefix=f"agm_calif_{materia_id}_")
    with os.fdopen(fd, 'wb') as f:
        f.write(archivo_bytes)

    try:
        ReporteCache.objects.create(
            materia_id=materia_id,
            tipo='calificaciones',
            formato=formato,
            archivo_path=filepath,
            valido_hasta=timezone.now() + timedelta(days=1), # Expira en exactamente 24 horas
        )
    except Exception as e:
        logger.warning(f"[-] Database error while writing cache: {e}")

    response = HttpResponse(archivo_bytes, content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="calificaciones_{materia_id}.{ext}"'
    return response


@api_view(['GET'])
@permission_classes([AllowAny])
def descargar_asistencias(request, materia_id):
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
            args=(materia_id, dest_email, formato, ext, 'asistencias')
        ).start()
        
        return Response({
            "success": True,
            "message": f"La generación del reporte de asistencias en formato {formato.upper()} ha comenzado en segundo plano. Recibirás un correo en {dest_email} con el archivo adjunto en cuanto esté listo."
        })

    try:
        cache_activo = ReporteCache.objects.filter(
            materia_id=materia_id,
            tipo='asistencia',
            formato=formato,
            valido_hasta__gt=timezone.now()
        ).first()
    except Exception as e:
        logger.warning(f"[-] Database error while reading cache: {e}")
        cache_activo = None

    if cache_activo and os.path.exists(cache_activo.archivo_path):
        with open(cache_activo.archivo_path, 'rb') as f:
            archivo_bytes = f.read()
        response = HttpResponse(archivo_bytes, content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="asistencias_{materia_id}_cached.{ext}"'
        return response

    datos_materia = CalificacionesGRPCClient.obtener_concentrado_materia(materia_id)
    if not datos_materia or not datos_materia.get('alumnos'):
        return Response({"error": "No hay calificaciones o alumnos registrados para obtener asistencias."}, status=404)

    # Obtener asistencias de todos los alumnos de la materia
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

    if ext == 'xlsx':
        archivo_bytes = generate_asistencias_excel(
            materia_id=materia_id,
            datos_calificaciones=datos_materia,
            datos_asistencias=datos_asistencias,
            periodo_nombre=periodo_nombre,
            docente_nombre=docente_nombre
        )
    else:
        datos_agregados = []
        for al in datos_materia['alumnos']:
            asist_sum = None
            for sa in datos_asistencias:
                if str(sa.get("alumno_id")) == str(al['alumno_id']):
                    asist_sum = sa
                    break
            datos_agregados.append({
                "matricula": al.get('matricula', 'N/A'),
                "nombre": al.get('alumno_nombre', 'Desconocido'),
                "presentes": asist_sum.get('total_presentes', 0) if asist_sum else 0,
                "retardos": asist_sum.get('total_retardos', 0) if asist_sum else 0,
                "faltas": asist_sum.get('total_ausentes', 0) if asist_sum else 0,
            })
        archivo_bytes = generate_asistencias_pdf(materia_id, datos_agregados)

    fd, filepath = tempfile.mkstemp(suffix=f".{ext}", prefix=f"agm_asist_{materia_id}_")
    with os.fdopen(fd, 'wb') as f:
        f.write(archivo_bytes)

    try:
        ReporteCache.objects.create(
            materia_id=materia_id,
            tipo='asistencia',
            formato=formato,
            archivo_path=filepath,
            valido_hasta=timezone.now() + timedelta(days=1),
        )
    except Exception as e:
        logger.warning(f"[-] Database error while writing cache: {e}")

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

    try:
        ReporteCache.objects.create(
            materia_id=materia_id,
            tipo='rendimiento',
            formato=formato,
            archivo_path=filepath,
            valido_hasta=timezone.now() + timedelta(days=1),
        )
    except Exception as e:
        logger.warning(f"[-] Database error while writing cache: {e}")

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
    periodo_activo = PeriodosGRPCClient.obtener_periodo_activo() or {}

    if promedio is None and asistencia is None:
        return Response({"error": "No se pudo obtener estadísticas del alumno para la materia indicada."}, status=404)

    # 1. Recuperar o autogenerar proactivamente el snapshot del grupo para comparaciones
    periodo_id = periodo_activo.get('id', 'N/A')
    snapshot = EstadisticasSnapshot.objects.filter(materia_id=materia_id, periodo_id=periodo_id).first()

    if not snapshot:
        try:
            datos_materia = CalificacionesGRPCClient.obtener_concentrado_materia(materia_id)
            if datos_materia and datos_materia.get('alumnos'):
                alumnos_base = datos_materia['alumnos']
                total_al = len(alumnos_base)
                prom_g = sum(a['promedio_real'] for a in alumnos_base) / total_al if total_al > 0 else 0.0
                aprob = sum(1 for a in alumnos_base if a['promedio_real'] >= 6.0)
                tasa_aprob = (aprob / total_al) * 100 if total_al > 0 else 0.0
                
                asist_global = AsistenciasGRPCClient.obtener_estadisticas_asistencia(materia_id)
                tasa_asist = asist_global.get('porcentaje_global', 0.0) if asist_global else 0.0
                
                snapshot = EstadisticasSnapshot.objects.create(
                    materia_id=materia_id,
                    periodo_id=periodo_id,
                    promedio_grupo=round(prom_g, 2),
                    tasa_aprobacion=round(tasa_aprob, 2),
                    tasa_asistencia=round(tasa_asist, 2),
                    total_alumnos=total_al,
                )
        except Exception:
            pass

    # 2. Computar KPIs Comparativos de Calificaciones
    prom_real = round(float(promedio.get('promedio_real', 0.0)), 2) if promedio and promedio.get('promedio_real') is not None else 0.0
    prom_red = promedio.get('promedio_redondeado', 0) if promedio and promedio.get('promedio_redondeado') is not None else 0
    promedio_grupo_val = float(snapshot.promedio_grupo) if snapshot else 0.0
    
    diff_prom = round(prom_real - promedio_grupo_val, 2)
    if diff_prom >= 0:
        msg_prom = f"Tu promedio se encuentra {diff_prom} puntos por encima de la media grupal."
    else:
        msg_prom = f"Tu promedio se encuentra {abs(diff_prom)} puntos por debajo de la media grupal."

    # 3. Computar KPIs Comparativos de Asistencias y Semáforo de Riesgo (Regla BUAP 80%)
    porcentaje_asist = round(float(asistencia.get('porcentaje', 0.0)), 2) if asistencia and asistencia.get('porcentaje') is not None else 0.0
    tasa_asistencia_grupo_val = float(snapshot.tasa_asistencia) if snapshot else 0.0
    
    diff_asist = round(porcentaje_asist - tasa_asistencia_grupo_val, 2)
    if diff_asist >= 0:
        msg_asist = f"Tu asistencia es un {diff_asist}% superior a la media de tu grupo."
    else:
        msg_asist = f"Tu asistencia es un {abs(diff_asist)}% inferior a la media de tu grupo."

    if porcentaje_asist >= 90.0:
        estado_riesgo = "EXCELENTE"
        msg_alerta = "Cumples satisfactoriamente con el porcentaje de asistencia requerido (mínimo 80%)."
    elif porcentaje_asist >= 80.0:
        estado_riesgo = "REGULAR"
        msg_alerta = "Cumples con el porcentaje mínimo requerido de asistencia, pero procura no faltar más."
    else:
        estado_riesgo = "RIESGO_POR_FALTAS"
        msg_alerta = "¡Alerta! Tu asistencia es menor al 80%. Estás en riesgo de perder derecho a examen final."

    # 4. Calcular el progreso del curso (actividades entregadas vs totales)
    actividades_totales = 0
    actividades_entregadas = 0
    porcentaje_completado = 0.0

    try:
        datos_concentrado = CalificacionesGRPCClient.obtener_concentrado_materia(materia_id)
        if datos_concentrado:
            for p in datos_concentrado.get("ponderaciones", []):
                actividades_totales += len(p.get("actividades", []))

            for al in datos_concentrado.get("alumnos", []):
                if str(al.get("alumno_id")) == str(id):
                    alumno_calificaciones = al.get("calificaciones", {})
                    for act_id, valor in alumno_calificaciones.items():
                        if valor is not None:
                            actividades_entregadas += 1
                    break

            if actividades_totales > 0:
                porcentaje_completado = round((actividades_entregadas / actividades_totales) * 100, 2)
    except Exception:
        pass

    # 5. Compilar el payload premium
    resumen_alumno = {
        "alumno_id": id,
        "materia_id": materia_id,
        "periodo_activo": periodo_activo.get('nombre', 'PRIMAVERA 2026'),
        
        "calificaciones_kpi": {
            "promedio_real": prom_real,
            "promedio_redondeado": prom_red,
            "comparativa_grupo": {
                "promedio_grupo": promedio_grupo_val,
                "diferencia": diff_prom,
                "mensaje": msg_prom
            }
        },
        
        "asistencia_kpi": {
            "porcentaje_asistencia": porcentaje_asist,
            "total_presentes": asistencia.get('total_presentes', 0) if asistencia else 0,
            "total_retardos": asistencia.get('total_retardos', 0) if asistencia else 0,
            "total_faltas": asistencia.get('total_ausentes', 0) if asistencia else 0,
            "comparativa_grupo": {
                "tasa_asistencia_grupo": tasa_asistencia_grupo_val,
                "diferencia": diff_asist,
                "mensaje": msg_asist
            },
            "estado_riesgo": estado_riesgo,
            "mensaje_alerta": msg_alerta
        },
        
        "progreso_academico": {
            "actividades_entregadas": actividades_entregadas,
            "actividades_totales": actividades_totales,
            "porcentaje_completado": porcentaje_completado
        }
    }

    return Response({
        "success": True,
        "message": f"Estadísticas analíticas del alumno {id} compiladas correctamente.",
        "data": resumen_alumno,
    })
