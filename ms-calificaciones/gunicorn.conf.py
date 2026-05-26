import os


def when_ready(server):
    """Hook invocado cuando el master de Gunicorn está listo."""
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.config.settings')
    django.setup()

    from src.grpc.server import start_grpc_in_background
    grpc_port = int(os.getenv('GRPC_PORT', 50054))
    start_grpc_in_background(grpc_port)
    server.log.info('[gRPC] Servidor arrancado en :%s desde when_ready', grpc_port)


def worker_exit(server, worker):
    """Hook invocado cuando un worker termina.

    Cierra las conexiones de base de datos del worker para evitar
    que descriptores de fichero queden abiertos innecesariamente.
    """
    from django.db import connections
    connections.close_all()
