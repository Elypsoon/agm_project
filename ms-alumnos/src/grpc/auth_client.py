"""
Cliente REST — Comunicacion con MS-1 Auth.

MS-1 (Django) aun no implementa gRPC. Usamos su API REST para registrar
usuarios al importar docentes/alumnos. Cuando MS-1 implemente gRPC,
solo hay que cambiar esta capa sin tocar los servicios.
"""

import logging

import httpx

from src.config.settings import settings

logger = logging.getLogger(__name__)

_AUTH_BASE = f"http://{settings.AUTH_GRPC_HOST}:3001"


async def registrar_usuario_en_auth(
    email: str,
    nombre: str,
    password: str,
    role: str = "alumno",
) -> str | None:
    """
    Registra un usuario en MS-1 Auth via REST.

    Returns:
        El user_id (UUID str) del usuario creado, o None si fallo o ya existia.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{_AUTH_BASE}/auth/register/",
                json={"email": email, "nombre": nombre, "password": password, "role": role},
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
