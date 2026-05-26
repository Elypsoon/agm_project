import os
import logging
import threading
from concurrent import futures

import grpc

logger = logging.getLogger(__name__)


def _ensure_django():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.config.settings')
    import django
    django.setup()


def crear_servidor_grpc(port):
    from src.grpc import calificaciones_pb2_grpc
    from src.grpc.handlers.calificaciones_handler import CalificacionesServicer

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    calificaciones_pb2_grpc.add_CalificacionesServiceServicer_to_server(
        CalificacionesServicer(), server
    )
    server.add_insecure_port(f'0.0.0.0:{port}')
    return server


def start_grpc_in_background(port=None):
    """Arranca el servidor gRPC en un hilo daemon del proceso actual."""
    if port is None:
        port = int(os.getenv('GRPC_PORT', 50054))

    server = crear_servidor_grpc(port)
    server.start()
    logger.info('[gRPC] Servidor de calificaciones iniciado en :%s', port)

    hilo = threading.Thread(
        target=server.wait_for_termination,
        name='grpc-server',
        daemon=True,
    )
    hilo.start()
    return server


if __name__ == '__main__':
    # Ejecución directa para desarrollo sin Gunicorn.
    _ensure_django()

    port = int(os.getenv('GRPC_PORT', 50054))
    server = crear_servidor_grpc(port)
    server.start()
    logger.info('[gRPC] Servidor escuchando en :%s (modo standalone)', port)
    print(f'[gRPC] Servidor escuchando en puerto {port}')
    server.wait_for_termination()
