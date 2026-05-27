from rest_framework.views import APIView
from rest_framework.response import Response

from src.models.models import Ponderacion

from src.services.estadisticas_service import get_estadisticas_materia, get_estadisticas_alumno

from src.utils.authentication import GrpcJWTAuthentication
from src.utils.permissions import IsAlumnoOrDocente


class EstadisticasMateriaView(APIView):
    """Vista para consultar las estadísticas grupales de una materia.

    Expone métricas agregadas del grupo (como promedio de grupo, nota máxima,
    nota mínima y total de estudiantes) basadas en promedios ponderados.
    """
    authentication_classes = [GrpcJWTAuthentication]
    permission_classes = [IsAlumnoOrDocente]

    def get(self, request, materia_id):
        """Retorna las estadísticas del grupo completo para la materia especificada.

        Calcula el promedio grupal como la media aritmética de los promedios ponderados
        de cada estudiante inscrito.

        Args:
            Request: Objeto de petición HTTP.
            materia_id (UUID): Identificador único de la materia.

        Returns:
            Response: Objeto de respuesta HTTP.
                - 200 OK: Métricas estadísticas en formato JSON.
                - 404 Not Found: Si la materia no cuenta con ponderaciones configuradas.
                - 403 Forbidden: Si el usuario no tiene permisos sobre la materia.
        """
        try:
            data = get_estadisticas_materia(materia_id)
        except Ponderacion.DoesNotExist:
            return Response(
                {'detail': 'No existe configuración de ponderación para esta materia.'},
                status=404
            )
        return Response(data, status=200)


class EstadisticasAlumnoView(APIView):
    """Vista para consultar el desempeño individual de un alumno en una materia.

    Expone el promedio real (escala 0-100), el promedio redondeado (escala 0-10) y un
    desglose detallado por categoría de ponderación con sus respectivas actividades.
    """
    authentication_classes = [GrpcJWTAuthentication]
    permission_classes = [IsAlumnoOrDocente]

    def get(self, request, alumno_id, materia_id):
        """Retorna el desglose ponderado y promedios individuales del alumno.

        Calcula la nota acumulada del alumno cruzando sus calificaciones con los
        porcentajes asignados a cada categoría.

        Args:
            Request: Objeto de petición HTTP.
            alumno_id (UUID): Identificador del estudiante.
            materia_id (UUID): Identificador de la materia.

        Returns:
            Response: Objeto de respuesta HTTP.
                - 200 OK: Desglose completo y promedios del estudiante.
                - 404 Not Found: Si la materia no cuenta con ponderaciones configuradas.
                - 403 Forbidden: Si el usuario no tiene permisos.
        """
        try:
            data = get_estadisticas_alumno(alumno_id, materia_id)
        except Ponderacion.DoesNotExist:
            return Response(
                {'detail': 'No existe configuración de ponderación para esta materia.'},
                status=404
            )
        return Response(data, status=200)
