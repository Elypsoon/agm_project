from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
import uuid
import tempfile
import os

from src.database import get_db
from src.models import Materia, Periodo, Horario
from src.schemas import MateriaCreate, MateriaUpdate, MateriaResponse, PaginatedResponse
from src.parsers.pdf_parser import ScheduleParser  

router = APIRouter(prefix="/materias", tags=["materias"])

# --- EXISTING IMPORT ROUTE ---
@router.post("/{periodo_id}/importar-pdf")
async def import_materias_from_pdf(
    periodo_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Imports academic programming from a PDF."""
    periodo = db.query(Periodo).filter(Periodo.id == periodo_id).first()
    if not periodo:
        raise HTTPException(status_code=404, detail="Periodo no encontrado")

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        parser = ScheduleParser()
        extracted_data = parser.extract_from_pdf(tmp_path)
        
        created_count = 0
        skipped_count = 0

        for item in extracted_data:
            materia = db.query(Materia).filter(
                Materia.nrc == item["nrc"], 
                Materia.periodo_id == periodo_id
            ).first()
            
            if not materia:
                raw_profesor = None
                if item["horarios"]:
                    raw_profesor = item["horarios"][0].get("profesor")

                materia = Materia(
                    nrc=item["nrc"],
                    clave=item["clave"],
                    nombre=item["materia"],
                    seccion=item["seccion"],
                    docente_nombre=raw_profesor if (raw_profesor and raw_profesor != "-") else "POR ASIGNAR",
                    periodo_id=periodo_id,
                    estado="ABIERTA"
                )
                db.add(materia)
                db.flush() 
                created_count += 1
            else:
                skipped_count += 1 

            for h in item["horarios"]:
                times = h["hora"].split("-") if "-" in h["hora"] else [None, None]
                
                exists_horario = db.query(Horario).filter(
                    Horario.materia_id == materia.id,
                    Horario.dia == h["dia"],
                    Horario.hora_inicio == times[0]
                ).first()

                if not exists_horario:
                    new_horario = Horario(
                        materia_id=materia.id,
                        dia=h["dia"],
                        hora_inicio=times[0],
                        hora_fin=times[1],
                        salon=h["salon"],
                        es_virtual=h.get("es_virtual", False)
                    )
                    db.add(new_horario)
            
            created_count += 1

        db.commit()
        os.unlink(tmp_path)

        return {
            "success": True,
            "imported": created_count,
            "skipped_duplicates": skipped_count,
            "message": f"Se importaron {created_count} materias exitosamente."
        }

    except Exception as e:
        db.rollback()
        if 'tmp_path' in locals(): os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Error en el servidor: {str(e)}")

@router.get("/buscar", response_model=PaginatedResponse)
def search_materias(
    q: str = Query(..., min_length=3),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search materias by name, NRC (e.g. 'Inteligencia' or '44746')."""
    search_filter = or_(
        Materia.nombre.ilike(f"%{q}%"),
        Materia.nrc.ilike(f"%{q}%"),
        Materia.clave.ilike(f"%{q}%")
    )
    
    query = db.query(Materia).filter(search_filter)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {"total": total, "page": page, "page_size": page_size, "items": items}

@router.patch("/{materia_id}/status", response_model=MateriaResponse)
def toggle_materia_status(
    materia_id: uuid.UUID,
    nuevo_estado: str, # 'abierta', 'cerrada', 'finalizada'
    db: Session = Depends(get_db)
):
    """Quickly open or close an NRC for registration."""
    materia = db.query(Materia).filter(Materia.id == materia_id).first()
    if not materia:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    
    materia.estado = nuevo_estado
    db.commit()
    db.refresh(materia)
    return materia

@router.delete("/periodos/{periodo_id}/reset", status_code=status.HTTP_204_NO_CONTENT)
def reset_periodo_materias(periodo_id: uuid.UUID, db: Session = Depends(get_db)):
    """Wipes all materias and schedules for a period to allow a fresh PDF re-import."""
    periodo = db.query(Periodo).filter(Periodo.id == periodo_id).first()
    if not periodo:
        raise HTTPException(status_code=404, detail="Periodo no encontrado")
    
    # cascade="all, delete-orphan" in your model will handle the Horarios automatically
    db.query(Materia).filter(Materia.periodo_id == periodo_id).delete()
    db.commit()
    return None