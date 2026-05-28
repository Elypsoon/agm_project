import grpc
from django.conf import settings
from src.grpc import asistencias_pb2, asistencias_pb2_grpc

class AsistenciasGRPCClient:
    @staticmethod
    def get_target():
        host = settings.ASISTENCIAS_GRPC_HOST
        port = settings.ASISTENCIAS_GRPC_PORT
        return f"{host}:{port}"

    @staticmethod
    def obtener_estadisticas_asistencia(materia_id):
        target = AsistenciasGRPCClient.get_target()
        with grpc.insecure_channel(target) as channel:
            stub = asistencias_pb2_grpc.AsistenciasServiceStub(channel)
            request = asistencias_pb2.GetEstadisticasAsistenciaRequest(materia_id=str(materia_id))
            try:
                response = stub.GetEstadisticasAsistencia(request, timeout=3)
                return {
                    "materia_id": response.materia_id,
                    "total_sesiones": response.total_sesiones,
                    "total_registros": response.total_registros,
                    "total_presentes": response.total_presentes,
                    "total_retardos": response.total_retardos,
                    "porcentaje_global": response.porcentaje_global,
                }
            except grpc.RpcError:
                return None

    @staticmethod
    def obtener_asistencia_alumno(alumno_id, materia_id):
        target = AsistenciasGRPCClient.get_target()
        with grpc.insecure_channel(target) as channel:
            stub = asistencias_pb2_grpc.AsistenciasServiceStub(channel)
            request = asistencias_pb2.GetAsistenciaAlumnoRequest(
                alumno_id=str(alumno_id),
                materia_id=str(materia_id)
            )
            try:
                response = stub.GetAsistenciaAlumno(request, timeout=3)
                
                # Parsear el listado de asistencias individuales para la segunda pestaña
                historial_asistencias = []
                for a in response.asistencias:
                    historial_asistencias.append({
                        "fecha": a.fecha,     # Formato ISO (ej. 2026-05-26)
                        "estado": a.estado    # 'presente', 'retardo', 'ausente'
                    })
                
                return {
                    "alumno_id": response.alumno_id,
                    "materia_id": response.materia_id,
                    "total_clases": response.total_clases,
                    "total_presentes": response.total_presentes,
                    "total_retardos": response.total_retardos,
                    "total_ausentes": response.total_ausentes,
                    "porcentaje": response.porcentaje,
                    "asistencias": historial_asistencias
                }
            except grpc.RpcError:
                return None