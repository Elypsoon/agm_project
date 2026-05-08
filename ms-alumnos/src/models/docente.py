"""
Modelo: Docente
"""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base


class Docente(Base):
    __tablename__ = "docentes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nombre_completo: Mapped[str] = mapped_column(String(255), nullable=False)
    correo_institucional: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    cubiculo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, comment="Referencia lógica al MS-1 Auth"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Docente {self.nombre_completo} ({self.correo_institucional})>"
