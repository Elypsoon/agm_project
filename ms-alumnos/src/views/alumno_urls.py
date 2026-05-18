"""URLs — Alumnos."""

from django.urls import path
from src.views.alumno_views import (
    AlumnosByMateriaView, AlumnoDetailView, AlumnoImportView, AlumnoBajaView, AlumnoListView
)

urlpatterns = [
    path("", AlumnoListView.as_view(), name="alumno-list"),
    path("materia/<uuid:materia_id>/", AlumnosByMateriaView.as_view(), name="alumnos-by-materia"),
    path("importar/<uuid:materia_id>/", AlumnoImportView.as_view(), name="alumno-import"),
    path("<uuid:alumno_id>/baja/", AlumnoBajaView.as_view(), name="alumno-baja"),
    path("<uuid:alumno_id>/", AlumnoDetailView.as_view(), name="alumno-detail"),
]
