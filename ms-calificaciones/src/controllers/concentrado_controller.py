from rest_framework.views import APIView
from rest_framework.response import Response
from src.models.models import Ponderacion
from src.services.concentrado_service import build_concentrado
from src.utils.authentication import GrpcJWTAuthentication
from src.utils.permissions import IsAlumnoOrDocente

class ConcentradoView(APIView):
    authentication_classes = [GrpcJWTAuthentication]
    permission_classes = [IsAlumnoOrDocente]

    def get(self, request, materia_id):
        try:
            data = build_concentrado(materia_id)
        except Ponderacion.DoesNotExist:
            return Response({'detail': 'No se encontró la configuración de ponderación para esta materia.'}, status=404)

        return Response(data, status=200)
