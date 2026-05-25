"""
Servicio de negocio — Docentes (Django ORM)
"""

import logging

from django.db import transaction, IntegrityError

from src.models.docente import Docente
from src.parsers.pdf_parser import parsear_pdf_docentes
from src.utils.rabbitmq import publish_event

logger = logging.getLogger(__name__)


class DocenteService:

    def importar_desde_pdf(self, archivo):
        """
        Importar docentes desde un archivo PDF institucional.
        Parsea el PDF, extrae los datos y los inserta en la BD.
        Si un docente ya existe (por correo), se actualiza.
        Docentes nuevos se registran en MS-1 Auth.
        """
        if not archivo.name.lower().endswith(".pdf"):
            return {"success": False, "detail": "El archivo debe ser PDF", "status_code": 400}

        contenido = archivo.read()
        docentes_extraidos = parsear_pdf_docentes(contenido)

        if not docentes_extraidos:
            return {
                "success": False,
                "detail": "No se pudieron extraer docentes del PDF.",
                "status_code": 422,
            }

        nuevos = 0
        actualizados = 0
        errores = []

        for datos in docentes_extraidos:
            try:
                with transaction.atomic():
                    existente = Docente.objects.filter(
                        correo_institucional=datos.correo_institucional
                    ).first()

                    if existente:
                        existente.nombre_completo = datos.nombre_completo
                        if datos.cubiculo:
                            existente.cubiculo = datos.cubiculo
                        existente.save()
                        actualizados += 1
                    else:
                        nuevo = Docente.objects.create(
                            nombre_completo=datos.nombre_completo,
                            correo_institucional=datos.correo_institucional,
                            cubiculo=datos.cubiculo,
                        )
                        nuevos += 1

                        # Publicar evento para registro asíncrono en MS-1 Auth
                        publish_event(
                            routing_key="teacher.registered",
                            payload={
                                "local_id": str(nuevo.id),
                                "role": "docente",
                                "email": datos.correo_institucional,
                                "nombre": datos.nombre_completo,
                                "password": datos.correo_institucional.split("@")[0],
                            }
                        )

            except IntegrityError:
                errores.append(datos.correo_institucional)
                logger.warning(f"Error de integridad para docente: {datos.correo_institucional}")
            except Exception as e:
                errores.append(f"{datos.correo_institucional}: {str(e)}")
                logger.error(f"Error importando docente {datos.correo_institucional}: {e}")

        return {
            "success": True,
            "data": {
                "archivo": archivo.name,
                "total_extraidos": len(docentes_extraidos),
                "nuevos": nuevos,
                "actualizados": actualizados,
                "errores": len(errores),
                "detalle_errores": errores[:10] if errores else [],
            },
            "message": f"Importacion completada: {nuevos} nuevos, {actualizados} actualizados",
        }
