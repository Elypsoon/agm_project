import grpc
from django.conf import settings
from src.grpc import alumnos_pb2, alumnos_pb2_grpc

class AlumnosGRPCClient:
    @staticmethod
    def obtener_alumnos_materia(materia_id):
        target = f"{settings.ALUMNOS_GRPC_HOST}:{settings.ALUMNOS_GRPC_PORT}"
        with grpc.insecure_channel(target) as channel:
            stub = alumnos_pb2_grpc.AlumnosServiceStub(channel)
            request = alumnos_pb2.GetAlumnosByMateriaRequest(materia_id=materia_id)
            try:
                response = stub.GetAlumnosByMateria(request, timeout=3)
                return [{
                    "id": a.id,
                    "matricula": a.matricula,
                    "nombre": a.nombre_completo
                } for a in response.alumnos]
            except grpc.RpcError as e:
                print(f"[-] Fallo crítico gRPC con MS-3: {e.details()}")
                return None