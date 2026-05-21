import os
import logging
from concurrent import futures
import grpc

logger = logging.getLogger(__name__)

def _ensure_django():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'calificaciones_project.settings')
    import django
    django.setup()

def crear_servidor_grpc(port: int) -> grpc.Server:
    from apps.grpc_server import calificaciones_pb2_grpc
    from apps.grpc_server.handlers.calificaciones_handler import CalificacionesServicer

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    calificaciones_pb2_grpc.add_CalificacionesServiceServicer_to_server(
        CalificacionesServicer(), server
    )
    server.add_insecure_port(f'0.0.0.0:{port}')
    return server

if __name__ == '__main__':
    import sys
    _ensure_django()

    port = int(os.getenv('GRPC_PORT', 50054))
    server = crear_servidor_grpc(port)
    server.start()
    logger.info(f'Servidor gRPC iniciado en :{port}')
    server.wait_for_termination()
