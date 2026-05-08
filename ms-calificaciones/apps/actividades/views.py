from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import ActividadInputSerializer, ActividadSerializer
from .services import crear_actividad, CategoriaNoEncontrada, CategoriaMateriaNoCoincide

class ActividadView(APIView):
    def post(self, request):
        input_serializer = ActividadInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        data = input_serializer.validated_data

        try:
            actividad = crear_actividad(
                materia_id=data['materia_id'],
                categoria_id=data['categoria_id'],
                nombre=data['nombre'],
            )
        except CategoriaNoEncontrada as exc:
            return Response({'detail': str(exc)}, status=404)
        except CategoriaMateriaNoCoincide as exc:
            return Response({'detail': str(exc)}, status=409)
        
        return Response(
            {
                'message': 'Actividad creada exitosamente.',
                'data': ActividadSerializer(actividad).data
            },
            status=201,
        )