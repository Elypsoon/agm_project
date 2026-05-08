from rest_framework.views import APIView
from rest_framework.response import Response
from apps.ponderaciones.models import PonderacionConfig
from .services import build_concentrado

class ConcentradoView(APIView):
    def get(self, request, materia_id):
        try:
            data = build_concentrado(materia_id)
        except PonderacionConfig.DoesNotExist:
            return Response({'detail': 'No se encontró la configuración de ponderación para esta materia.'}, status=404)

        return Response(data, status=200)