import os
import grpc
import logging
from src.grpc import alumnos_pb2, alumnos_pb2_grpc

logger = logging.getLogger(__name__)

ALUMNOS_GRPC_HOST = os.getenv("ALUMNOS_GRPC_HOST", "ms-alumnos")
ALUMNOS_GRPC_PORT = os.getenv("ALUMNOS_GRPC_PORT", "50053")
ALUMNOS_GRPC_SERVER = f"{ALUMNOS_GRPC_HOST}:{ALUMNOS_GRPC_PORT}"

def consultar_id_docente_grpc(nombre_limpio: str) -> str | None:
    """
    Calls the teacher microservice over gRPC to fetch a teacher's ID by name.
    """
    if not nombre_limpio or nombre_limpio == "POR ASIGNAR":
        return None

    try:
        with grpc.insecure_channel(ALUMNOS_GRPC_SERVER) as channel:
            stub = alumnos_pb2_grpc.AlumnosServiceStub(channel)
            
            request = alumnos_pb2.GetDocenteByNameRequest(nombre_completo=nombre_limpio)
            
            response = stub.GetDocenteByName(request, timeout=3.0)
            
            
            if response and response.id:
                return response.id, response.nombre_completo
                
        return None
                
    except grpc.RpcError as e:
        logger.warning(f"gRPC matching lookup skipped or failed: {e.code()}")
        return None