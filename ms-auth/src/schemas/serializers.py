from rest_framework import serializers
from src.models.models import User

# Representa los datos del usuario que se exponen al cliente.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'nombre', 'email', 'role', 'activo']
        # Protegemos campos para que no se puedan editar por accidente
        read_only_fields = ['id', 'role', 'activo']

# Valida y deserializa el cuerpo de una solicitud de registro.
class RegisterSerializer(serializers.ModelSerializer):
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
        return User.objects.create_user(**validated_data)

# Serializer para la respuesta del login
class CustomTokenSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()

# Serializer para pedir el correo
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

# Serializer para confirmar la nueva clave
class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=6)