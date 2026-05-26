from rest_framework.views import APIView
from rest_framework.response import Response

from src.controllers.serializers import ActividadInputSerializer, ActividadSerializer
from src.services.actividad_service import crear_actividad, PonderacionNoEncontrada, PonderacionMateriaNoCoincide
from src.utils.authentication import GrpcJWTAuthentication
from src.utils.permissions import IsDocente
from src.services.autorizacion_service import (
    verificar_docente_sobre_materia,
    DocenteSinAutorizacion,
    MateriaNoAccesible,
    MateriaCerradaError,
)

class ActividadView(APIView):
    authentication_classes = [GrpcJWTAuthentication]
    permission_classes = [IsDocente]

    def post(self, request):
        input_serializer = ActividadInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        data = input_serializer.validated_data

        try:
            verificar_docente_sobre_materia(request.user.user_id, data['materia_id'])
        except DocenteSinAutorizacion as exc:
            return Response({'detail': str(exc)}, status=403)
        except MateriaNoAccesible as exc:
            return Response({'detail': str(exc)}, status=503)

        try:
            actividad = crear_actividad(
                materia_id=data['materia_id'],
                ponderacion_id=data['ponderacion_id'],
                nombre=data['nombre'],
                descripcion=data.get('descripcion', ''),
                estado=data.get('estado', 'pendiente'),
            )
        except PonderacionNoEncontrada as exc:
            return Response({'detail': str(exc)}, status=404)
        except PonderacionMateriaNoCoincide as exc:
            return Response({'detail': str(exc)}, status=409)
        except MateriaCerradaError as exc:
            return Response({'detail': str(exc)}, status=403)
        except MateriaNoAccesible as exc:
            return Response({'detail': str(exc)}, status=503)
        
        return Response(
            {
                'message': 'Actividad creada exitosamente.',
                'data': ActividadSerializer(actividad).data
            },
            status=201,
        )
