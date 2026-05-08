"""URLs — Health check."""

from django.urls import path
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Endpoint de salud para verificar que el servicio esta activo."""
    return Response({
        "success": True,
        "data": {
            "service": "ms-alumnos",
            "status": "healthy",
            "version": "1.0.0",
            "ports": {
                "rest": settings.REST_PORT,
                "grpc": settings.GRPC_PORT,
            },
        },
        "message": "MS-3 Docentes & Alumnos operativo",
    })


urlpatterns = [
    path("", health_check, name="health-check"),
]
