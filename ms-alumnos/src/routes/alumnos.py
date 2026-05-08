"""
Rutas REST — Alumnos
"""

from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.services.alumno_service import AlumnoService

router = APIRouter()


@router.get("/materia/{materia_id}")
def listar_alumnos_por_materia(
    materia_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Listar alumnos inscritos en una materia con paginacion."""
    service = AlumnoService(db)
    return service.listar_por_materia(materia_id=materia_id, page=page, limit=limit)


@router.get("/{alumno_id}")
def obtener_alumno(alumno_id: UUID, db: Session = Depends(get_db)):
    """Obtener detalle de un alumno por ID."""
    service = AlumnoService(db)
    return service.obtener_por_id(alumno_id)


@router.post("/importar/{materia_id}")
async def importar_alumnos(
    materia_id: UUID,
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Importar alumnos desde PDF de lista de clase a una materia."""
    service = AlumnoService(db)
    return await service.importar_desde_pdf(materia_id, archivo)


@router.delete("/{alumno_id}/baja")
def baja_alumno(
    alumno_id: UUID,
    materia_id: UUID = Query(...),
    db: Session = Depends(get_db),
):
    """Baja irreversible de un alumno de una materia."""
    service = AlumnoService(db)
    return service.dar_de_baja(alumno_id=alumno_id, materia_id=materia_id)
