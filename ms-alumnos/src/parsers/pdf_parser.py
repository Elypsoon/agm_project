"""
Parser de PDF — Extrae el directorio de docentes desde PDF institucional.

Formato esperado del PDF:
- Múltiples páginas, cada una con tabla de 4 columnas:
  Nombre | Correo electrónico | Ubicación | Extensión
- Las filas de datos están en texto plano, NO en tabla real (el PDF las renderiza
  como texto posicionado), por lo que usamos extract_text() y procesamos línea a línea.
"""

import re
import logging
from dataclasses import dataclass
from io import BytesIO

import pdfplumber

logger = logging.getLogger(__name__)


@dataclass
class DocenteExtraido:
    """Datos extraídos de una fila del PDF."""
    nombre_completo: str
    correo_institucional: str
    cubiculo: str | None = None


def parsear_pdf_docentes(contenido: bytes) -> list[DocenteExtraido]:
    """
    Parsea un PDF del directorio de personal docente de la FCC BUAP.

    Args:
        contenido: bytes del archivo PDF.

    Returns:
        Lista de DocenteExtraido con los datos de cada docente encontrado.
    """
    docentes: list[DocenteExtraido] = []
    # Regex para detectar correos institucionales
    patron_correo = re.compile(r"[\w.+-]+@[\w.-]+\.buap\.mx")

    with pdfplumber.open(BytesIO(contenido)) as pdf:
        for num_pagina, page in enumerate(pdf.pages, start=1):
            texto = page.extract_text()
            if not texto:
                logger.warning(f"Pagina {num_pagina}: sin texto extraible")
                continue

            for linea in texto.split("\n"):
                # Saltar líneas de encabezado, navegación y vacías
                if _es_linea_ignorable(linea):
                    continue

                correo_match = patron_correo.search(linea)
                if not correo_match:
                    continue

                correo = correo_match.group()
                # Todo lo que está antes del correo es el nombre
                nombre = linea[:correo_match.start()].strip()
                # Todo lo que está después del correo es ubicación/extensión
                resto = linea[correo_match.end():].strip()

                # Extraer cubículo (patrón CCO#-###)
                cubiculo = None
                cubiculo_match = re.search(r"CCO\d+-\d+\w*", resto)
                if cubiculo_match:
                    cubiculo = cubiculo_match.group()

                if nombre and correo:
                    docentes.append(DocenteExtraido(
                        nombre_completo=_normalizar_nombre(nombre),
                        correo_institucional=correo.lower(),
                        cubiculo=cubiculo,
                    ))

    logger.info(f"PDF parseado: {len(docentes)} docentes extraidos de {len(pdf.pages)} paginas")
    return docentes


def _es_linea_ignorable(linea: str) -> bool:
    """Determina si una línea debe ser ignorada (headers, nav, etc.)."""
    linea_lower = linea.strip().lower()
    ignorar = [
        "nombre", "correo electr", "ubicaci", "extensi",
        "autoservicios", "inicio", "nosotros", "oferta",
        "facultad de ciencias", "personal docente",
        "secretar", "investigaci", "vinculaci", "servicios",
        "redes sociales", "mesa", "■",
    ]
    return any(patron in linea_lower for patron in ignorar) or len(linea.strip()) < 5


def _normalizar_nombre(nombre: str) -> str:
    """Normaliza el nombre: primera letra mayúscula de cada palabra."""
    # Quitar caracteres especiales residuales
    nombre = re.sub(r"[■●•]", "", nombre).strip()
    # Convertir a Title Case preservando acentos
    return " ".join(word.capitalize() for word in nombre.split())
