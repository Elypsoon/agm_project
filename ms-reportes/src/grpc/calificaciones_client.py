import grpc
import os
from src.grpc import calificaciones_pb2, calificaciones_pb2_grpc

class CalificacionesGRPCClient:
    
    @staticmethod
    def get_target():
        host = os.environ.get('CALIFICACIONES_GRPC_HOST', 'ms-calificaciones')
        port = os.environ.get('CALIFICACIONES_GRPC_PORT', '50054')
        return f"{host}:{port}"

    @staticmethod
    def obtener_concentrado_materia(materia_id):
        """Obtiene la lista completa de alumnos con sus promedios para exportar."""
        with grpc.insecure_channel(CalificacionesGRPCClient.get_target()) as channel:
            stub = calificaciones_pb2_grpc.CalificacionesServiceStub(channel)
            request = calificaciones_pb2.MateriaIdRequest(materia_id=materia_id)
            try:
                response = stub.GetConcentrado(request, timeout=5)
                # Formateamos la respuesta a un diccionario de Python limpio
                return {
                    "materia_id": response.materia_id,
                    "materia_nombre": response.materia_nombre,
                    "alumnos": [
                        {
                            "alumno_id": a.alumno_id,
                            "alumno_nombre": a.alumno_nombre,
                            "promedio_real": a.promedio_real,
                            "promedio_redondeado": a.promedio_redondeado
                        } for a in response.alumnos
                    ]
                }
            except grpc.RpcError as e:
                print(f"[-] Error al contactar MS-4 (Concentrado): {e.details()}")
                return None

    @staticmethod
    def obtener_estadisticas_globales(materia_id):
        """Obtiene los KPIs de la materia (Promedio grupal, max, min)."""
        with grpc.insecure_channel(CalificacionesGRPCClient.get_target()) as channel:
            stub = calificaciones_pb2_grpc.CalificacionesServiceStub(channel)
            request = calificaciones_pb2.MateriaIdRequest(materia_id=materia_id)
            try:
                response = stub.GetEstadisticasMateria(request, timeout=3)
                return {
                    "promedio_grupo": response.promedio_grupo,
                    "calificacion_max": response.calificacion_max,
                    "calificacion_min": response.calificacion_min,
                    "total_alumnos": response.total_alumnos
                }
            except grpc.RpcError as e:
                print(f"[-] Error al contactar MS-4 (Estadísticas): {e.details()}")
                return None