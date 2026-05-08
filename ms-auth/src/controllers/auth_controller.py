from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from src.schemas.serializers import RegisterSerializer, UserSerializer
from src.utils.permissions import IsAdminRole, IsDocenteRole

# --- Registro de usuarios ---
class RegisterView(generics.CreateAPIView):
    """
    Endpoint público para crear una cuenta nueva.
    Cualquier persona puede registrarse inicialmente.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

# --- Inicio de sesión ---
class LoginView(TokenObtainPairView):
    """
    Autentica al usuario y devuelve tokens + información básica del perfil.
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            from src.models.models import User
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

# --- Perfil del usuario autenticado (Gestión de Perfil) ---
class MeView(generics.RetrieveUpdateAPIView):
    """
    GET: Devuelve los datos del usuario logueado.
    PATCH / PUT: Permite al usuario actualizar su propio nombre, email, etc.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        # Retorna el usuario asociado al token actual
        return self.request.user

    def patch(self, request, *args, **kwargs):
        """
        Validación extra: Evitar que un usuario se cambie el rol a sí mismo
        para escalar privilegios (ej. de Alumno a Admin).
        """
        if 'role' in request.data and not request.user.role == 'admin':
            return Response(
                {"error": "No tienes permisos para cambiar tu propio rol."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().partial_update(request, *args, **kwargs)

# --- Listado de usuarios (Solo admins) ---
class UserListView(generics.ListAPIView):
    """
    Devuelve todos los usuarios. Protegido por RBAC (IsAdminRole).
    """
    from src.models.models import User
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]