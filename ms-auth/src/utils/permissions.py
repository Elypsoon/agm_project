from rest_framework import permissions

class IsAdminRole(permissions.BasePermission):
    """Permite el acceso solo a usuarios con rol 'admin'."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')

class IsDocenteRole(permissions.BasePermission):
    """Permite el acceso solo a usuarios con rol 'docente'."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'docente')

class IsAlumnoRole(permissions.BasePermission):
    """Permite el acceso solo a usuarios con rol 'alumno'."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'alumno')