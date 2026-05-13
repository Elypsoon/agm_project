from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date, datetime
import uuid

# --- Horario Schemas ---
class HorarioBase(BaseModel):
    dia: str
    hora_inicio: Optional[str] = None
    hora_fin: Optional[str] = None
    salon: str
    es_virtual: bool = False
    profesor: Optional[str] = None

class HorarioResponse(HorarioBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

# --- Materia Schemas ---
class MateriaBase(BaseModel):
    nrc: str
    clave: str
    nombre: str
    seccion: str
    docente_id: Optional[uuid.UUID] = None

class MateriaCreate(MateriaBase):
    pass

class MateriaUpdate(BaseModel):
    nrc: Optional[str] = None
    clave: Optional[str] = None
    nombre: Optional[str] = None
    seccion: Optional[str] = None
    docente_id: Optional[uuid.UUID] = None
    estado: Optional[str] = None

class MateriaResponse(MateriaBase):
    id: uuid.UUID
    periodo_id: uuid.UUID
    estado: str
    horarios: List[HorarioResponse] = []
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Periodo Schemas ---
class PeriodoBase(BaseModel):
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    plan_estudios: str
    activo: bool = False

class PeriodoCreate(PeriodoBase):
    pass

class PeriodoUpdate(BaseModel):
    nombre: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    plan_estudios: Optional[str] = None
    activo: Optional[bool] = None

class PeriodoResponse(PeriodoBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PeriodoWithMateriasResponse(PeriodoResponse):
    materias: List[MateriaResponse] = []

# --- Pagination Schema ---
class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[MateriaResponse] 