import os
import logging
import grpc
from django.conf import settings

logger = logging.getLogger(__name__)


def validar_token_en_auth(token):
    mock_mode = getattr(settings, 'GRPC_MOCK_MODE', True)
    if mock_mode:
        return {
            "valid": True,
            "user_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "email": "docente.mock@buap.mx",
            "role": "docente",
            "error": ""
        }

    from src.grpc.auth_pb2 import ValidateTokenRequest
    from src.grpc.auth_pb2_grpc import AuthServiceStub

    host = getattr(settings, 'AUTH_GRPC_HOST', os.getenv("AUTH_GRPC_HOST", "ms-auth"))
    port = getattr(settings, 'AUTH_GRPC_PORT', os.getenv("AUTH_GRPC_PORT", "50051"))
    target = f"{host}:{port}"
    
    try:
        with grpc.insecure_channel(target) as channel:
            stub = AuthServiceStub(channel)
            request = ValidateTokenRequest(access_token=token)
            
            response = stub.ValidateToken(request, timeout=3.0)
            
            return {
                "valid": response.valid,
                "user_id": response.user_id,
                "email": response.email,
                "role": response.role,
                "error": response.error
            }
    except grpc.RpcError as e:
        logger.error(f"Error gRPC al validar token en MS-1: {e.code()} - {e.details()}")
        return {"valid": False, "error": f"Error de comunicación con Auth: {e.details()}"}
    except Exception as e:
        logger.exception("Error inesperado validando token")
        return {"valid": False, "error": str(e)}
