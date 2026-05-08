"""
Modelos de datos — exporta Base y todos los modelos.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Clase base de la que heredan todos los modelos del MS-3."""
    pass


# Importar modelos para que SQLAlchemy los registre al hacer create_all
from src.models.docente import Docente
from src.models.alumno import Alumno
from src.models.inscripcion import Inscripcion

__all__ = ["Base", "Docente", "Alumno", "Inscripcion"]
