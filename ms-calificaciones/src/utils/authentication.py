from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from src.grpc.auth_client import validar_token_en_auth


class UsuarioAutenticado:
    """Clase contenedora que representa a un usuario autenticado de forma remota.

    Atributos:
        user_id (str): Identificador único del usuario (UUID).
        email (str): Correo electrónico del usuario.
        role (str): Rol o perfil asignado (e.g. 'docente', 'alumno').
        is_authenticated (bool): Bandera indicando que el usuario está autenticado.
    """

    def __init__(self, data):
        self.user_id = data['user_id']
        self.email = data['email']
        self.role = data['role']
        self.is_authenticated = True

    def __str__(self):
        return self.email


class GrpcJWTAuthentication(BaseAuthentication):
    """Clase de autenticación para Django REST Framework que valida tokens JWT mediante gRPC.

    Extrae el token Bearer del encabezado 'Authorization' y delega la verificación
    de firma y vigencia al microservicio de autenticación (MS-1) a través de gRPC.
    """

    def authenticate(self, request):
        """Valida el token provisto en las cabeceras HTTP de la solicitud.

        Args:
            request: Solicitud HTTP de Django.

        Returns:
            tuple[UsuarioAutenticado, str] | None: Una tupla con el objeto de usuario y
                el token si la validación es correcta, o None si no se provee cabecera de autenticación.
        """
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
        """Retorna el esquema de autenticación esperado."""
        return 'Bearer'