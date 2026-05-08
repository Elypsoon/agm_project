"""
MS-3: Docentes & Alumnos — Configuración Django.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Seguridad
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-ms3-dev-key-change-in-prod")
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
    "src.models.apps.ModelsConfig",
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

ROOT_URLCONF = "src.config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "src.config.wsgi.application"

# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "agm_alumnos_db"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "alumnos_dev_2026"),
        "HOST": os.getenv("DB_HOST", "db-alumnos"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
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
# Archivos estáticos (para admin)
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Puertos del microservicio
# ---------------------------------------------------------------------------
REST_PORT = int(os.getenv("REST_PORT", "3003"))
GRPC_PORT = int(os.getenv("GRPC_PORT", "50053"))

# ---------------------------------------------------------------------------
# Conexiones a otros microservicios
# ---------------------------------------------------------------------------
AUTH_GRPC_HOST = os.getenv("AUTH_GRPC_HOST", "ms-auth")
AUTH_GRPC_PORT = int(os.getenv("AUTH_GRPC_PORT", "50051"))
NOTIFICACIONES_GRPC_HOST = os.getenv("NOTIFICACIONES_GRPC_HOST", "ms-notificaciones")
NOTIFICACIONES_GRPC_PORT = int(os.getenv("NOTIFICACIONES_GRPC_PORT", "50056"))
PERIODOS_GRPC_HOST = os.getenv("PERIODOS_GRPC_HOST", "ms-periodos")
PERIODOS_GRPC_PORT = int(os.getenv("PERIODOS_GRPC_PORT", "50052"))

# ---------------------------------------------------------------------------
# Swagger (drf-yasg)
# ---------------------------------------------------------------------------
SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {},
    "USE_SESSION_AUTH": False,
}
