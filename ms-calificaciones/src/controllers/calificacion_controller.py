from rest_framework.views import APIView
from rest_framework.response import Response

from src.controllers.serializers import CalificacionInputSerializer, CalificacionSerializer
from src.services.calificacion_service import upsert_calificacion, ActividadNoEncontrada, importar_calificaciones
from src.utils.authentication import GrpcJWTAuthentication
from src.utils.permissions import IsDocente

class CalificacionView(APIView):
    authentication_classes = [GrpcJWTAuthentication]
    permission_classes = [IsDocente]

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

        return Response(
            {
                'message': 'Calificación guardada exitosamente.',
                'data': CalificacionSerializer(calificacion).data
            },
            status=201 if created else 200,
        )

class ImportarCalificacionesView(APIView):
    authentication_classes = [GrpcJWTAuthentication]
    permission_classes = [IsDocente]

    def post(self, request):
        archivo = request.FILES.get('archivo')
        materia_id = request.data.get('materia_id')

        if not archivo:
            return Response({'detail': 'Se requiere el campo "archivo".'}, status=400)
        if not materia_id:
            return Response({'detail': 'Se requiere el campo "materia_id".'}, status=400)

        try:
            resultado = importar_calificaciones(
                materia_id=materia_id,
                nombre_archivo=archivo.name,
                archivo_bytes=archivo.read(),
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)

        return Response(resultado, status=201)
