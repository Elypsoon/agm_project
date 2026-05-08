from rest_framework import permissions

class IsAdminRole(permissions.BasePermission):
    """
    Restringe el acceso a usuarios autenticados con rol 'admin'.
    Usado en endpoints de administración del sistema.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')

class IsDocenteRole(permissions.BasePermission):
    """
    Restringe el acceso a usuarios autenticados con rol 'docente'.
    Usado en endpoints exclusivos del cuerpo académico.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'docente')

class IsAlumnoRole(permissions.BasePermission):
    """
    Restringe el acceso a usuarios autenticados con rol 'alumno'.
    Usado en endpoints del portal estudiantil.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'alumno')