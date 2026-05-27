from rest_framework.views import APIView
from rest_framework.response import Response

from src.controllers.serializers import ActividadInputSerializer, ActividadSerializer

from src.services.actividad_service import crear_actividad, PonderacionNoEncontrada, PonderacionMateriaNoCoincide
from src.services.autorizacion_service import (
    verificar_docente_sobre_materia,
    DocenteSinAutorizacion,
    MateriaNoAccesible,
    MateriaCerradaError,
)

from src.utils.authentication import GrpcJWTAuthentication
from src.utils.permissions import IsDocente


class ActividadView(APIView):
    """Vista para la gestión de actividades evaluables dentro del microservicio.

    Esta vista permite a los usuarios con rol de docente autenticados realizar operaciones
    sobre actividades académicas.
    """
    authentication_classes = [GrpcJWTAuthentication]
    permission_classes = [IsDocente]

    def post(self, request):
        """Crea una nueva actividad evaluable asociada a una ponderación específica.

        Este método valida que la petición provenga del docente asignado a la materia,
        que la materia se encuentre activa/abierta, y que la ponderación referenciada
        pertenezca realmente a dicha materia.

        Args:
            Request: Objeto de petición HTTP.
                El cuerpo debe contener:
                - materia_id (UUID): Identificador de la materia.
                - ponderacion_id (UUID): Identificador de la categoría de ponderación.
                - nombre (str): Nombre representativo de la actividad.
                - descripcion (str, opcional): Explicación detallada de la actividad.
                - estado (str, opcional): Estatus de la actividad (por defecto "pendiente").

        Returns:
            Response: Objeto de respuesta HTTP.
                - 201 Created: Mensaje de éxito y el objeto de la actividad serializado.
                - 400 Bad Request: Error de validación en la estructura de los datos de entrada.
                - 403 Forbidden: Si el docente no está asignado a la materia o si esta está cerrada.
                - 404 Not Found: Si la ponderación especificada no existe.
                - 409 Conflict: Si la ponderación no coincide con la materia.
                - 503 Service Unavailable: Si hay un error de conexión con otros microservicios.
        """
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

