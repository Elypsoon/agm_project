from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuración del Generador de Documentación
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
   # Esto permite que la documentación cargue sin necesidad de token previo
   authentication_classes=[], 
)

urlpatterns = [
    # Panel de Administración de Django
    path('admin/', admin.site.urls),
    
    # Rutas del Microservicio de Autenticación
    # Django buscará los endpoints definidos en src/routes/auth_routes.py
    path('auth/', include('src.routes.auth_routes')), 
    
    # Documentación Interactiva (Swagger UI)
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    
    # Documentación Alternativa (ReDoc) - Similar a la que usa FastAPI
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]