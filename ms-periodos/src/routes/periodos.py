from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Periodo
from src.schemas import PeriodoCreate, PeriodoUpdate, PeriodoResponse
import uuid

router = APIRouter(prefix="/periodos", tags=["periodos"])

@router.put("/{periodo_id}/activar", response_model=PeriodoResponse)
def activate_periodo(periodo_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Activates a specific period and automatically deactivates all others.
    """
    periodo = db.query(Periodo).filter(Periodo.id == periodo_id).first()
    if not periodo:
        raise HTTPException(status_code=404, detail="Periodo no encontrado")

    # Business Rule: Deactivate all other periods first
    db.query(Periodo).filter(Periodo.id != periodo_id).update({"activo": False})
    
    periodo.activo = True
    db.commit()
    db.refresh(periodo)
    
    return periodo

@router.get("/activo", response_model=PeriodoResponse)
def get_periodo_activo(db: Session = Depends(get_db)):
    """Required for the GetPeriodoActivo() gRPC logic."""
    periodo = db.query(Periodo).filter(Periodo.activo == True).first()
    if not periodo:
        raise HTTPException(status_code=404, detail="No hay un periodo académico activo")
    return periodo