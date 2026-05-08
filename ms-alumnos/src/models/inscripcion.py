"""
Modelo: Inscripcion (relación alumno ↔ materia)
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base


class Inscripcion(Base):
    __tablename__ = "inscripciones"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    alumno_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alumnos.id", ondelete="CASCADE"), nullable=False
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False,
        comment="Referencia lógica al MS-2 Periodos (no FK real, por implementar)"
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    fecha_baja: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relación inversa con Alumno
    alumno = relationship("Alumno", back_populates="inscripciones")

    def __repr__(self) -> str:
        estado = "activa" if self.activo else "baja"
        return f"<Inscripcion alumno={self.alumno_id} materia={self.materia_id} ({estado})>"
