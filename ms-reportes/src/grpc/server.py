import os
import grpc
import django
from concurrent import futures
from django.conf import settings
from src.grpc import reportes_pb2, reportes_pb2_grpc
from src.grpc.calificaciones_client import CalificacionesGRPCClient
from src.grpc.asistencias_client import AsistenciasGRPCClient
from src.grpc.alumnos_client import AlumnosGRPCClient
from src.grpc.periodos_client import PeriodosGRPCClient
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
from src.models.reportes import EstadisticasSnapshot

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.core.settings')
django.setup()


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _enriquecer_calificaciones_con_asistencia(alumnos, materia_id):
    enriched = []
    for alumno in alumnos:
        asistencia = AsistenciasGRPCClient.obtener_asistencia_alumno(
            alumno_id=alumno.get('alumno_id'),
            materia_id=materia_id,
        )
        enriched.append({
            **alumno,
            'asistencia': asistencia.get('porcentaje', 0.0) if asistencia else 0.0,
            'presentes': asistencia.get('total_presentes', 0) if asistencia else 0,
            'retardos': asistencia.get('total_retardos', 0) if asistencia else 0,
            'faltas': asistencia.get('total_ausentes', 0) if asistencia else 0,
            'calificacion': round(alumno.get('promedio_real', 0.0), 2),
        })
    return enriched


def _build_calificaciones_report_bytes(materia_id, ext):
    datos_materia = CalificacionesGRPCClient.obtener_concentrado_materia(materia_id)
    if not datos_materia or not datos_materia.get('alumnos'):
        return None

    alumnos = _enriquecer_calificaciones_con_asistencia(datos_materia['alumnos'], materia_id)
    if ext == 'xlsx':
        return generate_calificaciones_excel(materia_id, alumnos)
    return generate_calificaciones_pdf(materia_id, alumnos)


def _build_asistencias_report_bytes(materia_id, ext):
    alumnos = AlumnosGRPCClient.obtener_alumnos_materia(materia_id)
    if alumnos is None:
        return None

    datos_agregados = []
    for alumno in alumnos:
        asistencia = AsistenciasGRPCClient.obtener_asistencia_alumno(
            alumno_id=alumno['id'],
            materia_id=materia_id,
        )
        datos_agregados.append({
            'matricula': alumno.get('matricula', 'N/A'),
            'nombre': alumno.get('nombre', 'Desconocido'),
            'presentes': asistencia.get('total_presentes', 0) if asistencia else 0,
            'retardos': asistencia.get('total_retardos', 0) if asistencia else 0,
            'faltas': asistencia.get('total_ausentes', 0) if asistencia else 0,
        })

    if ext == 'xlsx':
        return generate_asistencias_excel(materia_id, datos_agregados)
    return generate_asistencias_pdf(materia_id, datos_agregados)


def _build_rendimiento_report_bytes(materia_id, ext):
    datos_materia = CalificacionesGRPCClient.obtener_concentrado_materia(materia_id)
    asistencia_global = AsistenciasGRPCClient.obtener_estadisticas_asistencia(materia_id)
    estadisticas_materia = CalificacionesGRPCClient.obtener_estadisticas_globales(materia_id)

    if not datos_materia or not datos_materia.get('alumnos') or asistencia_global is None or estadisticas_materia is None:
        return None

    alumnos = _enriquecer_calificaciones_con_asistencia(datos_materia['alumnos'], materia_id)
    periodo_activo = PeriodosGRPCClient.obtener_periodo_activo() or {}

    resumen = {
        'materia_id': materia_id,
        'materia_nombre': datos_materia.get('materia_nombre', 'Desconocida'),
        'periodo_id': periodo_activo.get('id', 'N/A'),
        'promedio_grupo': estadisticas_materia.get('promedio_grupo', 0.0),
        'calificacion_maxima': estadisticas_materia.get('calificacion_max', 0.0),
        'calificacion_minima': estadisticas_materia.get('calificacion_min', 0.0),
        'tasa_asistencia': asistencia_global.get('porcentaje_global', 0.0),
        'total_alumnos': estadisticas_materia.get('total_alumnos', len(alumnos)),
    }

    if ext == 'xlsx':
        return generate_rendimiento_excel(materia_id, resumen, alumnos)
    return generate_rendimiento_pdf(materia_id, resumen, alumnos)


class ReportesServiceServicer(reportes_pb2_grpc.ReportesServiceServicer):

    def GetHistorialDocente(self, request, context):
        materias = PeriodosGRPCClient.obtener_materias_docente(request.docente_id) or []
        materia_ids = [m['materia_id'] for m in materias]
        snapshots = EstadisticasSnapshot.objects.filter(materia_id__in=materia_ids)

        response = reportes_pb2.HistorialDocenteResponse()
        for snap in snapshots:
            response.historial.append(reportes_pb2.StatsPeriodo(
                periodo_id=snap.periodo_id,
                materia_id=snap.materia_id,
                promedio_grupo=float(snap.promedio_grupo),
                tasa_asistencia=float(snap.tasa_asistencia),
                tasa_aprobacion=float(snap.tasa_aprobacion),
                total_alumnos=snap.total_alumnos,
            ))
        return response

    def GenerateReport(self, request, context):
        tipo = request.tipo_reporte.lower()
        formato = request.formato.lower()
        ext = 'xlsx' if formato in ['xls', 'xlsx'] else 'pdf'

        if tipo == 'calificaciones':
            archivo_bytes = _build_calificaciones_report_bytes(request.materia_id, ext)
        elif tipo == 'asistencias':
            archivo_bytes = _build_asistencias_report_bytes(request.materia_id, ext)
        elif tipo == 'rendimiento':
            archivo_bytes = _build_rendimiento_report_bytes(request.materia_id, ext)
        else:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details('Tipo de reporte no soportado')
            return reportes_pb2.GenerateReportResponse()

        if archivo_bytes is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('No se pudo generar el reporte solicitado')
            return reportes_pb2.GenerateReportResponse()

        return reportes_pb2.GenerateReportResponse(file_bytes=archivo_bytes)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    reportes_pb2_grpc.add_ReportesServiceServicer_to_server(ReportesServiceServicer(), server)
    port = os.environ.get('GRPC_PORT', '50057')
    server.add_insecure_port(f'[::]:{port}')
    print(f"[+] Servidor gRPC de Reportes escuchando en el puerto {port}...")
    server.start()
    server.wait_for_termination()