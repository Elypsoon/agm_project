import grpc
import os
import requests
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
        """Obtiene materia por ID. Intenta gRPC primero; si falla, usa REST como fallback."""
        # --- Intento gRPC ---
        try:
            with grpc.insecure_channel(PeriodosGRPCClient.get_target()) as channel:
                stub = periodos_pb2_grpc.PeriodosServiceStub(channel)
                request = periodos_pb2.MateriaIdRequest(materia_id=materia_id)
                response = stub.GetMateriaById(request, timeout=3)
                # Si la respuesta tiene id vacío significa que gRPC respondió con error silencioso
                if response.id:
                    return {
                        "id": response.id,
                        "nrc": response.nrc,
                        "nombre": response.nombre,
                        "clave": response.clave,
                        "seccion": response.seccion,
                        "docente_id": getattr(response, "docente_id", ""),
                        "docente_nombre": getattr(response, "docente_nombre", ""),
                        "periodo_id": response.periodo_id,
                        "estado": response.estado,
                    }
        except grpc.RpcError as e:
            print(f"[-] gRPC falló para materia {materia_id}: {e.details()} — usando REST como fallback")
        except Exception as e:
            print(f"[-] Error inesperado en gRPC de periodos: {e} — usando REST como fallback")

        # --- Fallback REST ---
        return PeriodosGRPCClient.obtener_materia_por_id_rest(materia_id)

    @staticmethod
    def obtener_materia_por_id_rest(materia_id):
        """Consulta la materia vía REST API de MS-2 (fallback cuando gRPC no está disponible)."""
        host = os.environ.get('PERIODOS_REST_HOST', 'ms-periodos')
        port = os.environ.get('PERIODOS_REST_PORT', '3002')
        url = f"http://{host}:{port}/api/materias/{materia_id}/"
        try:
            resp = requests.get(url, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "id": str(data.get("id", "")),
                    "nrc": data.get("nrc", ""),
                    "nombre": data.get("nombre", ""),
                    "clave": data.get("clave", ""),
                    "seccion": data.get("seccion", ""),
                    "docente_id": str(data.get("docente_id") or ""),
                    "docente_nombre": data.get("docente_nombre", ""),
                    "periodo_id": str(data.get("periodo", "")),
                    "estado": data.get("estado", ""),
                }
            else:
                print(f"[-] REST de periodos respondió {resp.status_code} para materia {materia_id}")
                return None
        except Exception as e:
            print(f"[-] Error al contactar REST de MS-2 (materia): {e}")
            return None