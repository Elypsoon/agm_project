"""
MS-3: URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="MS-3 — Docentes & Alumnos",
        default_version="v1",
        description="Microservicio de gestión de docentes y alumnos del sistema AGM",
    ),
    public=True,
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API
    path("docentes/", include("src.views.docente_urls")),
    path("alumnos/", include("src.views.alumno_urls")),
    # Health
    path("health/", include("src.views.health_urls")),
    # Swagger
    path("docs/", schema_view.with_ui("swagger", cache_timeout=0), name="docs"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="redoc"),
]
