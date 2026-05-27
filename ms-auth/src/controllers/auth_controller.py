import logging
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings

from src.utils.rabbitmq import publish_event

from src.schemas.serializers import (
    RegisterSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from src.utils.permissions import IsAdminRole, IsDocenteRole, IsAdminOrDocenteRole
from src.models.models import User

logger = logging.getLogger(__name__)


def _send_welcome_email(user: User, temp_password: str | None) -> None:
    """Publica el evento de bienvenida en el broker para que ms-notificaciones envíe el correo."""
    payload = {
        "email": user.email,
        "nombre_alumno": user.nombre,
        "clave_temporal": temp_password,
    }
    try:
        success = publish_event('student.registered', payload)
        if success:
            logger.info("Evento 'student.registered' encolado para %s", user.email)
        else:
            logger.error("Fallo al encolar evento 'student.registered' para %s", user.email)
    except Exception as exc:
        logger.error("Error inesperado al encolar evento de bienvenida para %s: %s", user.email, exc)


class RegisterView(generics.CreateAPIView):
    """
    Registra un nuevo usuario.
    Si no se envía `password`, se genera una contraseña temporal y se notifica por correo.

    SECURITY (VULN-05): Solo los administradores autenticados pueden crear cuentas.
    El registro no es un flujo público; los alumnos y docentes son dados de alta por el Admin.
    """
    # SECURITY (VULN-05): Requiere autenticación + rol admin o docente.
    permission_classes = [permissions.IsAuthenticated, IsAdminOrDocenteRole]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        from rest_framework.exceptions import PermissionDenied
        
        role_solicitado = request.data.get('role', 'alumno')
        
        # Lógica de negocio de jerarquía:
        # Si el usuario actual es docente, solo puede registrar alumnos.
        if request.user.role == 'docente' and role_solicitado != 'alumno':
            raise PermissionDenied("Los docentes solo pueden registrar alumnos.")

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
            email = request.data.get('email')
            if email:
                user = User.objects.get(email=email)
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
    Solo accesible si el usuario tiene un cambio de contraseña pendiente.
    Requiere autenticación JWT.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        # SECURITY (VULN-06): Bloquear el acceso si el usuario NO tiene cambio pendiente.
        # Evita que un token robado sea usado para cambiar contraseñas arbitrariamente.
        if not request.user.requires_password_change:
            return Response(
                {"error": "No tienes un cambio de contraseña pendiente."},
                status=status.HTTP_403_FORBIDDEN,
            )

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
            reset_url = (
                getattr(settings, 'FRONTEND_URL', 'http://localhost:4200')
                + f'/auth/reset-password/{uid}/{token}/'
            )
            payload = {
                "email": user.email,
                "reset_url": reset_url,
            }
            success = publish_event('usuario.reset', payload)
            if success:
                logger.info("Evento 'usuario.reset' encolado para %s", user.email)
            else:
                logger.error("Fallo al encolar evento 'usuario.reset' para %s", user.email)
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
        # SECURITY (VULN-08): Captura excepciones específicas en lugar de Exception genérico.
        # El mensaje al cliente es siempre genérico; el detalle solo queda en los logs internos.
        except (ValueError, TypeError):
            logger.warning("[VULN-08] UID malformado en reset de contraseña. uid_raw='%s'", uidb64)
            return Response(
                {"error": "El enlace es inválido o ha expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except User.DoesNotExist:
            logger.warning("[VULN-08] Reset con UID sin usuario asociado. uid_raw='%s'", uidb64)
            return Response(
                {"error": "El enlace es inválido o ha expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.exception("[VULN-08] Error inesperado en ConfirmPasswordResetView: %s", exc)
            return Response(
                {"error": "No se pudo procesar la solicitud."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )