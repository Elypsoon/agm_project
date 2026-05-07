from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from src.controllers.auth_controller import (
    RegisterView, 
    LoginView, 
    MeView, 
    UserListView # <--- No olvides importar la nueva vista de prueba
)

urlpatterns = [
    # 1. Registro de usuarios (Abierto al público)
    # POST /auth/register/
    path('register/', RegisterView.as_view(), name='auth_register'),
    
    # 2. Inicio de sesión (Obtención de tokens)
    # POST /auth/login/
    path('login/', LoginView.as_view(), name='auth_login'),
    
    # 3. Datos del usuario actual (Requiere cualquier token válido)
    # GET /auth/me/
    path('me/', MeView.as_view(), name='auth_me'),
    
    # 4. Refresco de tokens (Usa el refresh_token para dar un nuevo access)
    # POST /auth/token/refresh/
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # 5. Gestión de usuarios (SOLO ADMINS - Prueba de RBAC)
    # GET /auth/users/
    path('users/', UserListView.as_view(), name='user_list'),
]