"""
MS-7: Reportes & Estadísticas — Configuración Django.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Apuntar al archivo .env que está en la raíz de ms-reportes/
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
load_dotenv(ROOT_DIR / ".env")

# ---------------------------------------------------------------------------
# Seguridad
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-ms7-dev-key-change-in-prod")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]

# ---------------------------------------------------------------------------
# Aplicaciones
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceros
    "rest_framework",
    "corsheaders",
    "drf_yasg",
    # App local
    "src",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "src.core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "src.core.wsgi.application"

# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "agm_reportes_db"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "reportes_dev_2026"),
        "HOST": os.getenv("DB_HOST", "db-reportes"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    os.getenv("CORS_ORIGIN", "http://localhost:4200"),
]

# ---------------------------------------------------------------------------
# Internacionalización
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Archivos estáticos
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Puertos e Interfaces gRPC
# ---------------------------------------------------------------------------
REST_PORT = int(os.getenv("REST_PORT", "3007"))
GRPC_PORT = int(os.getenv("GRPC_PORT", "50057"))

AUTH_GRPC_HOST = os.getenv("AUTH_GRPC_HOST", "ms-auth")
AUTH_GRPC_PORT = int(os.getenv("AUTH_GRPC_PORT", "50051"))
ALUMNOS_GRPC_HOST = os.getenv("ALUMNOS_GRPC_HOST", "ms-alumnos")
ALUMNOS_GRPC_PORT = int(os.getenv("ALUMNOS_GRPC_PORT", "50053"))
CALIFICACIONES_GRPC_HOST = os.getenv("CALIFICACIONES_GRPC_HOST", "ms-calificaciones")
CALIFICACIONES_GRPC_PORT = int(os.getenv("CALIFICACIONES_GRPC_PORT", "50054"))
ASISTENCIAS_GRPC_HOST = os.getenv("ASISTENCIAS_GRPC_HOST", "ms-asistencias")
ASISTENCIAS_GRPC_PORT = int(os.getenv("ASISTENCIAS_GRPC_PORT", "50055"))