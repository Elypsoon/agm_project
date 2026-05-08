from django.core.exceptions import ValidationError
from rest_framework import exceptions
from src.models.models import User

class AuthService:
    
    @staticmethod
    def register_user(user_data):
        # Verificar unicidad del correo antes de intentar insertar.
        if User.objects.filter(email=user_data['email']).exists():
            raise exceptions.ValidationError("El correo electrónico ya está registrado.")

        # create_user aplica el hash a la contraseña internamente.
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
        # Buscar el registro por correo; el mensaje de error es intencional
        # para no revelar si el correo existe o no.
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("Correo o contraseña incorrectos")

        # Verificar la contraseña usando el método nativo de Django.
        if not user.check_password(password):
            raise exceptions.AuthenticationFailed("Correo o contraseña incorrectos")

        # Emitir el token con los claims necesarios para los demás microservicios.
        from src.utils.security import create_access_token
        return {
            "access_token": create_access_token(user),
            "token_type": "bearer",
            "user": user
        }