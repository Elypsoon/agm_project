from django.urls import path
from .views import (
    IniciarSesionView,
    RegistrarAsistenciaView,
    CerrarSesionView,
    AsistenciasHoyView,
    HistorialAsistenciasView,
    GenerarQRView,
    MisMateriasSesionView,
)

urlpatterns = [
    # Sesiones
    path('sesiones/iniciar', IniciarSesionView.as_view(), name='iniciar-sesion'),
    path('sesiones/<uuid:sesion_id>/cerrar', CerrarSesionView.as_view(), name='cerrar-sesion'),

    # Asistencias
    path('asistencias/registrar', RegistrarAsistenciaView.as_view(), name='registrar-asistencia'),
    path('asistencias/<uuid:materia_id>/hoy', AsistenciasHoyView.as_view(), name='asistencias-hoy'),
    path('asistencias/<uuid:materia_id>/historial', HistorialAsistenciasView.as_view(), name='historial-asistencias'),

    # QR
    path('asistencias/qr/generar', GenerarQRView.as_view(), name='generar-qr'),

    # Materias del docente (via gRPC a MS-2)
    path('materias/mis-materias', MisMateriasSesionView.as_view(), name='mis-materias'),
]