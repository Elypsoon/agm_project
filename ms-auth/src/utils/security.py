from django.contrib.auth.hashers import make_password, check_password
from rest_framework_simplejwt.tokens import RefreshToken

def get_password_hash(password: str) -> str:
    """Usa el sistema nativo de Django (PBKDF2 por defecto, muy seguro)"""
    return make_password(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica la contraseña usando el algoritmo detectado en el hash"""
    return check_password(plain_password, hashed_password)

def create_access_token(user):
    """SimpleJWT genera el token directamente desde el objeto usuario"""
    refresh = RefreshToken.for_user(user)
    # Podemos agregar claims personalizados (como el rol) al token
    refresh['role'] = user.role
    refresh['email'] = user.email
    
    return str(refresh.access_token)