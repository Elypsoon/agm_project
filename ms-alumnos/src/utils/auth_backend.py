"""
Backend de autenticación DRF — Validacion de tokens via gRPC con MS-1 Auth
"""
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from dataclasses import dataclass
from django.conf import settings

from src.grpc.auth_client import validar_token_en_auth


@dataclass
class RemoteUser:
    """Representación mínima de un usuario autenticado remotamente en MS-1."""
    id: str
    email: str
    role: str

    @property
    def is_authenticated(self):
        return True


class GrpcAuthentication(BaseAuthentication):
    """
    Autentica peticiones interceptando el header HTTP 'Authorization: Bearer <token>'.
    Valida el token contra MS-1 usando gRPC.
    """
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) == 0 or parts[0].lower() != self.keyword.lower():
            return None

        if len(parts) == 1:
            raise AuthenticationFailed("Token de autorización inválido: Faltan credenciales")
        elif len(parts) > 2:
            raise AuthenticationFailed("Token de autorización inválido: Contiene espacios")

        token = parts[1]
        
        # Validar via gRPC
        result = validar_token_en_auth(token)
        
        if not result.get("valid"):
            error_msg = result.get("error", "Token inválido o expirado")
            raise AuthenticationFailed(f"Autenticación fallida: {error_msg}")

        # Retornar (user, auth)
        user = RemoteUser(
            id=result["user_id"],
            email=result["email"],
            role=result["role"],
        )
        return (user, token)

    def authenticate_header(self, request):
        return self.keyword
