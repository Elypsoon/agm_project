from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuración de la documentación Swagger para MS-6
schema_view = get_schema_view(
    openapi.Info(
        title="MS-6: Notificaciones API",
        default_version='v1',
        description="Documentación de la API REST externa para el servicio de Notificaciones de AGM",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="soporte@agm.buap.mx"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Incluimos el archivo central de rutas del microservicio
    path('notificaciones/', include('src.routes.api')),
    
    # Endpoints para la documentación interactiva en el navegador
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]