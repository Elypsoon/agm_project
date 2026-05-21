"""
MS-6: Notificaciones — Configuración Django.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Apuntar al archivo .env que está en la raíz de ms-notificaciones/
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
load_dotenv(ROOT_DIR / ".env")

# ---------------------------------------------------------------------------
# Seguridad
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-ms6-dev-key-change-in-prod")
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
        "NAME": os.getenv("DB_NAME", "agm_notificaciones_db"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "notificaciones_dev_2026"),
        "HOST": os.getenv("DB_HOST", "db-notificaciones"),
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
    # Si implementas validación de token vía gRPC como MS-3, lo agregas aquí:
    # "DEFAULT_AUTHENTICATION_CLASSES": (
    #     "src.utils.auth_backend.GrpcAuthentication",
    # ),
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
# Configuración de Correo (SMTP - Mailtrap)
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("SMTP_HOST")
EMAIL_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("SMTP_USER")
EMAIL_HOST_PASSWORD = os.getenv("SMTP_PASS")
DEFAULT_FROM_EMAIL = f"{os.getenv('SMTP_FROM_NAME', 'AGM')} <{os.getenv('SMTP_FROM_EMAIL', 'noreply@agm.buap.mx')}>"

# ---------------------------------------------------------------------------
# Puertos del microservicio
# ---------------------------------------------------------------------------
REST_PORT = int(os.getenv("REST_PORT", "3006"))
GRPC_PORT = int(os.getenv("GRPC_PORT", "50056"))

# ---------------------------------------------------------------------------
# Conexiones a otros microservicios (Clientes gRPC)
# ---------------------------------------------------------------------------
AUTH_GRPC_HOST = os.getenv("AUTH_GRPC_HOST", "ms-auth")
AUTH_GRPC_PORT = int(os.getenv("AUTH_GRPC_PORT", "50051"))
ALUMNOS_GRPC_HOST = os.getenv("ALUMNOS_GRPC_HOST", "ms-alumnos")
ALUMNOS_GRPC_PORT = int(os.getenv("ALUMNOS_GRPC_PORT", "50053"))
PERIODOS_GRPC_HOST = os.getenv("PERIODOS_GRPC_HOST", "ms-periodos")
PERIODOS_GRPC_PORT = int(os.getenv("PERIODOS_GRPC_PORT", "50052"))