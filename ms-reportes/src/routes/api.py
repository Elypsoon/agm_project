from django.urls import path
from src.controllers import reportes_controller

# Aquí definiremos los GET del README más adelante
urlpatterns = [
    path('calificaciones/<str:materia_id>/', reportes_controller.descargar_calificaciones, name='descargar_calificaciones'),
    path('asistencias/<str:materia_id>/', reportes_controller.descargar_asistencias, name='descargar_asistencias'),
    path('estadisticas/<str:materia_id>/', reportes_controller.obtener_estadisticas, name='obtener_estadisticas'),  
]