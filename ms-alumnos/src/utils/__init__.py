"""
Utilidades — Generación de claves únicas de acceso para alumnos.
"""

import secrets
import string


def generar_clave_acceso(longitud: int = 10) -> str:
    """
    Genera una clave de acceso alfanumérica segura.

    Args:
        longitud: número de caracteres de la clave.

    Returns:
        Clave alfanumérica aleatoria (ej: "aX4kMn9pQr").
    """
    alfabeto = string.ascii_letters + string.digits
    return "".join(secrets.choice(alfabeto) for _ in range(longitud))
