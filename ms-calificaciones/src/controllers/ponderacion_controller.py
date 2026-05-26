from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from src.models.models import Ponderacion

from src.controllers.serializers import (
    PonderacionSerializer, 
    PonderacionConfigInputSerializer,
)

from src.services.ponderacion_service import (
    upsert_config, 
    replace_config, 
    PonderacionSumaInvalida, 
    PonderacionBloqueada, 
    PonderacionCategoriasRestringidas,
)
from src.services.autorizacion_service import (
    verificar_docente_sobre_materia,
    DocenteSinAutorizacion,
    MateriaNoAccesible,
    MateriaCerradaError,
)

from src.utils.authentication import GrpcJWTAuthentication
from src.utils.permissions import IsDocente, IsAlumnoOrDocente


class PonderacionView(APIView):
    """Vista para configurar y consultar el esquema de ponderaciones de una materia.

    Administra las categorías de evaluación y sus respectivos porcentajes. Los 
    alumnos inscritos y docentes asignados pueden consultar (GET) la configuración, 
    pero solo los docentes autorizados pueden crear (POST) o reemplazar (PUT) el esquema.
    """
    authentication_classes = [GrpcJWTAuthentication]

    def get_permissions(self):
        """Asigna permisos dinámicamente según el método de acceso HTTP.

        - GET: Permitido para Alumnos inscritos o Docentes asignados a la materia.
        - POST/PUT: Exclusivo para Docentes de la materia.
        """
        if self.request.method == 'GET':
            return [IsAlumnoOrDocente()]
        return [IsDocente()]

    def get(self, request, materia_id):
        """Consulta el esquema de ponderaciones activo para la materia.

        Args:
            Request: Objeto de petición HTTP.
            materia_id: Identificador único de la materia.

        Returns:
            Response: Objeto de respuesta HTTP.
                - 200 OK: Objeto JSON con el listado de categorías activas y porcentajes.
                - 404 Not Found: Si la materia no cuenta con un esquema de ponderación registrado.
        """
        ponderaciones = Ponderacion.objects.filter(materia_id=materia_id, activa=True)
        if not ponderaciones.exists():
            return Response({"detail": "Configuracion no encontrada."}, status=404)

        data = {
            "materia_id": str(materia_id),
            "bloqueada": False, 
            "categorias": [
                {
                    "id": str(p.id),
                    "nombre": p.nombre_categoria,
                    "porcentaje": p.porcentaje
                }
                for p in ponderaciones
            ]
        }
        return Response(data)

    def post(self, request, materia_id):
        """Crea o actualiza parcialmente la configuración de ponderación.

        Este método valida que la suma de porcentajes de las categorías propuestas
        sea exactamente del 100%.

        Args:
            Request: Objeto de petición HTTP.
                El cuerpo debe incluir:
                - categorias (list): Listado de objetos de tipo `{"nombre": str, "porcentaje": Decimal}`.
            materia_id (UUID): Identificador único de la materia.

        Returns:
            Response: Objeto de respuesta HTTP.
                - 200 OK: Si el esquema se actualizó.
                - 201 Created: Si se creó un esquema inicial de ponderaciones.
                - 400 Bad Request: Si la suma de porcentajes no es 100% o hay nombres duplicados.
                - 403 Forbidden: Si el docente no está asignado o la materia está cerrada.
                - 409 Conflict: Si la ponderación está bloqueada por tener actividades evaluadas 
                  y se intenta alterar una categoría protegida.
                - 503 Service Unavailable: Error de conexión.
        """
        input_serializer = PonderacionConfigInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            verificar_docente_sobre_materia(request.user.user_id, materia_id)
        except DocenteSinAutorizacion as exc:
            return Response({"detail": str(exc)}, status=403)
        except MateriaNoAccesible as exc:
            return Response({"detail": str(exc)}, status=503)

        try:
            config_list, created = upsert_config(materia_id, input_serializer.validated_data["categorias"])
        except PonderacionSumaInvalida as exc:
            return Response({"detail": str(exc)}, status=400)
        except PonderacionBloqueada as exc:
            return Response({"detail": str(exc)}, status=409)
        except PonderacionCategoriasRestringidas as exc:
            return Response({"detail": str(exc)}, status=409)
        except MateriaCerradaError as exc:
            return Response({"detail": str(exc)}, status=403)
        except MateriaNoAccesible as exc:
            return Response({"detail": str(exc)}, status=503)

        data = {
            "materia_id": str(materia_id),
            "bloqueada": False,
            "categorias": [
                {
                    "id": str(p.id),
                    "nombre": p.nombre_categoria,
                    "porcentaje": p.porcentaje
                }
                for p in config_list
            ]
        }
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(data, status=status_code)

    def put(self, request, materia_id):
        """Reemplaza por completo el esquema de ponderación de la materia.

        Este método inactiva las ponderaciones anteriores y registra el nuevo listado.
        No está permitido si ya existen actividades con calificaciones registradas
        bajo categorías que se intentan eliminar o reducir de peso.

        Args:
            Request: Objeto de petición HTTP.
                El cuerpo debe incluir:
                - categorias (list): Listado de objetos de tipo `{"nombre": str, "porcentaje": Decimal}`.
            materia_id (UUID): Identificador único de la materia.

        Returns:
            Response: Objeto de respuesta HTTP.
                - 200 OK: Esquema reemplazado exitosamente.
                - 400 Bad Request: Suma de porcentajes diferente de 100% o nombres duplicados.
                - 403 Forbidden: Si el docente no está asignado o la materia está cerrada.
                - 404 Not Found: Si no existía configuración previa para reemplazar.
                - 409 Conflict: Si el esquema está bloqueado por contener calificaciones registradas.
                - 503 Service Unavailable: Error de conexión.
        """
        input_serializer = PonderacionConfigInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            verificar_docente_sobre_materia(request.user.user_id, materia_id)
        except DocenteSinAutorizacion as exc:
            return Response({"detail": str(exc)}, status=403)
        except MateriaNoAccesible as exc:
            return Response({"detail": str(exc)}, status=503)

        try:
            config_list = replace_config(materia_id, input_serializer.validated_data["categorias"])
        except Ponderacion.DoesNotExist:
            return Response({"detail": "Configuracion no encontrada."}, status=404)
        except PonderacionSumaInvalida as exc:
            return Response({"detail": str(exc)}, status=400)
        except PonderacionBloqueada as exc:
            return Response({"detail": str(exc)}, status=409)
        except PonderacionCategoriasRestringidas as exc:
            return Response({"detail": str(exc)}, status=409)
        except MateriaCerradaError as exc:
            return Response({"detail": str(exc)}, status=403)
        except MateriaNoAccesible as exc:
            return Response({"detail": str(exc)}, status=503)

        data = {
            "materia_id": str(materia_id),
            "bloqueada": False,
            "categorias": [
                {
                    "id": str(p.id),
                    "nombre": p.nombre_categoria,
                    "porcentaje": p.porcentaje
                }
                for p in config_list
            ]
        }
        return Response(data, status=200)

