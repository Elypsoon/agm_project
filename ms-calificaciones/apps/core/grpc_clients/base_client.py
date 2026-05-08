from django.conf import settings

class BaseGRPCClient:
    def __init__(self):
        self.mock_mode = getattr(settings, 'GRPC_MOCK_MODE', True)