"""
Parser de PDF — Extrae la lista de alumnos desde PDF institucional (BUAP Banner).

Formato esperado del PDF (exportacion de "Resumen de lista de clase"):
- Encabezado con info del curso: materia, NRC, duracion
- Tabla con: Numero de Registro, Nombre de Alumno, ID (matricula), Status, Nivel, Creditos
- Correos embebidos como hyperlinks mailto: en anotaciones del PDF
- Algunos nombres se dividen en 2 lineas cuando son largos

Estrategia:
1. Extraer correos de las anotaciones mailto: ordenados por posicion vertical
2. Parsear texto linea a linea detectando filas de alumnos via regex
3. Emparejar correos con alumnos por orden de aparicion (ambas listas van de arriba a abajo)
4. Extraer metadatos del curso (materia, NRC) del encabezado
"""

import re
import logging
from dataclasses import dataclass
from io import BytesIO

import pdfplumber

logger = logging.getLogger(__name__)


@dataclass
class InfoCurso:
    """Metadatos del curso extraidos del encabezado del PDF."""
    materia: str = ""
    nrc: str = ""
    periodo: str = ""


@dataclass
class AlumnoExtraido:
    """Datos extraidos de una fila del PDF de lista de clase."""
    numero_registro: int = 0
    nombre_completo: str = ""
    matricula: str = ""
    correo: str = ""
    status: str = ""
    nivel: str = ""
    creditos: float = 0.0


# ---------------------------------------------------------------------------
# Regex compiladas a nivel modulo (se reutilizan en cada llamada)
# ---------------------------------------------------------------------------
_RE_ALUMNO = re.compile(
    r"^(\d{1,3})\s+"       # Numero de registro
    r"(.+?)\s+"            # Nombre (APELLIDO, NOMBRE)
    r"(\d{9})\s+"          # Matricula (9 digitos)
    r"\*\*(.+?)\*\*\s+"    # Status entre asteriscos
    r"(\w+)\s+"            # Nivel (Licenciatura, etc.)
    r"([\d.]+)"            # Creditos
)
_RE_CONTINUACION = re.compile(r"^[A-Z][A-Z.\s,]+$")
_RE_NRC = re.compile(r"NRC:\s*(\d+)")
_PERIODOS = ("Primavera", "Otoño", "Verano", "Invierno")
_PALABRAS_IGNORAR_HEADER = ("resumen", "pagina", "inicio", "duraci")
_PALABRAS_IGNORAR_CONTINUACION = ("nombre", "numero", "clase", "resumen", "pagina")


def parsear_pdf_alumnos(contenido: bytes) -> tuple[InfoCurso, list[AlumnoExtraido]]:
    """
    Parsea un PDF de lista de clase de BUAP (Banner).

    Args:
        contenido: bytes del archivo PDF.

    Returns:
        Tupla (InfoCurso, lista de AlumnoExtraido).
    """
    info_curso = InfoCurso()
    alumnos: list[AlumnoExtraido] = []

    with pdfplumber.open(BytesIO(contenido)) as pdf:
        correos = _extraer_correos_por_posicion(pdf)

        for num_pagina, page in enumerate(pdf.pages, start=1):
            texto = page.extract_text()
            if not texto:
                continue

            for linea in texto.split("\n"):
                linea = linea.strip()
                if not linea:
                    continue

                if num_pagina == 1:
                    _extraer_info_curso(linea, info_curso)

                match = _RE_ALUMNO.match(linea)
                if match:
                    alumnos.append(AlumnoExtraido(
                        numero_registro=int(match.group(1)),
                        nombre_completo=_normalizar_nombre(match.group(2)),
                        matricula=match.group(3),
                        status=match.group(4).strip(),
                        nivel=match.group(5),
                        creditos=float(match.group(6)),
                    ))
                elif alumnos and _RE_CONTINUACION.match(linea):
                    _agregar_continuacion_nombre(alumnos[-1], linea)

        _emparejar_correos(alumnos, correos)

    logger.info(
        f"PDF parseado: {len(alumnos)} alumnos, "
        f"materia='{info_curso.materia}', NRC={info_curso.nrc}"
    )
    return info_curso, alumnos


def _extraer_correos_por_posicion(pdf) -> list[str]:
    """
    Extrae correos unicos de las anotaciones mailto: del PDF,
    ordenados por posicion vertical (pagina + doctop).
    """
    correos_ordenados: list[tuple[int, float, str]] = []

    for num_pagina, page in enumerate(pdf.pages):
        if not page.annots:
            continue

        vistos: set[tuple[int, str]] = set()
        for annot in page.annots:
            uri = annot.get("uri", "")
            if not uri or not uri.startswith("mailto:"):
                continue

            correo = uri[len("mailto:"):].strip().lower()

            # Saltar el mailto masivo (Bcc con todos los correos)
            if "?bcc=" in correo or "," in correo:
                continue

            clave = (num_pagina, correo)
            if clave not in vistos:
                vistos.add(clave)
                doctop = annot.get("doctop", annot.get("top", 0))
                correos_ordenados.append((num_pagina, doctop, correo))

    correos_ordenados.sort(key=lambda x: (x[0], x[1]))
    return [c for _, _, c in correos_ordenados]


def _emparejar_correos(alumnos: list[AlumnoExtraido], correos: list[str]) -> None:
    """Empareja correos con alumnos por orden de aparicion en el PDF."""
    if not correos:
        logger.warning("No se encontraron correos mailto: en el PDF")
        return

    if len(correos) != len(alumnos):
        logger.warning(
            f"Numero de correos ({len(correos)}) != alumnos ({len(alumnos)}). "
            "Se emparejaran los disponibles."
        )

    for i, alumno in enumerate(alumnos):
        if i < len(correos):
            alumno.correo = correos[i]


def _extraer_info_curso(linea: str, info: InfoCurso) -> None:
    """Extrae metadatos del curso de las lineas del encabezado."""
    nrc_match = _RE_NRC.search(linea)
    if nrc_match:
        info.nrc = nrc_match.group(1)

    if not info.periodo and linea.startswith(_PERIODOS):
        info.periodo = linea

    if " - " in linea and not info.materia:
        posible = linea.split(" - ")[0].strip()
        if len(posible) > 3 and not any(kw in posible.lower() for kw in _PALABRAS_IGNORAR_HEADER):
            info.materia = posible


def _agregar_continuacion_nombre(alumno: AlumnoExtraido, linea: str) -> None:
    """Agrega la segunda linea de un nombre largo al alumno."""
    if len(linea) >= 50 or any(kw in linea.lower() for kw in _PALABRAS_IGNORAR_CONTINUACION):
        return

    nombre_upper = alumno.nombre_completo.upper()
    # Si el nombre ya tiene coma, la continuacion es parte del primer nombre
    if "," not in nombre_upper:
        combinado = f"{nombre_upper}, {linea}"
    else:
        combinado = f"{nombre_upper} {linea}"
    alumno.nombre_completo = _normalizar_nombre(combinado)


def _normalizar_nombre(nombre: str) -> str:
    """
    Convierte 'APELLIDO APELLIDO, NOMBRE M.' → 'Nombre M. Apellido Apellido'.
    """
    nombre = nombre.strip()
    if "," in nombre:
        apellidos, _, nombres = nombre.partition(",")
        nombres = nombres.strip()
        apellidos = apellidos.strip()
        nombre = f"{nombres} {apellidos}" if nombres else apellidos
    return " ".join(word.capitalize() for word in nombre.split())
