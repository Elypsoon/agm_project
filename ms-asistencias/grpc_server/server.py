"""
Servidor gRPC del MS-5 Asistencias QR.
Puerto: 50055 (configurable via GRPC_PORT)

Métodos expuestos:
    - GetAsistenciaAlumno   → historial de asistencias de un alumno en una materia
    - GetEstadisticasAsistencia → estadísticas globales de una materia
"""

import os
import sys
from concurrent import futures

# Agregar la raíz del proyecto al path ANTES de cualquier otro import
sys.path.insert(0, '/app')

# Forzar que 'grpc' se importe desde site-packages y no desde carpeta local
import importlib
import importlib.util

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

# Importar grpc directamente desde site-packages
spec = importlib.util.spec_from_file_location(
    "grpc",
    "/usr/local/lib/python3.11/site-packages/grpc/__init__.py"
)
grpc = importlib.util.module_from_spec(spec)
sys.modules['grpc'] = grpc
spec.loader.exec_module(grpc)

from django.conf import settings
from grpc_generated import asistencias_pb2, asistencias_pb2_grpc
from asistencias.models import Sesion, Asistencia


class AsistenciasServicer(asistencias_pb2_grpc.AsistenciasServiceServicer):

    def GetAsistenciaAlumno(self, request, context):
        alumno_id = request.alumno_id
        materia_id = request.materia_id

        asistencias = Asistencia.objects.filter(
            alumno_id=alumno_id,
            materia_id=materia_id,
        ).select_related('sesion').order_by('-hora_registro')

        total_sesiones = Sesion.objects.filter(
            materia_id=materia_id,
            estado='cerrada'
        ).count()

        presentes = asistencias.filter(estado='presente').count()
        retardos = asistencias.filter(estado='retardo').count()
        ausentes = max(0, total_sesiones - presentes - retardos)
        porcentaje = (presentes + retardos) / total_sesiones * 100 if total_sesiones > 0 else 0.0

        items = []
        for a in asistencias:
            items.append(asistencias_pb2.AsistenciaItem(
                id=str(a.id),
                sesion_id=str(a.sesion_id),
                estado=a.estado,
                hora_registro=a.hora_registro.isoformat(),
                fecha=a.sesion.fecha.isoformat(),
            ))

        return asistencias_pb2.AsistenciaAlumnoResponse(
            alumno_id=alumno_id,
            materia_id=materia_id,
            total_clases=total_sesiones,
            total_presentes=presentes,
            total_retardos=retardos,
            total_ausentes=ausentes,
            porcentaje=porcentaje,
            asistencias=items,
        )

    def GetEstadisticasAsistencia(self, request, context):
        materia_id = request.materia_id

        total_sesiones = Sesion.objects.filter(materia_id=materia_id).count()
        asistencias = Asistencia.objects.filter(materia_id=materia_id)
        total_registros = asistencias.count()
        presentes = asistencias.filter(estado='presente').count()
        retardos = asistencias.filter(estado='retardo').count()
        porcentaje = (presentes + retardos) / total_registros * 100 if total_registros > 0 else 0.0

        return asistencias_pb2.EstadisticasResponse(
            materia_id=materia_id,
            total_sesiones=total_sesiones,
            total_registros=total_registros,
            total_presentes=presentes,
            total_retardos=retardos,
            porcentaje_global=porcentaje,
        )


def serve():
    port = settings.GRPC_PORT
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    asistencias_pb2_grpc.add_AsistenciasServiceServicer_to_server(AsistenciasServicer(), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"[gRPC] MS-5 Asistencias escuchando en puerto {port}")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()