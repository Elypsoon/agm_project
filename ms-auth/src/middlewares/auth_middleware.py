from rest_framework import permissions

# En Django, esto se reemplaza por el uso de 'IsAuthenticated' 
# en los controladores. El "guardián" es el JWTAuthentication 
# que configuramos en el settings.py.

class IsAuthenticatedMiddleware(permissions.BasePermission):
    """
    Este es el equivalente al 'get_current_user'.
    Django ya decodificó el token y puso al usuario en request.user
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)