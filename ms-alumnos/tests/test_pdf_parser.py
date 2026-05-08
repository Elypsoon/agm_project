"""
Tests del parser de docentes — PDF del directorio FCC BUAP.
Usa unittest.TestCase.
"""

import os
import re
import unittest

from src.parsers.pdf_parser import parsear_pdf_docentes, DocenteExtraido

PDF_PATH = os.path.join(os.path.dirname(__file__), "Personal Docente - FCC BUAP.pdf")


@unittest.skipUnless(os.path.exists(PDF_PATH), "PDF de docentes no disponible")
class TestParsearPdfDocentes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(PDF_PATH, "rb") as f:
            cls.docentes = parsear_pdf_docentes(f.read())

    def test_parsea_mas_de_100(self):
        self.assertGreater(len(self.docentes), 100)

    def test_cada_docente_tiene_correo_buap(self):
        for d in self.docentes:
            self.assertTrue(
                d.correo_institucional.endswith("buap.mx"),
                f"Correo invalido: {d.correo_institucional}",
            )

    def test_cada_docente_tiene_nombre(self):
        for d in self.docentes:
            self.assertTrue(d.nombre_completo.strip(), f"Nombre vacio: {d.correo_institucional}")

    def test_sin_duplicados_por_correo(self):
        correos = [d.correo_institucional for d in self.docentes]
        self.assertEqual(len(correos), len(set(correos)), "Hay correos duplicados")

    def test_algunos_tienen_cubiculo(self):
        con_cubiculo = [d for d in self.docentes if d.cubiculo]
        self.assertGreater(len(con_cubiculo), 10)

    def test_formato_cubiculo(self):
        patron = re.compile(r"CCO\d+-\d+\w*")
        for d in self.docentes:
            if d.cubiculo:
                self.assertTrue(patron.match(d.cubiculo), f"Cubiculo invalido: {d.cubiculo}")

    def test_todos_son_DocenteExtraido(self):
        for d in self.docentes:
            self.assertIsInstance(d, DocenteExtraido)
