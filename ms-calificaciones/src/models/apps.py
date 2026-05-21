import os
import sys
import logging
import threading

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class ModelsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.models"
    label = "models"
    verbose_name = "MS-4 Calificaciones y Ponderaciones"

    def ready(self):
        """Iniciar el servidor gRPC al arrancar Django."""
        if not self._should_start_grpc():
            return
        # Levantar gRPC en un hilo daemon
        threading.Thread(target=self._start_grpc, daemon=True).start()

    def _should_start_grpc(self):
        argv = sys.argv
        if len(argv) < 2:
            return False
        command = argv[1]
        if command != "runserver":
            return False
        if os.environ.get("RUN_MAIN") != "true":
            return False
        return True

    def _start_grpc(self):
        from django.conf import settings
        from src.grpc.server import crear_servidor_grpc

        try:
            port = getattr(settings, 'GRPC_PORT', 50054)
            server = crear_servidor_grpc(port)
            server.start()
            print(f"[gRPC] Servidor escuchando en puerto {port}")
        except Exception as e:
            print(f"[gRPC] Error al iniciar gRPC en ready(): {e}")
