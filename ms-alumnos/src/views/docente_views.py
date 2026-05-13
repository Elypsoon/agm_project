"""Vistas — Docentes."""

import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from src.models.docente import Docente
from src.serializers.docente_serializer import DocenteSerializer
from src.services.docente_service import DocenteService

logger = logging.getLogger(__name__)


class DocenteListView(APIView):
    """GET /docentes/ — Listar con búsqueda y paginación."""

    @swagger_auto_schema(
        operation_description="Lista los docentes registrados. Permite buscar por nombre, correo o cubículo.",
        manual_parameters=[
            openapi.Parameter("search", openapi.IN_QUERY, description="Término de búsqueda", type=openapi.TYPE_STRING),
            openapi.Parameter("page", openapi.IN_QUERY, description="Número de página (default: 1)", type=openapi.TYPE_INTEGER),
            openapi.Parameter("limit", openapi.IN_QUERY, description="Límite de resultados por página (default: 10)", type=openapi.TYPE_INTEGER),
        ],
        responses={200: "Lista de docentes"}
    )
    def get(self, request):
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 10))
        search = request.query_params.get("search")

        qs = Docente.objects.all()
        if search:
            filtro = Q(nombre_completo__icontains=search) | \
                     Q(correo_institucional__icontains=search) | \
                     Q(cubiculo__icontains=search)
            qs = qs.filter(filtro)

        total = qs.count()
        docentes = qs.order_by("nombre_completo")[(page - 1) * limit: page * limit]
        serializer = DocenteSerializer(docentes, many=True)

        return Response({
            "success": True,
            "data": {
                "docentes": serializer.data,
                "total": total,
                "page": page,
                "limit": limit,
            },
            "message": f"{len(serializer.data)} docentes encontrados",
        })


class DocenteDetailView(APIView):
    """GET /docentes/<uuid>/ — Detalle de un docente."""

    def get(self, request, docente_id):
        try:
            docente = Docente.objects.get(id=docente_id)
        except Docente.DoesNotExist:
            return Response(
                {"detail": "Docente no encontrado"}, status=404
            )

        serializer = DocenteSerializer(docente)
        return Response({
            "success": True,
            "data": serializer.data,
            "message": "",
        })


class DocenteImportView(APIView):
    """POST /docentes/importar/ — Importar desde PDF."""
    parser_classes = [MultiPartParser]

    @swagger_auto_schema(
        operation_description="Importa docentes masivamente desde el PDF del Directorio de la FCC.",
        manual_parameters=[
            openapi.Parameter(
                "archivo",
                openapi.IN_FORM,
                description="Archivo PDF del Directorio FCC BUAP",
                type=openapi.TYPE_FILE,
                required=True,
            )
        ],
        responses={200: "Importación exitosa", 400: "Error en la petición", 422: "Error procesando el PDF"}
    )
    def post(self, request):
        archivo = request.FILES.get("archivo")
        if not archivo:
            return Response({"detail": "No se envió archivo"}, status=400)

        service = DocenteService()
        result = service.importar_desde_pdf(archivo)
        status = result.pop("status_code", 200 if result["success"] else 422)
        return Response(result, status=status)
