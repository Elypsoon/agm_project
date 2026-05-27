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
                
                # Parsear las ponderaciones del gRPC
                ponderaciones = []
                for p in response.categorias:
                    actividades = []
                    for act in p.actividades:
                        actividades.append({
                            "id": act.actividad_id,
                            "nombre": act.actividad_nombre
                        })
                    ponderaciones.append({
                        "id": "",
                        "nombre_categoria": p.nombre_categoria,
                        "porcentaje": p.porcentaje,
                        "actividades": actividades
                    })

                # Parsear los alumnos con su matrícula y notas desglosadas por actividad
                alumnos = []
                for a in response.alumnos:
                    calificaciones_map = {}
                    for c in a.calificaciones:
                        calificaciones_map[c.actividad_id] = c.valor
                    
                    alumnos.append({
                        "alumno_id": a.alumno_id,
                        "alumno_nombre": a.alumno_nombre,
                        "matricula": a.alumno_matricula or "N/A",
                        "promedio_real": a.promedio_real,
                        "promedio_redondeado": a.promedio_redondeado,
                        "calificaciones": calificaciones_map
                    })

                return {
                    "materia_id": response.materia_id,
                    "materia_nombre": response.materia_nombre,
                    "alumnos": alumnos,
                    "ponderaciones": ponderaciones
                }
            except grpc.RpcError as e:
                print(f"[-] Error al contactar MS-4 (Concentrado): {e.details()}")
                return None

    @staticmethod
    def obtener_promedio_alumno(alumno_id, materia_id):
        with grpc.insecure_channel(CalificacionesGRPCClient.get_target()) as channel:
            stub = calificaciones_pb2_grpc.CalificacionesServiceStub(channel)
            request = calificaciones_pb2.AlumnoMateriaRequest(
                alumno_id=alumno_id,
                materia_id=materia_id
            )
            try:
                response = stub.GetPromedioAlumno(request, timeout=3)
                return {
                    "promedio_real": response.promedio_real,
                    "promedio_redondeado": response.promedio_redondeado
                }
            except grpc.RpcError as e:
                print(f"[-] Error al contactar MS-4 (Promedio Alumno): {e.details()}")
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