from rest_framework import permissions

# JWTAuthentication (configurado en settings.py) se encarga de decodificar el token
# y poblar request.user antes de que el request llegue a cualquier vista.
# Este permiso actúa como una segunda capa de verificación explícita.
class IsAuthenticatedMiddleware(permissions.BasePermission):
    """
    Verifica que request.user exista y esté autenticado.
    Equivale al guard de sesión en frameworks como FastAPI o Express.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)