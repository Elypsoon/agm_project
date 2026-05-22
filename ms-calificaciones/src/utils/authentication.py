from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from src.grpc.auth_client import validar_token_en_auth


class UsuarioAutenticado:
    def __init__(self, data):
        self.user_id = data['user_id']
        self.email = data['email']
        self.role = data['role']
        self.is_authenticated = True

    def __str__(self):
        return self.email


class GrpcJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header:
            return None

        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header[7:]

        result = validar_token_en_auth(token)

        if not result.get('valid'):
            raise AuthenticationFailed(result.get('error', 'Token inválido o expirado.'))

        return (UsuarioAutenticado(result), token)

    def authenticate_header(self, request):
        return 'Bearer'
