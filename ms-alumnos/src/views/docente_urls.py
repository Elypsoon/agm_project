"""URLs — Docentes."""

from django.urls import path
from src.views.docente_views import DocenteListView, DocenteDetailView, DocenteImportView

urlpatterns = [
    path("", DocenteListView.as_view(), name="docente-list"),
    path("importar/", DocenteImportView.as_view(), name="docente-import"),
    path("<uuid:docente_id>/", DocenteDetailView.as_view(), name="docente-detail"),
]
