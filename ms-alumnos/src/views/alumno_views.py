"""Vistas — Alumnos."""

import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from src.models.alumno import Alumno
from src.serializers.alumno_serializer import AlumnoSerializer, AlumnoDetalleSerializer
from src.services.alumno_service import AlumnoService

logger = logging.getLogger(__name__)


from django.db.models import Q

class AlumnoListView(APIView):
    """GET /alumnos/ — Listar con búsqueda y paginación global."""

    @swagger_auto_schema(
        operation_description="Lista los alumnos registrados globalmente. Permite buscar por nombre, correo o matrícula.",
        manual_parameters=[
            openapi.Parameter("search", openapi.IN_QUERY, description="Término de búsqueda", type=openapi.TYPE_STRING),
            openapi.Parameter("page", openapi.IN_QUERY, description="Número de página (default: 1)", type=openapi.TYPE_INTEGER),
            openapi.Parameter("limit", openapi.IN_QUERY, description="Límite de resultados por página (default: 10)", type=openapi.TYPE_INTEGER),
        ],
        responses={200: "Lista de alumnos"}
    )
    def get(self, request):
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 10))
        search = request.query_params.get("search")

        qs = Alumno.objects.all()
        if search:
            filtro = Q(nombre_completo__icontains=search) | \
                     Q(correo__icontains=search) | \
                     Q(matricula__icontains=search)
            qs = qs.filter(filtro)

        total = qs.count()
        alumnos = qs.order_by("nombre_completo")[(page - 1) * limit: page * limit]
        serializer = AlumnoSerializer(alumnos, many=True)

        return Response({
            "success": True,
            "data": {
                "alumnos": serializer.data,
                "total": total,
                "page": page,
                "limit": limit,
            },
            "message": f"{len(serializer.data)} alumnos encontrados",
        })


class AlumnosByMateriaView(APIView):
    """GET /alumnos/materia/<uuid>/ — Listar alumnos inscritos activos."""

    @swagger_auto_schema(
        operation_description="Lista los alumnos inscritos activos en una materia específica.",
        manual_parameters=[
            openapi.Parameter("search", openapi.IN_QUERY, description="Término de búsqueda", type=openapi.TYPE_STRING),
            openapi.Parameter("page", openapi.IN_QUERY, description="Número de página (default: 1)", type=openapi.TYPE_INTEGER),
            openapi.Parameter("limit", openapi.IN_QUERY, description="Límite de resultados por página (default: 10)", type=openapi.TYPE_INTEGER),
        ],
        responses={200: "Lista de alumnos de la materia"}
    )
    def get(self, request, materia_id):
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 10))
        search = request.query_params.get("search")

        qs = Alumno.objects.filter(
            inscripciones__materia_id=materia_id,
            inscripciones__activo=True,
        )
        if search:
            filtro = Q(nombre_completo__icontains=search) | \
                     Q(correo__icontains=search) | \
                     Q(matricula__icontains=search)
            qs = qs.filter(filtro)
            
        qs = qs.distinct().order_by("nombre_completo")

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
        from django.core.exceptions import ValidationError
        try:
            # Intentar buscar por id o por user_id de forma flexible
            alumno = Alumno.objects.prefetch_related("inscripciones").filter(
                Q(id=alumno_id) | Q(user_id=alumno_id)
            ).first()
            if not alumno:
                raise Alumno.DoesNotExist
        except (Alumno.DoesNotExist, ValidationError, ValueError):
            try:
                alumno = Alumno.objects.prefetch_related("inscripciones").get(correo=alumno_id)
            except Alumno.DoesNotExist:
                return Response({"detail": "Alumno no encontrado"}, status=404)

        serializer = AlumnoDetalleSerializer(alumno)
        return Response({
            "success": True,
            "data": serializer.data,
            "message": "",
        })


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

    @swagger_auto_schema(
        operation_description="Da de baja permanentemente a un alumno de una materia.",
        manual_parameters=[
            openapi.Parameter("materia_id", openapi.IN_QUERY, description="ID (UUID) de la materia de la cual se dará de baja al alumno", type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID, required=True),
        ],
        responses={200: "Baja exitosa", 400: "Error en la petición", 404: "Alumno no inscrito"}
    )
    def delete(self, request, alumno_id):
        materia_id = request.query_params.get("materia_id")
        if not materia_id:
            return Response({"detail": "materia_id es requerido"}, status=400)

        service = AlumnoService()
        result = service.dar_de_baja(alumno_id, materia_id)
        return Response(result, status=result.get("status_code", 200))
