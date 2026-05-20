from django.urls import path
from src.controllers import reportes_controller

# Aquí definiremos los GET del README más adelante
urlpatterns = [
    path('reportes/calificaciones/<str:materia_id>/', reportes_controller.descargar_calificaciones),
    path('reportes/asistencias/<str:materia_id>/', reportes_controller.descargar_asistencias),
    path('reportes/estadisticas/<str:materia_id>/', reportes_controller.obtener_estadisticas), # Global de la materia
    path('reportes/estadisticas/docente/<str:id>/', reportes_controller.obtener_estadisticas_docente),
    path('reportes/estadisticas/alumno/<str:id>/', reportes_controller.obtener_estadisticas_alumno),
]