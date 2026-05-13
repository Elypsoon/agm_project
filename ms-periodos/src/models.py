import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Date, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from src.database import Base

class EstadoMateria(str, enum.Enum):
    ABIERTA = "abierta"
    CERRADA = "cerrada"
    FINALIZADA = "finalizada"

class Periodo(Base):
    __tablename__ = "periodos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False) # e.g., "Primavera 2026"
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    plan_estudios = Column(String(50), nullable=False) # e.g., "ITI"
    activo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    materias = relationship("Materia", back_populates="periodo", cascade="all, delete-orphan")

class Materia(Base):
    __tablename__ = "materias"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nrc = Column(String(20), nullable=False)
    clave = Column(String(20), nullable=False) # e.g., "ITIS 604"
    nombre = Column(String(255), nullable=False) # e.g., "Inteligencia Artificial"
    seccion = Column(String(10)) # e.g., "001"
    docente_nombre = Column(String(255), nullable=False)
    docente_id = Column(UUID(as_uuid=True), nullable=True) 
    periodo_id = Column(UUID(as_uuid=True), ForeignKey("periodos.id", ondelete="CASCADE"), nullable=False)
    estado = Column(SQLEnum(EstadoMateria), default=EstadoMateria.ABIERTA, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    periodo = relationship("Periodo", back_populates="materias")
    horarios = relationship("Horario", back_populates="materia", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint('nrc', 'periodo_id', name='_nrc_periodo_uc'),)

class Horario(Base):
    __tablename__ = "horarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    materia_id = Column(UUID(as_uuid=True), ForeignKey("materias.id", ondelete="CASCADE"), nullable=False)
    
    dia = Column(String(5)) # L, A, M, J, V, S
    hora_inicio = Column(String(4)) # e.g., "0700"
    hora_fin = Column(String(4))    # e.g., "0859"
    salon = Column(String(20))     # e.g., "1CCO4/308"
    es_virtual = Column(Boolean, default=False)
    
    materia = relationship("Materia", back_populates="horarios")