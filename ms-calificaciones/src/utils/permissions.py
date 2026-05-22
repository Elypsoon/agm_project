from rest_framework.permissions import BasePermission


class IsDocente(BasePermission):
    """Permiso exclusivo para usuarios con rol 'docente'."""
    message = 'Se requiere rol de docente para realizar esta operación.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', '') == 'docente'
        )


class IsAlumno(BasePermission):
    """Permiso exclusivo para usuarios con rol 'alumno'."""
    message = 'Se requiere rol de alumno para realizar esta operación.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', '') == 'alumno'
        )


class IsAlumnoOrDocente(BasePermission):
    """Permiso para usuarios con rol 'alumno' o 'docente'."""
    message = 'Se requiere autenticación para realizar esta operación.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', '') in ('docente', 'alumno')
        )
