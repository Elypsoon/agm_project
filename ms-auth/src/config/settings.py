import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# Raíz del proyecto; se usa como base para construir rutas absolutas.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Configuración de seguridad básica.
# SECRET_KEY debe sobreescribirse con un valor fuerte en producción.
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-clave-temporal")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]

# APLICACIONES
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Paquetes de terceros
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_yasg',  # Generador de documentación OpenAPI / Swagger

    # App que contiene el modelo User personalizado.
    'src.models.apps.ModelsConfig',

    'rest_framework_simplejwt.token_blacklist',
    'src',

]
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'src.config.urls'

# BASE DE DATOS
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv("DB_NAME"),
        'USER': os.getenv("DB_USER"),
        'PASSWORD': os.getenv("DB_PASSWORD"),
        'HOST': os.getenv("DB_HOST"),
        'PORT': os.getenv("DB_PORT"),
    }
}

# Modelo de usuario personalizado; 'models' corresponde al label definido en apps.py.
AUTH_USER_MODEL = 'models.User'

# DJANGO REST FRAMEWORK
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

# Configuración de tokens JWT.
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),   # El token de acceso expira en 1 hora.
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),      # El refresh token es válido por 7 días.
    'ROTATE_REFRESH_TOKENS': True,                    # Emite un nuevo refresh en cada uso.
    'BLACKLIST_AFTER_ROTATION': False,                # Activar si se instala 'token_blacklist'.
    'AUTH_HEADER_TYPES': ('Bearer',),
    'BLACKLIST_AFTER_ROTATION': True,
}

# INTERNACIONALIZACIÓN
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_URL = 'static/'

# Configuración de Swagger para autenticación con Bearer token.
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': False,  # Oculta el formulario de login por sesión en la UI de Swagger.
}