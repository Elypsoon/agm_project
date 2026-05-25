from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView
from rest_framework_simplejwt.views import TokenRefreshView
from src.controllers.auth_controller import (
    RegisterView,
    LoginView,
    MeView,
    UserListView,
    ChangePasswordView,
    RequestPasswordResetView,
    ConfirmPasswordResetView,
)

urlpatterns = [
    # POST /auth/register/ — Registro interno; password opcional (genera temporal si se omite).
    path('register/', RegisterView.as_view(), name='auth_register'),

    # POST /auth/login/ — Autenticación y emisión de tokens JWT.
    path('login/', LoginView.as_view(), name='auth_login'),

    # POST /auth/change-password/ — Cambio de contraseña temporal (primer login).
    path('change-password/', ChangePasswordView.as_view(), name='auth_change_password'),

    # GET /auth/me/ — Datos del usuario autenticado (cualquier rol).
    path('me/', MeView.as_view(), name='auth_me'),

    # POST /auth/token/refresh/ — Renueva el access token usando el refresh token.
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # GET /auth/users/ — Lista todos los usuarios (requiere rol admin).
    path('users/', UserListView.as_view(), name='user_list'),

    # POST /auth/logout/ — Invalida el refresh token (blacklist).
    path('logout/', TokenBlacklistView.as_view(), name='auth_logout'),

    # POST /auth/forgot-password/ — Envía correo de recuperación.
    path('forgot-password/', RequestPasswordResetView.as_view(), name='auth_forgot_password'),

    # POST /auth/reset-password/ — Establece nueva contraseña usando el token.
    path('reset-password/', ConfirmPasswordResetView.as_view(), name='auth_reset_password'),
]