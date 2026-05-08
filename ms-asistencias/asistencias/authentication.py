"""
Autenticación JWT para este microservicio.

En lugar de validar el JWT localmente (lo que requeriría compartir el SECRET_KEY
del MS-Auth), este MS llama al método gRPC ValidateToken del MS-1 Auth & Users.
Si el token es válido, el MS-Auth devuelve los claims del usuario (id, rol, etc.).

Esto respeta el principio de responsabilidad única: solo MS-Auth conoce los secretos.
"""

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from decouple import config
import jwt


class GrpcJWTAuthentication(BaseAuthentication):

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ', 1)[1].strip()
        if not token:
            return None

        try:
            user_claims = self._validate_token_local(token)
        except Exception as e:
            raise AuthenticationFailed(f"Token inválido: {str(e)}")

        user = AuthenticatedUser(
            user_id=user_claims.get('user_id'),
            rol=user_claims.get('rol'),
            email=user_claims.get('email', ''),
        )
        return (user, token)

    def _validate_token_local(self, token: str) -> dict:
        """
        Validación local temporal hasta que MS-Auth esté disponible.
        Cuando MS-Auth esté listo, esto se reemplaza por la llamada gRPC.
        """
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
    def __init__(self, user_id, rol, email):
        self.id = user_id
        self.user_id = user_id
        self.rol = rol
        self.email = email
        self.is_authenticated = True
        self.is_anonymous = False

    def __str__(self):
        return f"User({self.user_id}, {self.rol})"