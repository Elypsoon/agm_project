import os


# Servidor gRPC iniciado como proceso independiente en entrypoint.sh


def worker_exit(server, worker):
    """Hook invocado cuando un worker termina.

    Cierra las conexiones de base de datos del worker para evitar
    que descriptores de fichero queden abiertos innecesariamente.
    """
    from django.db import connections
    connections.close_all()
