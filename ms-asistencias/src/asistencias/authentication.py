"""
Autenticación JWT para este microservicio.

Flujo principal: validar token via gRPC con MS-Auth.
Fallback si MS-Auth cae:
  1. Decodificar JWT localmente con simplejwt
  2. Buscar role en Redis (caché local)
  3. Si no hay caché, intentar gRPC con timeout corto
"""

import os
import sys
import importlib.util
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from decouple import config
from django.core.cache import cache


def _load_grpc():
    spec = importlib.util.spec_from_file_location(
        "grpc",
        "/usr/local/lib/python3.11/site-packages/grpc/__init__.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules['grpc'] = mod
    spec.loader.exec_module(mod)
    return mod


def _role_cache_key(user_id: str) -> str:
    return f"user_role:{user_id}"


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
                auth_pb2.ValidateTokenRequest(access_token=token),
                timeout=2
            )

            if not response.valid:
                raise AuthenticationFailed(f"Token rechazado: {response.error}")

            # Guardar role en Redis como memoria de emergencia
            if response.user_id and response.role:
                try:
                    cache.set(
                        _role_cache_key(response.user_id),
                        {'role': response.role, 'email': response.email},
                        timeout=3600  # 1 hora
                    )
                except Exception:
                    pass  # Redis no crítico aquí

            return {
                'user_id': response.user_id,
                'rol': response.role,
                'email': response.email,
                'matricula': '',
            }

        except AuthenticationFailed:
            raise
        except Exception:
            return self._validate_token_local(token)

    def _validate_token_local(self, token: str) -> dict:
        """
        Fallback cuando MS-Auth no está disponible.
        1. Decodifica JWT localmente
        2. Busca role en Redis local
        3. Si no hay caché, intenta gRPC con timeout corto
        """
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            decoded = AccessToken(token)
            user_id = str(decoded['user_id'])
            role = decoded.get('role', '')
            email = decoded.get('email', '')

            # Si el token no trae role, buscar en Redis primero
            if not role:
                try:
                    cached = cache.get(_role_cache_key(user_id))
                    if cached:
                        role = cached.get('role', '')
                        email = cached.get('email', email)
                except Exception:
                    pass

            # Si tampoco está en Redis, fallamos rápido. Ya sabemos que MS-Auth está caído.            if not role:
            if not role:
                raise AuthenticationFailed("Servicio de autenticación no disponible y sin caché local. Intente más tarde.")

            return {
                'user_id': user_id,
                'rol': role,
                'email': email,
                'matricula': decoded.get('matricula', ''),
            }
        except Exception as e:
            raise AuthenticationFailed(f"Token inválido: {str(e)}")

    def _get_user_info_via_grpc(self, user_id: str, token: str):
        host = config('MS_AUTH_GRPC_HOST', default='localhost')
        port = config('MS_AUTH_GRPC_PORT', default='50051')

        grpc = _load_grpc()

        def load_module(name, path):
            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            return mod

        auth_pb2 = load_module('auth_pb2', '/app/src/grpc/grpc_generated/auth_pb2.py')
        auth_pb2_grpc = load_module('auth_pb2_grpc', '/app/src/grpc/grpc_generated/auth_pb2_grpc.py')

        channel = grpc.insecure_channel(f'{host}:{port}')
        stub = auth_pb2_grpc.AuthServiceStub(channel)
        response = stub.ValidateToken(
            auth_pb2.ValidateTokenRequest(access_token=token),
            timeout=2
        )

        if response.valid:
            return response.role, response.email

        raise Exception("Token rechazado por MS-Auth")


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