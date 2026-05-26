import os
import sys
import logging
import threading

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class ModelsConfig(AppConfig):
    """Configuración de la aplicación Django 'models'.

    Contiene la inicialización del ciclo de vida de la aplicación, incluyendo el arranque
    del servidor gRPC integrado cuando Django se ejecuta a través del comando 'runserver' 
    en modo local.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.models"
    label = "models"
    verbose_name = "MS-4 Calificaciones y Ponderaciones"

    def ready(self):
        """Hook del ciclo de vida de Django que se ejecuta al iniciar la aplicación.

        Inicia el servidor gRPC en un hilo secundario para no bloquear el hilo
        principal del servidor web Django en entornos locales.
        """
        if not self._should_start_grpc():
            return
        # Levantar gRPC en un hilo daemon
        threading.Thread(target=self._start_grpc, daemon=True).start()

    def _should_start_grpc(self):
        """Determina si las condiciones del entorno requieren levantar el servidor gRPC.

        Evita que se duplique el arranque del servidor gRPC en subprocesos reloaders
        de Django y que intente iniciarse durante la ejecución de migraciones u otros comandos.

        Returns:
            bool: True si se debe arrancar gRPC, False en caso contrario.
        """
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
        """Instancia e inicia el servidor gRPC de Calificaciones.

        Consulta la configuración del puerto desde los settings del proyecto e inicia la
        escucha de sockets.
        """
        from django.conf import settings
        from src.grpc.server import crear_servidor_grpc

        try:
            port = getattr(settings, 'GRPC_PORT', 50054)
            server = crear_servidor_grpc(port)
            server.start()
            print(f"[gRPC] Servidor escuchando en puerto {port}")
        except Exception as e:
            print(f"[gRPC] Error al iniciar gRPC en ready(): {e}")

