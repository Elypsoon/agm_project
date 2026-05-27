import grpc
import os
from src.grpc import periodos_pb2, periodos_pb2_grpc

class PeriodosGRPCClient:
    
    @staticmethod
    def get_target():
        host = os.environ.get('PERIODOS_GRPC_HOST', 'ms-periodos')
        port = os.environ.get('PERIODOS_GRPC_PORT', '50052')
        return f"{host}:{port}"

    @staticmethod
    def obtener_materias_docente(docente_id):
        """Consulta al MS-2 todas las materias asignadas a un profesor."""
        with grpc.insecure_channel(PeriodosGRPCClient.get_target()) as channel:
            stub = periodos_pb2_grpc.PeriodosServiceStub(channel)
            request = periodos_pb2.DocenteIdRequest(docente_id=docente_id)
            try:
                response = stub.GetMateriasByDocente(request, timeout=3)
                return [
                    {
                        "materia_id": m.id,
                        "nrc": m.nrc,
                        "nombre": m.nombre,
                        "periodo_id": m.periodo_id,
                        "estado": m.estado,
                    } for m in response.materias
                ]
            except grpc.RpcError as e:
                print(f"[-] Error al contactar MS-2 (Periodos): {e.details()}")
                return None

    @staticmethod
    def obtener_periodo_activo():
        with grpc.insecure_channel(PeriodosGRPCClient.get_target()) as channel:
            stub = periodos_pb2_grpc.PeriodosServiceStub(channel)
            request = periodos_pb2.Empty()
            try:
                response = stub.GetPeriodoActivo(request, timeout=3)
                return {
                    "id": response.id,
                    "nombre": response.nombre,
                    "fecha_inicio": response.fecha_inicio,
                    "fecha_fin": response.fecha_fin,
                    "estado": response.estado,
                }
            except grpc.RpcError as e:
                print(f"[-] Error al solicitar periodo activo a MS-2: {e.details()}")
                return None

    @staticmethod
    def obtener_materia_por_id(materia_id):
        with grpc.insecure_channel(PeriodosGRPCClient.get_target()) as channel:
            stub = periodos_pb2_grpc.PeriodosServiceStub(channel)
            request = periodos_pb2.MateriaIdRequest(materia_id=materia_id)
            try:
                response = stub.GetMateriaById(request, timeout=3)
                return {
                    "id": response.id,
                    "nrc": response.nrc,
                    "nombre": response.nombre,
                    "clave": response.clave,
                    "seccion": response.seccion,
                    "docente_id": response.docente_id,
                    "docente_nombre": response.docente_nombre,
                    "periodo_id": response.periodo_id,
                    "estado": response.estado,
                }
            except grpc.RpcError as e:
                print(f"[-] Error al obtener materia por ID: {e.details()}")
                return None