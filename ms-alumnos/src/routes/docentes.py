"""
Rutas REST — Docentes
"""

from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.services.docente_service import DocenteService

router = APIRouter()


@router.get("")
def listar_docentes(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None),
    db: Session = Depends(get_db),
):
    """Listar docentes con búsqueda y paginación."""
    service = DocenteService(db)
    return service.listar(page=page, limit=limit, search=search)


@router.get("/{docente_id}")
def obtener_docente(docente_id: UUID, db: Session = Depends(get_db)):
    """Obtener detalle de un docente por ID."""
    service = DocenteService(db)
    return service.obtener_por_id(docente_id)


@router.post("/importar")
async def importar_docentes(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Importar docentes desde PDF institucional."""
    service = DocenteService(db)
    return await service.importar_desde_pdf(archivo)
