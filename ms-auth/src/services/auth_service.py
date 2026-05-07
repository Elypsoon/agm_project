from django.core.exceptions import ValidationError
from rest_framework import exceptions
from src.models.models import User

class AuthService:
    
    @staticmethod
    def register_user(user_data):
        # 1. Verificar si el email existe
        if User.objects.filter(email=user_data['email']).exists():
            raise exceptions.ValidationError("El correo electrónico ya está registrado.")
        
        # 2. Crear el usuario (create_user ya hace el hash internamente)
        try:
            new_user = User.objects.create_user(
                email=user_data['email'],
                nombre=user_data['nombre'],
                password=user_data['password'],
                role=user_data.get('role', 'alumno')
            )
            return new_user
        except Exception as e:
            raise exceptions.APIException(f"Error al guardar: {str(e)}")

    @staticmethod
    def login_user(email, password):
        # 1. Buscar al usuario
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("Correo o contraseña incorrectos")

        # 2. Validar contraseña
        if not user.check_password(password):
            raise exceptions.AuthenticationFailed("Correo o contraseña incorrectos")

        # 3. Generar Token
        from src.utils.security import create_access_token
        return {
            "access_token": create_access_token(user),
            "token_type": "bearer",
            "user": user
        }