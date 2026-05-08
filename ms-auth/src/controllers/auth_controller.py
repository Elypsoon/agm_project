from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from src.schemas.serializers import RegisterSerializer, UserSerializer
from src.utils.permissions import IsAdminRole, IsDocenteRole

# --- Registro de usuarios ---
class RegisterView(generics.CreateAPIView):
    """
    Endpoint público para crear una cuenta nueva.
    La validación del cuerpo de la solicitud y el hash de la contraseña
    se delegan al RegisterSerializer.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

# --- Inicio de sesión ---
class LoginView(TokenObtainPairView):
    """
    Extiende TokenObtainPairView para enriquecer la respuesta con los datos
    del usuario, además del par de tokens que SimpleJWT ya devuelve.
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            from src.models.models import User
            # Recuperamos el usuario para incluir su información en la respuesta.
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
class MeView(generics.RetrieveAPIView):
    """
    Devuelve los datos del usuario propietario del token.
    Cualquier rol puede acceder siempre que el token sea válido.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

# --- Listado de usuarios (solo admins) ---
class UserListView(generics.ListAPIView):
    """
    Devuelve todos los usuarios registrados en el sistema.
    Requiere rol 'admin'; cualquier otro rol recibirá un 403.
    """
    from src.models.models import User
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]