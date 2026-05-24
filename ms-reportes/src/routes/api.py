from django.urls import path
from src.controllers import reportes_controller

urlpatterns = [
    # Exportación de Archivos
    path('calificaciones/<str:materia_id>/', reportes_controller.descargar_calificaciones),
    path('asistencias/<str:materia_id>/', reportes_controller.descargar_asistencias),
    path('rendimiento/<str:materia_id>/', reportes_controller.descargar_rendimiento),
    
    # Análisis Estadístico
    path('estadisticas/<str:materia_id>/', reportes_controller.obtener_estadisticas),
    path('estadisticas/docente/<str:id>/', reportes_controller.obtener_estadisticas_docente),
    path('estadisticas/alumno/<str:id>/', reportes_controller.obtener_estadisticas_alumno),
]