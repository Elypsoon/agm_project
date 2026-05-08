from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import CalificacionInputSerializer, CalificacionSerializer
from .services import upsert_calificacion, ActividadNoEncontrada

class CalificacionView(APIView):
    def post(self, request):
        input_serializer = CalificacionInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data

        try:
            calificacion, created = upsert_calificacion(
                actividad_id=data['actividad_id'],
                alumno_id=data['alumno_id'],
                valor=data['valor'],
            )
        except ActividadNoEncontrada as exc:
            return Response({'detail': str(exc)}, status=404)
        
        mensaje = 'Calificacion registrada.' if created else 'Calificación actualizada.'

        return Response(
            {
                'message': mensaje,
                'data': CalificacionSerializer(calificacion).data
            },
            status=201 if created else 200,
        )