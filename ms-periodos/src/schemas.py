from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date, datetime
import uuid

# --- Horario Schemas ---
class HorarioResponse(BaseModel):
    id: uuid.UUID
    dia: str
    hora_inicio: Optional[str] = None
    hora_fin: Optional[str] = None
    salon: str
    es_virtual: bool
    profesor: Optional[str] = None # The raw name from the PDF

    model_config = ConfigDict(from_attributes=True)

# --- Materia Schemas ---
class MateriaResponse(BaseModel):
    id: uuid.UUID
    nrc: str
    clave: str
    nombre: str
    seccion: str
    docente_id: Optional[uuid.UUID] = None
    periodo_id: uuid.UUID
    estado: str
    horarios: List[HorarioResponse] = []
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)