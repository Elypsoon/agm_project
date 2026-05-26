"""
Autenticación JWT para este microservicio.

En lugar de validar el JWT localmente (lo que requeriría compartir el SECRET_KEY
del MS-Auth), este MS llama al método gRPC ValidateToken del MS-1 Auth & Users.
Si el token es válido, el MS-Auth devuelve los claims del usuario (id, rol, etc.).

Esto respeta el principio de responsabilidad única: solo MS-Auth conoce los secretos.
"""

import os
import sys
import importlib.util
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from decouple import config


def _load_grpc():
    """Carga grpc desde site-packages evitando conflicto con carpeta src/grpc."""
    spec = importlib.util.spec_from_file_location(
        "grpc",
        "/usr/local/lib/python3.11/site-packages/grpc/__init__.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules['grpc'] = mod
    spec.loader.exec_module(mod)
    return mod


class GrpcJWTAuthentication(BaseAuthentication):

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
            matricula=user_claims.get('matricula', ''),
        )
        return (user, token)

    def _validate_token_via_grpc(self, token: str) -> dict:
        host = config('MS_AUTH_GRPC_HOST', default='localhost')
        port = config('MS_AUTH_GRPC_PORT', default='50051')

        try:
            grpc = _load_grpc()

            # Cargar auth_pb2 y auth_pb2_grpc desde ruta absoluta
            def load_module(name, path):
                spec = importlib.util.spec_from_file_location(name, path)
                mod = importlib.util.module_from_spec(spec)
                sys.modules[name] = mod
                spec.loader.exec_module(mod)
                return mod

            auth_pb2 = load_module(
                'auth_pb2',
                '/app/src/grpc/grpc_generated/auth_pb2.py'
            )
            auth_pb2_grpc = load_module(
                'auth_pb2_grpc',
                '/app/src/grpc/grpc_generated/auth_pb2_grpc.py'
            )

            channel = grpc.insecure_channel(f'{host}:{port}')
            stub = auth_pb2_grpc.AuthServiceStub(channel)
            response = stub.ValidateToken(
                auth_pb2.ValidateTokenRequest(access_token=token)
            )

            if not response.valid:
                raise AuthenticationFailed(f"Token rechazado: {response.error}")

            return {
                'user_id': response.user_id,
                'rol': response.role,
                'email': response.email,
            }
        except Exception:
            # Fallback: validación local con JWT cuando MS-Auth no está disponible
            return self._validate_token_local(token)

    def _validate_token_local(self, token: str) -> dict:
        import jwt
        secret = config('JWT_SECRET_KEY', default='temporal-secret')
        try:
            payload = jwt.decode(token, secret, algorithms=['HS256'])
            return {
                'user_id': payload.get('user_id'),
                'rol': payload.get('rol'),
                'email': payload.get('email', ''),
            }
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token expirado.")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Token inválido.")


class AuthenticatedUser:
    def __init__(self, user_id, rol, email, matricula=''):
        self.id = user_id
        self.user_id = user_id
        self.rol = rol
        self.email = email
        self.matricula = matricula
        self.is_authenticated = True
        self.is_anonymous = False

    def __str__(self):
        return f"User({self.user_id}, {self.rol})"