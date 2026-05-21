import grpc
from django.conf import settings
from src.grpc import asistencias_pb2, asistencias_pb2_grpc

class AsistenciasGRPCClient:
    @staticmethod
    def obtener_estadisticas_asistencia(materia_id):
        target = f"{settings.ASISTENCIAS_GRPC_HOST}:{settings.ASISTENCIAS_GRPC_PORT}"
        with grpc.insecure_channel(target) as channel:
            stub = asistencias_pb2_grpc.AsistenciasServiceStub(channel)
            request = asistencias_pb2.GetEstadisticasAsistenciaRequest(materia_id=materia_id)
            try:
                response = stub.GetEstadisticasAsistencia(request, timeout=3)
                # Mapeamos las métricas acumuladas por alumno
                return {a.alumno_id: {
                    "presentes": a.presentes,
                    "retardos": a.retardos,
                    "faltas": a.faltas
                } for a in response.alumnos_stats}
            except grpc.RpcError:
                return None