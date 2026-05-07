#!/usr/bin/env python
import os
import sys

def main():
    """Ejecuta tareas administrativas del microservicio."""
    # Le decimos a Django dónde está nuestro archivo de configuración
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. ¿Está instalado en tu PYTHONPATH?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()