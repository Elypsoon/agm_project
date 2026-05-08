"""
Servicio de negocio — Docentes
"""

import logging
from uuid import UUID

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from src.models.docente import Docente
from src.parsers.pdf_parser import parsear_pdf_docentes

logger = logging.getLogger(__name__)


class DocenteService:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, page: int, limit: int, search: str | None):
        """Listar docentes con paginacion y busqueda opcional."""
        query = self.db.query(Docente)

        if search:
            filtro = f"%{search}%"
            query = query.filter(
                or_(
                    Docente.nombre_completo.ilike(filtro),
                    Docente.correo_institucional.ilike(filtro),
                    Docente.cubiculo.ilike(filtro),
                )
            )

        total = query.count()
        docentes = query.order_by(Docente.nombre_completo).offset((page - 1) * limit).limit(limit).all()

        return {
            "success": True,
            "data": {
                "docentes": [self._to_dict(d) for d in docentes],
                "total": total,
                "page": page,
                "limit": limit,
            },
            "message": f"{len(docentes)} docentes encontrados",
        }

    def obtener_por_id(self, docente_id: UUID):
        """Obtener un docente por su ID."""
        docente = self.db.query(Docente).filter(Docente.id == docente_id).first()
        if not docente:
            raise HTTPException(status_code=404, detail="Docente no encontrado")

        return {
            "success": True,
            "data": self._to_dict(docente),
            "message": "",
        }

    async def importar_desde_pdf(self, archivo: UploadFile):
        """
        Importar docentes desde un archivo PDF institucional.
        Parsea el PDF, extrae los datos y los inserta en la BD.
        Si un docente ya existe (por correo), se actualiza.
        """
        if not archivo.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="El archivo debe ser PDF")

        contenido = await archivo.read()

        # Parsear el PDF
        docentes_extraidos = parsear_pdf_docentes(contenido)

        if not docentes_extraidos:
            raise HTTPException(
                status_code=422,
                detail="No se pudieron extraer docentes del PDF. Verifica que el formato sea correcto.",
            )

        nuevos = 0
        actualizados = 0
        errores = []

        for datos in docentes_extraidos:
            try:
                # Buscar si ya existe por correo
                existente = (
                    self.db.query(Docente)
                    .filter(Docente.correo_institucional == datos.correo_institucional)
                    .first()
                )

                if existente:
                    # Actualizar datos
                    existente.nombre_completo = datos.nombre_completo
                    if datos.cubiculo:
                        existente.cubiculo = datos.cubiculo
                    actualizados += 1
                else:
                    # Crear nuevo docente
                    nuevo = Docente(
                        nombre_completo=datos.nombre_completo,
                        correo_institucional=datos.correo_institucional,
                        cubiculo=datos.cubiculo,
                    )
                    self.db.add(nuevo)
                    nuevos += 1

            except IntegrityError:
                self.db.rollback()
                errores.append(datos.correo_institucional)
                logger.warning(f"Error de integridad para docente: {datos.correo_institucional}")
            except Exception as e:
                errores.append(f"{datos.correo_institucional}: {str(e)}")
                logger.error(f"Error importando docente {datos.correo_institucional}: {e}")

        self.db.commit()

        return {
            "success": True,
            "data": {
                "archivo": archivo.filename,
                "total_extraidos": len(docentes_extraidos),
                "nuevos": nuevos,
                "actualizados": actualizados,
                "errores": len(errores),
                "detalle_errores": errores[:10] if errores else [],
            },
            "message": f"Importacion completada: {nuevos} nuevos, {actualizados} actualizados",
        }

    @staticmethod
    def _to_dict(docente: Docente) -> dict:
        return {
            "id": str(docente.id),
            "nombre_completo": docente.nombre_completo,
            "correo_institucional": docente.correo_institucional,
            "cubiculo": docente.cubiculo,
            "user_id": str(docente.user_id) if docente.user_id else None,
            "created_at": docente.created_at.isoformat() if docente.created_at else None,
        }
