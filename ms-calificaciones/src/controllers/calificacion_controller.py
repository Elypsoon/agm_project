from rest_framework.views import APIView
from rest_framework.response import Response

from src.controllers.serializers import CalificacionInputSerializer, CalificacionSerializer

from src.services.calificacion_service import (
    upsert_calificacion,
    importar_calificaciones,
    ActividadNoEncontrada,
    AlumnoNoInscrito,
    ServicioExternoInaccesible,
)
from src.services.autorizacion_service import MateriaCerradaError, MateriaNoAccesible

from src.utils.authentication import GrpcJWTAuthentication
from src.utils.permissions import IsDocente


class CalificacionView(APIView):
    """Vista para el registro individual de calificaciones.

    Permite a los docentes asignar o actualizar la calificación obtenida por un
    alumno en una actividad específica.
    """
    authentication_classes = [GrpcJWTAuthentication]
    permission_classes = [IsDocente]

    def post(self, request):
        """Registra o actualiza la calificación de un alumno.

        Verifica que el alumno se encuentre inscrito en la materia y que la materia
        no esté cerrada.

        Args:
            Request: Objeto de petición HTTP.
                El cuerpo debe incluir:
                - actividad_id (UUID): Identificador de la actividad evaluable.
                - alumno_id (UUID): Identificador del estudiante.
                - valor (Decimal): Nota numérica (rango de 0.00 a 100.00).

        Returns:
            Response: Objeto de respuesta HTTP.
                - 200 OK: Calificación actualizada con éxito.
                - 201 Created: Calificación registrada por primera vez.
                - 400 Bad Request: Error en la estructura de los datos de entrada.
                - 403 Forbidden: Si la materia está cerrada para cambios.
                - 404 Not Found: Si la actividad evaluable no existe.
                - 422 Unprocessable Entity: Si el estudiante no está inscrito o activo en la materia.
                - 503 Service Unavailable: Error de conexión gRPC.
        """
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
        except AlumnoNoInscrito as exc:
            return Response({'detail': str(exc)}, status=422)
        except MateriaCerradaError as exc:
            return Response({'detail': str(exc)}, status=403)
        except MateriaNoAccesible as exc:
            return Response({'detail': str(exc)}, status=503)
        except ServicioExternoInaccesible as exc:
            return Response({'detail': str(exc)}, status=503)

        return Response(
            {
                'message': 'Calificación guardada exitosamente.',
                'data': CalificacionSerializer(calificacion).data
            },
            status=201 if created else 200,
        )


class ImportarCalificacionesView(APIView):
    """Vista para la importación masiva de calificaciones desde archivos.

    Permite a los docentes subir archivos (.xlsx o .csv) exportados de Microsoft Teams
    para asignar múltiples notas de manera ágil.
    """
    authentication_classes = [GrpcJWTAuthentication]
    permission_classes = [IsDocente]

    def post(self, request):
        """Carga y procesa un archivo de calificaciones grupales.

        Valida que el formato del archivo coincida con la plantilla soportada, que la
        materia exista y que no esté bloqueada/cerrada. Las calificaciones cargadas
        son registradas masivamente en una transacción.

        Args:
            Request: Objeto de petición HTTP.
                Debe enviarse como tipo 'multipart/form-data' incluyendo:
                - archivo (File): Archivo CSV o Excel.
                - materia_id (UUID): Identificador de la materia de destino.

        Returns:
            Response: Objeto de respuesta HTTP.
                - 201 Created: Estadísticas detalladas del proceso de importación
                  (registros creados, actualizados y errores encontrados).
                - 400 Bad Request: Extensión de archivo inválida o campos faltantes.
                - 403 Forbidden: Si la materia está en estado cerrado.
                - 503 Service Unavailable: Falla de comunicación con otros servicios.
        """
        import logging
        logger = logging.getLogger(__name__)

        archivo = request.FILES.get('archivo')
        materia_id = request.data.get('materia_id')
        criterio_evaluacion = request.data.get('criterio_evaluacion')

        if not archivo:
            logger.warning("Falta el archivo en la peticion de importacion")
            return Response({'detail': 'Se requiere el campo "archivo".'}, status=400)
        if not materia_id:
            logger.warning("Falta materia_id en la peticion de importacion")
            return Response({'detail': 'Se requiere el campo "materia_id".'}, status=400)

        try:
            resultado = importar_calificaciones(
                materia_id=materia_id,
                nombre_archivo=archivo.name,
                archivo_bytes=archivo.read(),
                criterio_evaluacion=criterio_evaluacion,
            )
            logger.info("Importacion completada exitosamente para la materia %s", materia_id)
        except ValueError as exc:
            logger.warning("Error de validacion al importar calificaciones: %s", exc, exc_info=True)
            return Response({'detail': str(exc)}, status=400)
        except MateriaCerradaError as exc:
            logger.warning("Intento de importacion en materia cerrada %s", materia_id)
            return Response({'detail': str(exc)}, status=403)
        except MateriaNoAccesible as exc:
            logger.error("Error gRPC: materia no accesible %s: %s", materia_id, exc)
            return Response({'detail': str(exc)}, status=503)
        except ServicioExternoInaccesible as exc:
            logger.error("Servicio externo inaccesible durante importacion: %s", exc)
            return Response({'detail': str(exc)}, status=503)

        return Response(resultado, status=201)
