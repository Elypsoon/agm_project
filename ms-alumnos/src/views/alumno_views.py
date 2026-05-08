"""Vistas — Alumnos."""

import logging
from datetime import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

from src.models.alumno import Alumno
from src.models.inscripcion import Inscripcion
from src.serializers.alumno_serializer import AlumnoSerializer, AlumnoDetalleSerializer
from src.services.alumno_service import AlumnoService

logger = logging.getLogger(__name__)


class AlumnosByMateriaView(APIView):
    """GET /alumnos/materia/<uuid>/ — Listar alumnos inscritos activos."""

    def get(self, request, materia_id):
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 10))

        qs = Alumno.objects.filter(
            inscripciones__materia_id=materia_id,
            inscripciones__activo=True,
        ).distinct().order_by("nombre_completo")

        total = qs.count()
        alumnos = qs[(page - 1) * limit: page * limit]
        serializer = AlumnoSerializer(alumnos, many=True)

        return Response({
            "success": True,
            "data": {
                "alumnos": serializer.data,
                "total": total,
                "page": page,
                "limit": limit,
                "materia_id": str(materia_id),
            },
            "message": f"{len(serializer.data)} alumnos encontrados",
        })


class AlumnoDetailView(APIView):
    """GET /alumnos/<uuid>/ — Detalle con inscripciones."""

    def get(self, request, alumno_id):
        try:
            alumno = Alumno.objects.prefetch_related("inscripciones").get(id=alumno_id)
        except Alumno.DoesNotExist:
            return Response({"detail": "Alumno no encontrado"}, status=404)

        serializer = AlumnoDetalleSerializer(alumno)
        return Response({
            "success": True,
            "data": serializer.data,
            "message": "",
        })


from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class AlumnoImportView(APIView):
    """POST /alumnos/importar/<uuid>/ — Importar desde PDF."""
    parser_classes = [MultiPartParser]

    @swagger_auto_schema(
        operation_description="Importa alumnos masivamente a una materia específica desde el PDF de Lista de Clase (Banner).",
        manual_parameters=[
            openapi.Parameter(
                "materia_id",
                openapi.IN_PATH,
                description="ID (UUID) de la materia a la que se inscribirán los alumnos",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
                required=True,
            ),
            openapi.Parameter(
                "archivo",
                openapi.IN_FORM,
                description="Archivo PDF de la Lista de Clase (BUAP Banner)",
                type=openapi.TYPE_FILE,
                required=True,
            )
        ],
        responses={200: "Importación exitosa", 400: "Error en la petición", 422: "Error procesando el PDF"}
    )

    def post(self, request, materia_id):
        archivo = request.FILES.get("archivo")
        if not archivo:
            return Response({"detail": "No se envió archivo"}, status=400)

        service = AlumnoService()
        result = service.importar_desde_pdf(materia_id, archivo)
        status = result.pop("status_code", 200 if result["success"] else 422)
        return Response(result, status=status)


class AlumnoBajaView(APIView):
    """DELETE /alumnos/<uuid>/baja/?materia_id=<uuid> — Baja irreversible."""

    def delete(self, request, alumno_id):
        materia_id = request.query_params.get("materia_id")
        if not materia_id:
            return Response({"detail": "materia_id es requerido"}, status=400)

        service = AlumnoService()
        result = service.dar_de_baja(alumno_id, materia_id)
        return Response(result, status=result.get("status_code", 200))
