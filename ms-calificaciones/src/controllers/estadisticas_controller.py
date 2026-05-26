from rest_framework.views import APIView
from rest_framework.response import Response

from src.services.estadisticas_service import get_estadisticas_materia, get_estadisticas_alumno
from src.models.models import Ponderacion
from src.utils.authentication import GrpcJWTAuthentication
from src.utils.permissions import IsAlumnoOrDocente


class EstadisticasMateriaView(APIView):
    authentication_classes = [GrpcJWTAuthentication]
    permission_classes = [IsAlumnoOrDocente]

    def get(self, request, materia_id):
        try:
            data = get_estadisticas_materia(materia_id)
        except Ponderacion.DoesNotExist:
            return Response(
                {'detail': 'No existe configuración de ponderación para esta materia.'},
                status=404
            )
        return Response(data, status=200)


class EstadisticasAlumnoView(APIView):
    authentication_classes = [GrpcJWTAuthentication]
    permission_classes = [IsAlumnoOrDocente]

    def get(self, request, alumno_id, materia_id):
        try:
            data = get_estadisticas_alumno(alumno_id, materia_id)
        except Ponderacion.DoesNotExist:
            return Response(
                {'detail': 'No existe configuración de ponderación para esta materia.'},
                status=404
            )
        return Response(data, status=200)
