from rest_framework.permissions import BasePermission


class EsDocente(BasePermission):
    """Solo usuarios con rol 'docente' o 'administrador'."""
    message = "Solo los docentes pueden realizar esta acción."

    def has_permission(self, request, view):
        return (
            hasattr(request.user, 'rol') and
            request.user.rol in ('docente', 'administrador')
        )


class EsAlumno(BasePermission):
    """Solo usuarios con rol 'alumno'."""
    message = "Solo los alumnos pueden realizar esta acción."

    def has_permission(self, request, view):
        return (
            hasattr(request.user, 'rol') and
            request.user.rol == 'alumno'
        )


class EsDocenteOAlumno(BasePermission):
    """Docentes y alumnos pueden acceder."""

    def has_permission(self, request, view):
        return (
            hasattr(request.user, 'rol') and
            request.user.rol in ('docente', 'administrador', 'alumno')
        )