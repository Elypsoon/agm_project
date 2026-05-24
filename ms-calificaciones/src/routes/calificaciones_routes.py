from django.urls import path
from src.controllers.ponderacion_controller import PonderacionView
from src.controllers.actividad_controller import ActividadView
from src.controllers.calificacion_controller import CalificacionView, ImportarCalificacionesView
from src.controllers.concentrado_controller import ConcentradoView

urlpatterns = [
    # Ponderaciones
    path('ponderaciones/<uuid:materia_id>/', PonderacionView.as_view(), name='ponderaciones'),

    # Actividades
    path('actividades/', ActividadView.as_view(), name='actividades'),

    # Calificaciones
    path('calificaciones/', CalificacionView.as_view(), name='calificaciones'),
    path('calificaciones/importar/', ImportarCalificacionesView.as_view(), name='calificaciones-importar'),

    # Concentrado
    path('concentrado/<uuid:materia_id>/', ConcentradoView.as_view(), name='concentrado'),
]
