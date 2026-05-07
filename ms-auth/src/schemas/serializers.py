from rest_framework import serializers
from src.models.models import User

# Equivalente a UserResponse: Lo que enviamos al cliente
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'nombre', 'email', 'role', 'activo']

# Equivalente a UserCreate: Lo que recibimos para registrar
class RegisterSerializer(serializers.ModelSerializer):
    # Definimos el password como write_only para que no se incluya en respuestas
    password = serializers.CharField(
        write_only=True, 
        min_length=6, 
        style={'input_type': 'password'}
    )
    nombre = serializers.CharField(min_length=3, max_length=100)

    class Meta:
        model = User
        fields = ['nombre', 'email', 'password', 'role']

    def create(self, validated_data):
        # Usamos el método create_user que definimos en el modelo
        # para que el password se guarde con hash automáticamente
        return User.objects.create_user(**validated_data)

# Nota sobre LoginRequest: 
# Django SimpleJWT ya trae un serializer interno para el login (TokenObtainPairSerializer),
# por lo que no es estrictamente necesario crear uno manual, pero si quieres 
# personalizar la respuesta para que coincida con TokenResponse, haríamos esto:

class CustomTokenSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer() # Aquí anidamos el UserResponse que ya tenías