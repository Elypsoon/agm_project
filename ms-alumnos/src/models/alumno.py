"""
Modelo: Alumno
"""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base


class Alumno(Base):
    __tablename__ = "alumnos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    matricula: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(255), nullable=False)
    correo: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    tipo_formacion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    clave_acceso: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Clave generada al registrarse"
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, comment="Referencia lógica al MS-1 Auth"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relación con inscripciones
    inscripciones = relationship("Inscripcion", back_populates="alumno", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Alumno {self.matricula} — {self.nombre_completo}>"
