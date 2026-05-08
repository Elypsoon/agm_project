from rest_framework import serializers
from src.models.models import User

# Representa los datos del usuario que se exponen al cliente.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'nombre', 'email', 'role', 'activo']

# Valida y deserializa el cuerpo de una solicitud de registro.
class RegisterSerializer(serializers.ModelSerializer):
    # write_only garantiza que la contraseña nunca aparezca en ninguna respuesta.
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
        # Delegamos la creación a create_user para que el hash se aplique correctamente.
        return User.objects.create_user(**validated_data)

# Serializer auxiliar que representa la respuesta completa del login:
# combina los tokens de SimpleJWT con los datos del usuario.
class CustomTokenSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()