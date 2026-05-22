"""
ASGI config for MS-Periodos project.
Supports both HTTP (Django) and WebSocket if needed.
"""

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

application = get_asgi_application()
