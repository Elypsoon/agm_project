from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from src.schemas.serializers import RegisterSerializer, UserSerializer
from src.utils.permissions import IsAdminRole, IsDocenteRole # Importamos tus nuevos permisos

# 1. Registro de Usuario
class RegisterView(generics.CreateAPIView):
    """
    Crea un usuario en la base de datos. 
    Por defecto, cualquier persona puede registrarse (AllowAny).
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

# 2. Login Personalizado
class LoginView(TokenObtainPairView):
    """
    Autentica y devuelve access_token, refresh_token e info del usuario.
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            from src.models.models import User
            # Buscamos al usuario para devolver su info completa
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

# 3. Perfil del Usuario Autenticado (/auth/me)
class MeView(generics.RetrieveAPIView):
    """
    Retorna los datos del usuario dueño del token.
    Funciona para cualquier rol siempre que esté autenticado.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

# 4. LISTA DE USUARIOS (Solo para Admins - RBAC en acción)
class UserListView(generics.ListAPIView):
    """
    Muestra todos los usuarios registrados.
    BLINDAJE: Solo usuarios con role == 'admin' pueden entrar.
    """
    from src.models.models import User
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # Aquí aplicamos el permiso personalizado que creaste
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]