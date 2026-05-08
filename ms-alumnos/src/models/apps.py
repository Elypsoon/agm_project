"""Configuración de la app 'models' del MS-3."""

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
    verbose_name = "MS-3 Docentes & Alumnos"

    def ready(self):
        """Iniciar el servidor gRPC al arrancar Django."""
        # Solo iniciar durante `runserver`, no en migrate/shell/test
        if not self._should_start_grpc():
            return
        # Iniciar en hilo daemon para no bloquear
        threading.Thread(target=self._start_grpc, daemon=True).start()

    def _should_start_grpc(self):
        """Determinar si debemos iniciar el servidor gRPC."""
        argv = sys.argv
        # Verificar si es runserver
        if len(argv) < 2:
            return False
        command = argv[1]
        if command != "runserver":
            return False
        # Con auto-reload, Django ejecuta ready() dos veces:
        # una en el watcher y otra en el child. Solo iniciar en el child.
        if os.environ.get("RUN_MAIN") != "true":
            return False
        return True

    def _start_grpc(self):
        from django.conf import settings
        from src.grpc.server import crear_servidor_grpc

        try:
            server = crear_servidor_grpc(settings.GRPC_PORT)
            server.start()
            print(f"[gRPC] Servidor escuchando en puerto {settings.GRPC_PORT}")
        except Exception as e:
            print(f"[gRPC] Error al iniciar: {e}")
