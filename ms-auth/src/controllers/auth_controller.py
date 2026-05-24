import logging
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings

from src.schemas.serializers import (
    RegisterSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from src.utils.permissions import IsAdminRole, IsDocenteRole
from src.models.models import User

logger = logging.getLogger(__name__)


def _send_welcome_email(user: User, temp_password: str | None) -> None:
    """Envía el correo de bienvenida con la contraseña temporal (si aplica)."""
    login_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:4200') + '/auth/login'

    if temp_password:
        password_section = f"""
        <div style="background:#f0f4ff;border-left:4px solid #4f46e5;padding:16px 20px;border-radius:6px;margin:24px 0;">
            <p style="margin:0 0 8px;font-size:13px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;">Tu contraseña temporal</p>
            <p style="margin:0;font-size:22px;font-weight:700;font-family:monospace;color:#1e1b4b;letter-spacing:.1em;">{temp_password}</p>
            <p style="margin:8px 0 0;font-size:12px;color:#ef4444;">⚠️ Deberás cambiarla en tu primer inicio de sesión.</p>
        </div>"""
    else:
        password_section = "<p>Utiliza la contraseña que te fue asignada por el administrador.</p>"

    html_message = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#f8fafc;font-family:'Segoe UI',Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr><td align="center" style="padding:40px 16px;">
          <table width="600" cellpadding="0" cellspacing="0"
                 style="background:#ffffff;border-radius:12px;overflow:hidden;
                        box-shadow:0 4px 24px rgba(0,0,0,.08);">
            <tr>
              <td style="background:linear-gradient(135deg,#4f46e5 0%,#7c3aed 100%);
                         padding:36px 40px;text-align:center;">
                <h1 style="margin:0;color:#fff;font-size:28px;font-weight:700;
                           letter-spacing:-.5px;">🎓 AGM</h1>
                <p style="margin:6px 0 0;color:#c7d2fe;font-size:14px;">
                  Sistema de Gestión Académica
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:36px 40px;">
                <p style="margin:0 0 16px;font-size:16px;color:#374151;">
                  Hola, <strong>{user.nombre}</strong>:
                </p>
                <p style="margin:0 0 16px;font-size:15px;color:#6b7280;line-height:1.6;">
                  Tu cuenta en el sistema <strong>AGM</strong> ha sido creada exitosamente
                  con el rol de <strong>{user.get_role_display()}</strong>.
                </p>
                {password_section}
                <a href="{login_url}"
                   style="display:inline-block;background:linear-gradient(135deg,#4f46e5,#7c3aed);
                          color:#fff;text-decoration:none;padding:14px 32px;border-radius:8px;
                          font-weight:600;font-size:15px;margin-top:8px;">
                  Iniciar Sesión →
                </a>
                <p style="margin:28px 0 0;font-size:13px;color:#9ca3af;line-height:1.5;">
                  Si no reconoces este registro, puedes ignorar este correo con seguridad.<br>
                  Este mensaje fue generado automáticamente por el sistema AGM.
                </p>
              </td>
            </tr>
            <tr>
              <td style="background:#f9fafb;padding:20px 40px;text-align:center;
                         border-top:1px solid #e5e7eb;">
                <p style="margin:0;font-size:12px;color:#9ca3af;">
                  © 2026 AGM
                </p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>"""

    plain_message = (
        f"Hola {user.nombre},\n\n"
        f"Tu cuenta AGM ha sido creada (rol: {user.get_role_display()}).\n"
        + (f"Contraseña temporal: {temp_password}\nDeberás cambiarla en tu primer inicio de sesión.\n" if temp_password else "")
        + f"\nAccede en: {login_url}\n\n"
        "Si no reconoces este registro, ignora este correo."
    )

    try:
        send_mail(
            subject='Bienvenido/a al Sistema AGM 🎓',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info("Correo de bienvenida enviado a %s", user.email)
    except Exception as exc:
        logger.error("Error al enviar correo de bienvenida a %s: %s", user.email, exc)


class RegisterView(generics.CreateAPIView):
    """
    Registra un nuevo usuario.
    Si no se envía `password`, se genera una contraseña temporal y se notifica por correo.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        temp_password = getattr(user, '_temp_password', None)
        _send_welcome_email(user, temp_password)

        return Response(
            {
                "message": "Usuario creado exitosamente. Se ha enviado un correo de bienvenida.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """
    Autentica al usuario y retorna los tokens JWT.
    Incluye `requires_password_change` para que el frontend fuerce el cambio de contraseña si es necesario.
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            user = User.objects.get(email=request.data['email'])
            return Response({
                'access_token': response.data['access'],
                'refresh_token': response.data['refresh'],
                'token_type': 'bearer',
                'requires_password_change': user.requires_password_change,
                'user': UserSerializer(user).data,
            })
        return response


class ChangePasswordView(APIView):
    """
    Permite cambiar la contraseña temporal. Marca `requires_password_change = False` al completar.
    Requiere autenticación JWT.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {"error": "La contraseña actual es incorrecta."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data['new_password'])
        user.requires_password_change = False
        user.save()
        return Response(
            {"message": "Contraseña actualizada exitosamente."},
            status=status.HTTP_200_OK,
        )


class MeView(generics.RetrieveUpdateAPIView):
    """Retorna o actualiza el perfil del usuario autenticado."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        if 'role' in request.data and request.user.role != 'admin':
            return Response(
                {"error": "No tienes permisos para cambiar tu propio rol."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().partial_update(request, *args, **kwargs)


class UserListView(generics.ListAPIView):
    """Lista todos los usuarios del sistema. Solo accesible para administradores."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]


class RequestPasswordResetView(generics.GenericAPIView):
    """Genera y envía un enlace de recuperación de contraseña al correo indicado."""
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"http://localhost:4200/auth/reset-password/{uid}/{token}/"

            send_mail(
                'Recuperación de Contraseña - AGM',
                f'Hola {user.nombre},\n\nHaz clic en el siguiente enlace para restablecer tu contraseña:\n{reset_url}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except User.DoesNotExist:
            pass  # Respuesta ambigua para no revelar si el correo existe

        return Response(
            {"message": "Si el correo existe, se ha enviado un enlace de recuperación."},
            status=status.HTTP_200_OK,
        )


class ConfirmPasswordResetView(generics.GenericAPIView):
    """Valida el token de recuperación y aplica la nueva contraseña."""
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uidb64 = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)

            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.requires_password_change = False
                user.save()
                return Response(
                    {"message": "Contraseña actualizada con éxito."},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": "El enlace es inválido o ha expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {"error": "No se pudo procesar la solicitud."},
                status=status.HTTP_400_BAD_REQUEST,
            )