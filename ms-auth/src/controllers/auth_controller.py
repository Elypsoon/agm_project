from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

# Importamos los serializadores (asegúrate de haberlos creado en serializers.py)
from src.schemas.serializers import (
    RegisterSerializer, 
    UserSerializer, 
    PasswordResetRequestSerializer, 
    PasswordResetConfirmSerializer
)
from src.utils.permissions import IsAdminRole, IsDocenteRole
from src.models.models import User

# --- Registro de usuarios ---
class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

# --- Inicio de sesión ---
class LoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            user = User.objects.get(email=request.data['email'])
            user_data = UserSerializer(user).data
            custom_data = {
                'access_token': response.data['access'],
                'refresh_token': response.data['refresh'],
                'token_type': 'bearer',
                'user': user_data
            }
            return Response(custom_data)
        return response

# --- Perfil del usuario autenticado ---
class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        if 'role' in request.data and not request.user.role == 'admin':
            return Response(
                {"error": "No tienes permisos para cambiar tu propio rol."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().partial_update(request, *args, **kwargs)

# --- Listado de usuarios (Solo admins) ---
class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

# --- NUEVO: Solicitar recuperación de contraseña ---
class RequestPasswordResetView(generics.GenericAPIView):
    """
    Recibe un email y envía un enlace de recuperación único a Mailtrap.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetRequestSerializer # Esto activa el cuadro en Swagger

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
                'Recuperación de Contraseña - AGM BUAP',
                f'Hola {user.nombre},\n\nHaz clic en el siguiente enlace para restablecer tu contraseña:\n{reset_url}',
                'admin@agm-buap.com',
                [user.email],
                fail_silently=False,
            )
            return Response({"message": "Si el correo existe, se ha enviado un enlace."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"message": "Si el correo existe, se ha enviado un enlace."}, status=status.HTTP_200_OK)

# --- NUEVO: Confirmar cambio de contraseña ---
class ConfirmPasswordResetView(generics.GenericAPIView):
    """
    Recibe el uid, el token y la nueva contraseña para aplicarla al usuario.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetConfirmSerializer # Esto activa el cuadro en Swagger

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
                user.save()
                return Response({"message": "Contraseña actualizada con éxito."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "El enlace es inválido o ha expirado."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "No se pudo procesar la solicitud."}, status=status.HTTP_400_BAD_REQUEST)