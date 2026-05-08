from django.contrib.auth.hashers import make_password, check_password
from rest_framework_simplejwt.tokens import RefreshToken

def get_password_hash(password: str) -> str:
    """
    Genera un hash seguro para la contraseña usando el backend de Django.
    Por defecto emplea PBKDF2 con SHA-256 y un salt aleatorio.
    """
    return make_password(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compara una contraseña en texto plano contra su hash almacenado.
    Django detecta automáticamente el algoritmo a partir del prefijo del hash.
    """
    return check_password(plain_password, hashed_password)

def create_access_token(user):
    """
    Genera un par de tokens JWT (refresh + access) para el usuario dado.
    Se agregan claims personalizados al payload para evitar consultas adicionales
    a la base de datos en cada petición protegida.
    """
    refresh = RefreshToken.for_user(user)
    # Claims extra que necesitan los demás microservicios para tomar decisiones de acceso.
    refresh['role'] = user.role
    refresh['email'] = user.email

    return str(refresh.access_token)