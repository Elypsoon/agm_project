import secrets
import string
from rest_framework import serializers
from src.models.models import User


def generate_temp_password(length: int = 12) -> str:
    """Genera una contraseña temporal segura con al menos una mayúscula, minúscula, dígito y símbolo."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    required = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice('!@#$%^&*'),
    ]
    rest = [secrets.choice(alphabet) for _ in range(length - len(required))]
    combined = required + rest
    secrets.SystemRandom().shuffle(combined)
    return ''.join(combined)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'nombre', 'email', 'role', 'activo', 'requires_password_change']
        read_only_fields = ['id', 'role', 'activo', 'requires_password_change']


class RegisterSerializer(serializers.ModelSerializer):
    # La contraseña es opcional; si se omite se genera una temporal automáticamente.
    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=6,
        allow_blank=False,
        style={'input_type': 'password'},
        help_text="Opcional. Si se omite, se genera una contraseña temporal segura."
    )
    nombre = serializers.CharField(min_length=3, max_length=100)

    class Meta:
        model = User
        fields = ['nombre', 'email', 'password', 'role']
        # SECURITY: La seguridad sobre quién puede asignar qué roles 
        # (VULN-05) ahora se maneja en el controlador (RegisterView).

    def create(self, validated_data):
        temp_password = None
        if not validated_data.get('password'):
            temp_password = generate_temp_password()
            validated_data['password'] = temp_password

        user = User.objects.create_user(**validated_data)
        user._temp_password = temp_password  # Solo en memoria, para el correo de bienvenida
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Valida el cambio de contraseña temporal en el primer inicio de sesión."""
    old_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Contraseña temporal recibida por correo."
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text="Nueva contraseña definitiva (mínimo 8 caracteres)."
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError("Las contraseñas nuevas no coinciden.")
        return data


class CustomTokenSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=6)