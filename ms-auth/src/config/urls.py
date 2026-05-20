from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from src.controllers.auth_controller import RequestPasswordResetView, ConfirmPasswordResetView

# Configuración del esquema OpenAPI expuesto por drf_yasg.
schema_view = get_schema_view(
   openapi.Info(
      title="AGM - Auth Service",
      default_version='v1.0.0',
      description="Microservicio de Autenticación y Gestión de Usuarios - Proyecto AGM",
      contact=openapi.Contact(email="tu-correo@alumno.buap.mx"),
      license=openapi.License(name="MIT License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
   authentication_classes=[],  # Sin autenticación previa para acceder a los docs.
)

urlpatterns = [
    # Panel de administración de Django.
    path('admin/', admin.site.urls),

    # Endpoints del microservicio de autenticación (definidos en src/routes/auth_routes.py).
    path('auth/', include('src.routes.auth_routes')),

    # Documentación interactiva Swagger UI.
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    # Documentación alternativa en formato ReDoc.
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('password-reset/', RequestPasswordResetView.as_view(), name='password_reset'),

    path('password-reset-confirm/', ConfirmPasswordResetView.as_view(), name='password_reset_confirm'),
]