from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Periodo, Materia
from src.schemas import PeriodoCreate, PeriodoUpdate, PeriodoResponse
import uuid

router = APIRouter(prefix="/periodos", tags=["periodos"])

@router.post("/", response_model=PeriodoResponse, status_code=status.HTTP_201_CREATED)
def create_periodo(periodo: PeriodoCreate, db: Session = Depends(get_db)):
    """Creates a new academic period (e.g., Primavera 2026)."""
    new_periodo = Periodo(
        nombre=periodo.nombre,
        fecha_inicio=periodo.fecha_inicio,
        fecha_fin=periodo.fecha_fin,
        plan_estudios=periodo.plan_estudios,
        activo=periodo.activo
    )
    db.add(new_periodo)
    db.commit()
    db.refresh(new_periodo)
    return new_periodo

@router.get("/", response_model=list[PeriodoResponse])
def list_periodos(db: Session = Depends(get_db)):
    """Lists all available academic periods."""
    periodos = db.query(Periodo).all()
    # Ensure datetime fields are populated
    for periodo in periodos:
        if periodo.created_at is None:
            db.refresh(periodo)
    return periodos

@router.put("/{periodo_id}/activar", response_model=PeriodoResponse)
def activate_periodo(periodo_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Activates a specific period and automatically deactivates all others.
    """
    periodo = db.query(Periodo).filter(Periodo.id == periodo_id).first()
    if not periodo:
        raise HTTPException(status_code=404, detail="Periodo no encontrado")

    # Deactivate all other periods first
    db.query(Periodo).filter(Periodo.id != periodo_id).update({"activo": False})
    db.query(Materia).filter(Materia.periodo_id != periodo_id).update({"estado": "finalizada"})
    db.query(Materia).filter(Materia.periodo_id == periodo_id).update({"estado": "abierta"})
    
    periodo.activo = True
    db.commit()
    db.refresh(periodo)
    
    return periodo

@router.get("/activo", response_model=PeriodoResponse)
def get_periodo_activo(db: Session = Depends(get_db)):
    periodo = db.query(Periodo).filter(Periodo.activo == True).first()
    if not periodo:
        raise HTTPException(status_code=404, detail="No hay un periodo académico activo")
    return periodo