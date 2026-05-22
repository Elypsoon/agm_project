import grpc
from django.conf import settings
from src.grpc import alumnos_pb2, alumnos_pb2_grpc

class AlumnosGRPCClient:
    @staticmethod
    def obtener_datos_alumno(alumno_id):
        target = f"{settings.ALUMNOS_GRPC_HOST}:{settings.ALUMNOS_GRPC_PORT}"
        with grpc.insecure_channel(target) as channel:
            stub = alumnos_pb2_grpc.AlumnosServiceStub(channel)
            request = alumnos_pb2.GetAlumnoByIdRequest(alumno_id=alumno_id)
            try:
                response = stub.GetAlumnoById(request, timeout=2)
                return {
                    "email": response.correo, # <- Ajustado al Proto
                    "nombre": response.nombre_completo
                }
            except grpc.RpcError:
                return None
    
    @staticmethod
    def obtener_datos_docente(docente_id):
        """Nuevo método: Consulta el perfil del docente en el MS-3"""
        target = f"{settings.ALUMNOS_GRPC_HOST}:{settings.ALUMNOS_GRPC_PORT}"
        with grpc.insecure_channel(target) as channel:
            stub = alumnos_pb2_grpc.AlumnosServiceStub(channel)
            request = alumnos_pb2.GetDocenteByIdRequest(docente_id=docente_id)
            try:
                response = stub.GetDocenteById(request, timeout=2)
                return {"email": response.correo_institucional, "nombre": response.nombre_completo}
            except grpc.RpcError:
                return None

    @staticmethod
    def obtener_lista_grupo(materia_id):
        target = f"{settings.ALUMNOS_GRPC_HOST}:{settings.ALUMNOS_GRPC_PORT}"
        with grpc.insecure_channel(target) as channel:
            stub = alumnos_pb2_grpc.AlumnosServiceStub(channel)
            request = alumnos_pb2.GetAlumnosByMateriaRequest(materia_id=materia_id)
            try:
                response = stub.GetAlumnosByMateria(request, timeout=3)
                # <- Ajustado al Proto (a.correo)
                return [{"email": a.correo, "nombre": a.nombre_completo} for a in response.alumnos]
            except grpc.RpcError:
                return None