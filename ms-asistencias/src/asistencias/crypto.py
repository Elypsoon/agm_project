"""
Módulo de cifrado para tokens QR dinámicos.

El alumno genera un QR que contiene un token cifrado con la siguiente estructura:
    {alumno_id}:{matricula}:{timestamp}

El token se cifra con AES-128 (Fernet) usando QR_SECRET_KEY.
El token cambia cada 30 segundos (el frontend lo regenera), lo que
previene capturas y uso fraudulento (anti-replay).

En el backend se valida:
1. Que el token pueda descifrarse correctamente.
2. Que el timestamp no sea mayor a QR_MAX_AGE_SECONDS (60 s por defecto).
3. Que el hash del token no exista ya en la tabla asistencias (anti-replay).
"""

import hashlib
import time
from cryptography.fernet import Fernet, InvalidToken
from decouple import config

_RAW_KEY = config('QR_SECRET_KEY', default='')
QR_MAX_AGE_SECONDS = int(config('QR_MAX_AGE_SECONDS', default=60))


def _get_fernet() -> Fernet:
    if not _RAW_KEY:
        raise RuntimeError("QR_SECRET_KEY no está configurada en las variables de entorno.")
    return Fernet(_RAW_KEY.encode() if isinstance(_RAW_KEY, str) else _RAW_KEY)


def encrypt_qr_payload(alumno_id: str, matricula: str) -> str:
    """
    Genera el token cifrado que el alumno mostrará en su QR.
    Formato del payload: alumno_id:matricula:timestamp
    """
    timestamp = int(time.time())
    payload = f"{alumno_id}:{matricula}:{timestamp}"
    f = _get_fernet()
    token = f.encrypt(payload.encode()).decode()
    return token


def decrypt_qr_token(token: str) -> dict:
    """
    Descifra y valida un token QR.
    Retorna un diccionario con los campos o lanza una excepción descriptiva.
    """
    f = _get_fernet()
    try:
        payload = f.decrypt(token.encode()).decode()
    except InvalidToken:
        raise ValueError("Token QR inválido o corrupto.")

    parts = payload.split(':')
    if len(parts) != 3:
        raise ValueError("Formato de token QR incorrecto.")

    alumno_id, matricula, timestamp_str = parts
    timestamp = int(timestamp_str)
    age = int(time.time()) - timestamp

    if age > QR_MAX_AGE_SECONDS:
        raise ValueError(f"Token QR expirado (generado hace {age} segundos, máximo {QR_MAX_AGE_SECONDS}s).")

    return {
        'alumno_id': alumno_id,
        'matricula': matricula,
        'timestamp': timestamp,
    }


def hash_token(token: str) -> str:
    """
    Genera un hash SHA-256 del token para almacenarlo en la BD
    y detectar intentos de reutilización (anti-replay).
    """
    return hashlib.sha256(token.encode()).hexdigest()