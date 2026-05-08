"""
Servicio de negocio — Alumnos (Django ORM)
"""

import logging
from datetime import datetime, timezone

from django.db import transaction, IntegrityError

from src.models.alumno import Alumno
from src.models.inscripcion import Inscripcion
from src.parsers.pdf_alumnos_parser import parsear_pdf_alumnos
from src.utils import generar_clave_acceso
from src.grpc.auth_client import registrar_usuario_en_auth

logger = logging.getLogger(__name__)


class AlumnoService:

    def importar_desde_pdf(self, materia_id, archivo):
        """
        Importar alumnos desde PDF de lista de clase (BUAP Banner) a una materia.
        - Parsea el PDF extrayendo nombre, matricula y correo.
        - Si el alumno ya existe (por matricula), se reutiliza.
        - Si ya esta inscrito en la materia, se omite.
        - Si es nuevo, se genera clave de acceso y se registra en MS-1 Auth.
        """
        if not archivo.name.lower().endswith(".pdf"):
            return {"success": False, "detail": "El archivo debe ser PDF", "status_code": 400}

        contenido = archivo.read()
        info_curso, alumnos_extraidos = parsear_pdf_alumnos(contenido)

        if not alumnos_extraidos:
            return {
                "success": False,
                "detail": "No se pudieron extraer alumnos del PDF.",
                "status_code": 422,
            }

        nuevos = 0
        inscritos = 0
        ya_inscritos = 0
        errores = []

        for datos in alumnos_extraidos:
            try:
                with transaction.atomic():
                    alumno = Alumno.objects.filter(matricula=datos.matricula).first()

                    if not alumno:
                        clave = generar_clave_acceso()
                        alumno = Alumno.objects.create(
                            matricula=datos.matricula,
                            nombre_completo=datos.nombre_completo,
                            correo=datos.correo or None,
                            tipo_formacion=datos.nivel or None,
                            clave_acceso=clave,
                        )
                        nuevos += 1
                        logger.info(
                            f"Alumno nuevo: {datos.nombre_completo} "
                            f"({datos.matricula}) [{datos.correo}]"
                        )

                        # Registrar en MS-1 Auth (tolerante a fallos)
                        if datos.correo:
                            user_id = registrar_usuario_en_auth(
                                email=datos.correo,
                                nombre=datos.nombre_completo,
                                password=clave,
                                role="alumno",
                            )
                            if user_id:
                                alumno.user_id = user_id
                                alumno.save(update_fields=["user_id"])
                    else:
                        updated = False
                        if datos.correo and not alumno.correo:
                            alumno.correo = datos.correo
                            updated = True
                        if datos.nivel and not alumno.tipo_formacion:
                            alumno.tipo_formacion = datos.nivel
                            updated = True
                        if updated:
                            alumno.save()

                    # Verificar inscripcion
                    if Inscripcion.objects.filter(
                        alumno=alumno, materia_id=materia_id
                    ).exists():
                        ya_inscritos += 1
                    else:
                        Inscripcion.objects.create(
                            alumno=alumno,
                            materia_id=materia_id,
                            activo=True,
                        )
                        inscritos += 1

            except IntegrityError:
                errores.append(datos.matricula)
                logger.warning(f"Error de integridad para alumno: {datos.matricula}")
            except Exception as e:
                errores.append(f"{datos.matricula}: {str(e)}")
                logger.error(f"Error importando alumno {datos.matricula}: {e}")

        return {
            "success": True,
            "data": {
                "archivo": archivo.name,
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

    def dar_de_baja(self, alumno_id, materia_id):
        """Baja irreversible de un alumno de una materia."""
        inscripcion = Inscripcion.objects.filter(
            alumno_id=alumno_id, materia_id=materia_id,
        ).first()

        if not inscripcion:
            return {
                "success": False,
                "detail": "No se encontro la inscripcion del alumno en esa materia",
                "status_code": 404,
            }

        if not inscripcion.activo:
            return {
                "success": False,
                "detail": "El alumno ya fue dado de baja de esta materia",
                "status_code": 400,
            }

        inscripcion.activo = False
        inscripcion.fecha_baja = datetime.now(timezone.utc)
        inscripcion.save(update_fields=["activo", "fecha_baja"])

        return {
            "success": True,
            "data": {
                "alumno_id": str(alumno_id),
                "materia_id": str(materia_id),
                "fecha_baja": inscripcion.fecha_baja.isoformat(),
            },
            "message": "Alumno dado de baja exitosamente",
            "status_code": 200,
        }
