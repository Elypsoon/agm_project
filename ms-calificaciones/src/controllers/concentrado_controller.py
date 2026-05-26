from rest_framework.views import APIView
from rest_framework.response import Response

from src.models.models import Ponderacion

from src.services.concentrado_service import build_concentrado

from src.utils.authentication import GrpcJWTAuthentication
from src.utils.permissions import IsDocente


class ConcentradoView(APIView):
    """Vista para consultar el concentrado (acta) completo de calificaciones de una materia.

    Permite a docentes asignados obtener la lista completa de estudiantes con 
    sus respectivos desgloses de actividades y promedios.
    """
    authentication_classes = [GrpcJWTAuthentication]
    permission_classes = [IsDocente]

    def get(self, request, materia_id):
        """Obtiene la matriz completa de calificaciones de la materia.

        Genera una vista matricial en donde cada renglón corresponde a un alumno,
        mostrando sus calificaciones en cada actividad evaluable, el promedio final
        real y el promedio redondeado.

        Args:
            Request: Objeto de petición HTTP.
            materia_id (UUID): Identificador único de la materia en la URL.

        Returns:
            Response: Objeto de respuesta HTTP.
                - 200 OK: Estructura JSON del concentrado con metadata del curso
                  y el listado de calificaciones detalladas por alumno.
                - 404 Not Found: Si la materia no cuenta con un esquema de ponderación configurado.
                - 403 Forbidden: Si el usuario no tiene permisos de visualización.
        """
        try:
            data = build_concentrado(materia_id)
        except Ponderacion.DoesNotExist:
            return Response({'detail': 'No se encontró la configuración de ponderación para esta materia.'}, status=404)

        return Response(data, status=200)
