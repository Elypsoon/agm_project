"""
Autenticación JWT para este microservicio.

En lugar de validar el JWT localmente (lo que requeriría compartir el SECRET_KEY
del MS-Auth), este MS llama al método gRPC ValidateToken del MS-1 Auth & Users.
Si el token es válido, el MS-Auth devuelve los claims del usuario (id, rol, etc.).

Esto respeta el principio de responsabilidad única: solo MS-Auth conoce los secretos.
"""

import grpc
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from decouple import config


class GrpcJWTAuthentication(BaseAuthentication):
    """
    Extrae el Bearer token del header Authorization,
    lo valida llamando a MS-Auth vía gRPC y retorna un objeto de usuario ficticio
    con los claims necesarios para los permission checks.
    """

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ', 1)[1].strip()
        if not token:
            return None

        try:
            user_claims = self._validate_token_via_grpc(token)
        except Exception as e:
            raise AuthenticationFailed(f"Token inválido: {str(e)}")

        user = AuthenticatedUser(
            user_id=user_claims.get('user_id'),
            rol=user_claims.get('rol'),
            email=user_claims.get('email', ''),
        )
        return (user, token)

    def _validate_token_via_grpc(self, token: str) -> dict:
        """
        Llama al método ValidateToken del MS-Auth via gRPC.
        Retorna los claims del usuario si el token es válido.
        """
        host = config('MS_AUTH_GRPC_HOST', default='localhost')
        port = config('MS_AUTH_GRPC_PORT', default='50051')

        try:
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'grpc'))

            from grpc_generated import auth_pb2, auth_pb2_grpc

            channel = grpc.insecure_channel(f'{host}:{port}')
            stub = auth_pb2_grpc.AuthServiceStub(channel)
            response = stub.ValidateToken(auth_pb2.ValidateTokenRequest(token=token))

            if not response.valid:
                raise AuthenticationFailed("Token rechazado por MS-Auth.")

            return {
                'user_id': response.user_id,
                'rol': response.rol,
                'email': response.email,
            }
        except grpc.RpcError as e:
            raise AuthenticationFailed(f"Error comunicándose con MS-Auth: {e.details()}")


class AuthenticatedUser:
    """Objeto de usuario mínimo compatible con DRF."""

    def __init__(self, user_id, rol, email):
        self.id = user_id
        self.user_id = user_id
        self.rol = rol
        self.email = email
        self.is_authenticated = True
        self.is_anonymous = False

    def __str__(self):
        return f"User({self.user_id}, {self.rol})"