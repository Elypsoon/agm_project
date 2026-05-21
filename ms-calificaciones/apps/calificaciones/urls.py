from django.urls import path
from .views import CalificacionView, ImportarCalificacionesView

urlpatterns = [
    path('calificaciones/', CalificacionView.as_view(), name='calificaciones'),
    path('calificaciones/importar/', ImportarCalificacionesView.as_view(), name='calificaciones-importar')
]