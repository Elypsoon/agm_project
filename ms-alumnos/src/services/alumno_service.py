"""
Servicio de negocio — Alumnos
"""

import logging
from uuid import UUID
from datetime import datetime, timezone

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.models.alumno import Alumno
from src.models.inscripcion import Inscripcion
from src.parsers.pdf_alumnos_parser import parsear_pdf_alumnos
from src.utils import generar_clave_acceso

logger = logging.getLogger(__name__)


class AlumnoService:
    def __init__(self, db: Session):
        self.db = db

    def listar_por_materia(self, materia_id: UUID, page: int, limit: int):
        """Listar alumnos inscritos (activos) en una materia."""
        query = (
            self.db.query(Alumno)
            .join(Inscripcion, Inscripcion.alumno_id == Alumno.id)
            .filter(Inscripcion.materia_id == materia_id, Inscripcion.activo == True)
        )

        total = query.count()
        alumnos = (
            query.order_by(Alumno.nombre_completo)
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        return {
            "success": True,
            "data": {
                "alumnos": [self._to_dict(a) for a in alumnos],
                "total": total,
                "page": page,
                "limit": limit,
                "materia_id": str(materia_id),
            },
            "message": f"{len(alumnos)} alumnos encontrados",
        }

    def obtener_por_id(self, alumno_id: UUID):
        """Obtener un alumno por su ID."""
        alumno = self.db.query(Alumno).filter(Alumno.id == alumno_id).first()
        if not alumno:
            raise HTTPException(status_code=404, detail="Alumno no encontrado")

        return {
            "success": True,
            "data": self._to_dict(alumno),
            "message": "",
        }

    async def importar_desde_pdf(self, materia_id: UUID, archivo: UploadFile):
        """
        Importar alumnos desde PDF de lista de clase (BUAP Banner) a una materia.
        - Parsea el PDF extrayendo nombre, matricula y correo (de hyperlinks mailto:).
        - Si el alumno ya existe (por matricula), se reutiliza.
        - Si ya esta inscrito en la materia, se omite.
        - Si es nuevo, se genera clave de acceso.
        """
        if not archivo.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="El archivo debe ser PDF")

        contenido = await archivo.read()

        # Parsear el PDF
        info_curso, alumnos_extraidos = parsear_pdf_alumnos(contenido)

        if not alumnos_extraidos:
            raise HTTPException(
                status_code=422,
                detail="No se pudieron extraer alumnos del PDF. Verifica el formato.",
            )

        nuevos = 0
        inscritos = 0
        ya_inscritos = 0
        errores = []

        for datos in alumnos_extraidos:
            try:
                # Buscar si el alumno ya existe por matricula
                alumno = (
                    self.db.query(Alumno)
                    .filter(Alumno.matricula == datos.matricula)
                    .first()
                )

                if not alumno:
                    # Crear nuevo alumno
                    clave = generar_clave_acceso()
                    alumno = Alumno(
                        matricula=datos.matricula,
                        nombre_completo=datos.nombre_completo,
                        correo=datos.correo if datos.correo else None,
                        clave_acceso=clave,
                    )
                    self.db.add(alumno)
                    self.db.flush()  # Para obtener el ID antes del commit
                    nuevos += 1
                    logger.info(
                        f"Alumno nuevo: {datos.nombre_completo} "
                        f"({datos.matricula}) [{datos.correo}]"
                    )
                else:
                    # Actualizar correo si no lo tenia y ahora lo tenemos
                    if datos.correo and not alumno.correo:
                        alumno.correo = datos.correo

                # Verificar si ya esta inscrito en la materia
                inscripcion_existente = (
                    self.db.query(Inscripcion)
                    .filter(
                        Inscripcion.alumno_id == alumno.id,
                        Inscripcion.materia_id == materia_id,
                    )
                    .first()
                )

                if inscripcion_existente:
                    ya_inscritos += 1
                else:
                    # Crear inscripcion
                    inscripcion = Inscripcion(
                        alumno_id=alumno.id,
                        materia_id=materia_id,
                        activo=True,
                    )
                    self.db.add(inscripcion)
                    inscritos += 1

            except IntegrityError:
                self.db.rollback()
                errores.append(datos.matricula)
                logger.warning(f"Error de integridad para alumno: {datos.matricula}")
            except Exception as e:
                errores.append(f"{datos.matricula}: {str(e)}")
                logger.error(f"Error importando alumno {datos.matricula}: {e}")

        self.db.commit()

        return {
            "success": True,
            "data": {
                "archivo": archivo.filename,
                "materia_id": str(materia_id),
                "curso": {
                    "materia": info_curso.materia,
                    "nrc": info_curso.nrc,
                    "periodo": info_curso.periodo,
                },
                "total_extraidos": len(alumnos_extraidos),
                "alumnos_nuevos": nuevos,
                "inscripciones_nuevas": inscritos,
                "ya_inscritos": ya_inscritos,
                "errores": len(errores),
                "detalle_errores": errores[:10] if errores else [],
            },
            "message": (
                f"Importacion completada: {nuevos} alumnos nuevos, "
                f"{inscritos} inscripciones creadas, {ya_inscritos} ya inscritos"
            ),
        }

    def dar_de_baja(self, alumno_id: UUID, materia_id: UUID):
        """Baja irreversible de un alumno de una materia."""
        inscripcion = (
            self.db.query(Inscripcion)
            .filter(
                Inscripcion.alumno_id == alumno_id,
                Inscripcion.materia_id == materia_id,
            )
            .first()
        )

        if not inscripcion:
            raise HTTPException(
                status_code=404,
                detail="No se encontro la inscripcion del alumno en esa materia",
            )

        if not inscripcion.activo:
            raise HTTPException(
                status_code=400,
                detail="El alumno ya fue dado de baja de esta materia",
            )

        # Marcar como baja
        inscripcion.activo = False
        inscripcion.fecha_baja = datetime.now(timezone.utc)
        self.db.commit()

        # TODO: notificar al docente via gRPC al MS-6 Notificaciones

        return {
            "success": True,
            "data": {
                "alumno_id": str(alumno_id),
                "materia_id": str(materia_id),
                "fecha_baja": inscripcion.fecha_baja.isoformat(),
            },
            "message": "Alumno dado de baja exitosamente",
        }

    @staticmethod
    def _to_dict(alumno: Alumno) -> dict:
        return {
            "id": str(alumno.id),
            "matricula": alumno.matricula,
            "nombre_completo": alumno.nombre_completo,
            "correo": alumno.correo,
            "tipo_formacion": alumno.tipo_formacion,
            "user_id": str(alumno.user_id) if alumno.user_id else None,
            "created_at": alumno.created_at.isoformat() if alumno.created_at else None,
        }
