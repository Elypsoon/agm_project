from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from src.models.models import PonderacionConfig
from src.controllers.serializers import (
    PonderacionConfigSerializer, 
    PonderacionConfigInputSerializer,
)
from src.services.ponderacion_service import (
    upsert_config, 
    replace_config, 
    PonderacionSumaInvalida, 
    PonderacionBloqueada, 
    PonderacionCategoriasRestringidas,
)
from src.utils.authentication import GrpcJWTAuthentication
from src.utils.permissions import IsDocente, IsAlumnoOrDocente
from src.services.autorizacion_service import (
    verificar_docente_sobre_materia,
    DocenteSinAutorizacion,
    MateriaNoAccesible,
)

class PonderacionView(APIView):
    authentication_classes = [GrpcJWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAlumnoOrDocente()]
        return [IsDocente()]

    def get(self, request, materia_id):
        try:
            config = PonderacionConfig.objects.get(materia_id=materia_id)
        except PonderacionConfig.DoesNotExist:
            return Response({"detail": "Configuracion no encontrada."}, status=404)

        return Response(PonderacionConfigSerializer(config).data)

    def post(self, request, materia_id):
        input_serializer = PonderacionConfigInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            verificar_docente_sobre_materia(request.user.user_id, materia_id)
        except DocenteSinAutorizacion as exc:
            return Response({"detail": str(exc)}, status=403)
        except MateriaNoAccesible as exc:
            return Response({"detail": str(exc)}, status=503)

        try:
            config, created = upsert_config(
                materia_id, input_serializer.validated_data["categorias"]
            )
        except PonderacionSumaInvalida as exc:
            return Response({"detail": str(exc)}, status=400)
        except PonderacionBloqueada as exc:
            return Response({"detail": str(exc)}, status=409)
        except PonderacionCategoriasRestringidas as exc:
            return Response({"detail": str(exc)}, status=409)

        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(PonderacionConfigSerializer(config).data, status=status_code)

    def put(self, request, materia_id):
        input_serializer = PonderacionConfigInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            verificar_docente_sobre_materia(request.user.user_id, materia_id)
        except DocenteSinAutorizacion as exc:
            return Response({"detail": str(exc)}, status=403)
        except MateriaNoAccesible as exc:
            return Response({"detail": str(exc)}, status=503)

        try:
            config = replace_config(
                materia_id, input_serializer.validated_data["categorias"]
            )
        except PonderacionConfig.DoesNotExist:
            return Response({"detail": "Configuracion no encontrada."}, status=404)
        except PonderacionSumaInvalida as exc:
            return Response({"detail": str(exc)}, status=400)
        except PonderacionBloqueada as exc:
            return Response({"detail": str(exc)}, status=409)
        except PonderacionCategoriasRestringidas as exc:
            return Response({"detail": str(exc)}, status=409)

        return Response(PonderacionConfigSerializer(config).data, status=200)
