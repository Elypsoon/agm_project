from django.urls import path
from src.controllers import notificacion_controller

urlpatterns = [
    path('bienvenida', notificacion_controller.send_bienvenida),
    path('baja', notificacion_controller.send_baja),
    path('cierre-materia', notificacion_controller.send_cierre),
    path('reset-password', notificacion_controller.send_reset),
]