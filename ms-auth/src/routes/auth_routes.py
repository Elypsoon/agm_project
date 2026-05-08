from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView
from rest_framework_simplejwt.views import TokenRefreshView
from src.controllers.auth_controller import (
    RegisterView,
    LoginView,
    MeView,
    UserListView
)

urlpatterns = [
    # POST /auth/register/ — Registro público de nuevas cuentas.
    path('register/', RegisterView.as_view(), name='auth_register'),

    # POST /auth/login/ — Autenticación y emisión de tokens.
    path('login/', LoginView.as_view(), name='auth_login'),

    # GET /auth/me/ — Datos del usuario autenticado (cualquier rol).
    path('me/', MeView.as_view(), name='auth_me'),

    # POST /auth/token/refresh/ — Renueva el access token usando el refresh token.
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # GET /auth/users/ — Lista todos los usuarios (requiere rol admin).
    path('users/', UserListView.as_view(), name='user_list'),

    path('logout/', TokenBlacklistView.as_view(), name='auth_logout'),
]