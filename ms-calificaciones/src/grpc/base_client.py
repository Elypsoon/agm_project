from django.conf import settings

class BaseGRPCClient:
    """Clase base para todos los clientes gRPC del microservicio.

    Proporciona soporte para cambiar entre el modo simulado en memoria y el
    modo real (conexiones de sockets TCP gRPC activas) basado en los settings 
    del proyecto Django (GRPC_MOCK_MODE).
    """
    def __init__(self):
        """Inicializa el cliente gRPC evaluando el modo de simulación configurado."""
        self.mock_mode = getattr(settings, 'GRPC_MOCK_MODE', True)

