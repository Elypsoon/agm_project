"""
Cliente REST — Comunicacion con MS-1 Auth (sincrónico).

Dado que el MS-1aun no implementa gRPC. Usamos su API REST para registrar
usuarios al importar docentes/alumnos. Cuando MS-1 implemente gRPC,
solo hay que cambiar esta capa sin tocar los servicios.
"""

import os
import logging
import httpx

logger = logging.getLogger(__name__)


def _get_auth_base():
    """Obtener la URL base de MS-1 Auth (lazy para evitar import prematuro)."""
    try:
        from django.conf import settings
        host = settings.AUTH_GRPC_HOST
    except Exception:
        host = os.getenv("AUTH_GRPC_HOST", "ms-auth")
    return f"http://{host}:3001"


def registrar_usuario_en_auth(
    email: str,
    nombre: str,
    password: str,
    role: str = "alumno",
) -> str | None:
    """
    Registra un usuario en MS-1 Auth via REST (sincrono).

    Returns:
        El user_id (UUID str) del usuario creado, o None si fallo o ya existia.
    """
    try:
        auth_base = _get_auth_base()
        response = httpx.post(
            f"{auth_base}/auth/register/",
            json={"email": email, "nombre": nombre, "password": password, "role": role},
            timeout=10.0,
        )

        if response.status_code in (200, 201):
            data = response.json()
            user_id = data.get("id") or data.get("user", {}).get("id")
            logger.info(f"Usuario registrado en Auth: {email} -> {user_id}")
            return user_id

        if response.status_code == 400:
            logger.info(f"Usuario ya existe en Auth: {email}")
            return None

        logger.warning(f"Auth respondio {response.status_code} para {email}: {response.text}")
        return None

    except httpx.ConnectError:
        logger.warning("MS-1 Auth no disponible — se omite el registro del usuario")
        return None
    except Exception as e:
        logger.error(f"Error al comunicarse con MS-1 Auth: {e}")
        return None


def validar_token_en_auth(token: str) -> dict:
    """
    Valida un JWT token contra el MS-1 (Auth) usando gRPC.
    
    Args:
        token: El token JWT (sin el prefijo Bearer).
        
    Returns:
        Diccionario con { 'valid': bool, 'user_id': str, 'email': str, 'role': str }
        Si hay un error o es inválido, retorna {'valid': False, 'error': ...}
    """
    import grpc
    from src.grpc.auth_pb2 import ValidateTokenRequest
    from src.grpc.auth_pb2_grpc import AuthServiceStub

    try:
        from django.conf import settings
        host = settings.AUTH_GRPC_HOST
    except Exception:
        host = os.getenv("AUTH_GRPC_HOST", "ms-auth")

    target = f"{host}:50051"
    
    try:
        with grpc.insecure_channel(target) as channel:
            stub = AuthServiceStub(channel)
            request = ValidateTokenRequest(access_token=token)
            
            # Timeout corto para no bloquear la petición REST si MS-1 está caído
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
        return {"valid": False, "error": "Error de comunicación con Auth"}
    except Exception as e:
        logger.exception("Error inesperado validando token")
        return {"valid": False, "error": str(e)}
