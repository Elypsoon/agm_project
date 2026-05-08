"""
Tests del parser de alumnos — PDF de lista de clase (BUAP Banner).
Usa unittest.TestCase.
"""

import os
import unittest

from src.parsers.pdf_alumnos_parser import parsear_pdf_alumnos

PDF_PATH = os.path.join(os.path.dirname(__file__), "ListaAlumnos_Servicios_Web.pdf")


@unittest.skipUnless(os.path.exists(PDF_PATH), "PDF de alumnos no disponible")
class TestParsearPdfAlumnos(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(PDF_PATH, "rb") as f:
            cls.info, cls.alumnos = parsear_pdf_alumnos(f.read())

    def test_parsea_30_alumnos(self):
        self.assertEqual(len(self.alumnos), 30)

    def test_extrae_info_curso(self):
        self.assertEqual(self.info.materia, "Servicios Web")
        self.assertEqual(self.info.nrc, "50130")
        self.assertIn("Primavera", self.info.periodo)

    def test_todas_las_matriculas_son_9_digitos(self):
        for a in self.alumnos:
            self.assertEqual(len(a.matricula), 9, f"Matricula invalida: {a.matricula}")
            self.assertTrue(a.matricula.isdigit(), f"No numerica: {a.matricula}")

    def test_todos_tienen_correo(self):
        for a in self.alumnos:
            self.assertTrue(a.correo, f"Sin correo: {a.nombre_completo}")
            self.assertIn("@", a.correo)

    def test_correos_son_buap(self):
        for a in self.alumnos:
            self.assertTrue(a.correo.endswith("buap.mx"), f"No BUAP: {a.correo}")

    def test_sin_duplicados_por_matricula(self):
        matriculas = [a.matricula for a in self.alumnos]
        self.assertEqual(len(matriculas), len(set(matriculas)))

    def test_nombres_normalizados_title_case(self):
        for a in self.alumnos:
            self.assertNotEqual(
                a.nombre_completo, a.nombre_completo.upper(),
                f"Sin normalizar: {a.nombre_completo}",
            )

    def test_numero_registro_secuencial(self):
        numeros = [a.numero_registro for a in self.alumnos]
        self.assertEqual(numeros, list(range(1, 31)))

    def test_nivel_es_licenciatura(self):
        for a in self.alumnos:
            self.assertEqual(a.nivel, "Licenciatura")

    def test_nombre_largo_con_continuacion(self):
        alumno_4 = next(a for a in self.alumnos if a.numero_registro == 4)
        self.assertIn("Contreras", alumno_4.nombre_completo)
        self.assertIn("Gerson", alumno_4.nombre_completo)

    def test_primer_alumno_conocido(self):
        primero = self.alumnos[0]
        self.assertEqual(primero.matricula, "202224429")
        self.assertIn("Aguilar", primero.nombre_completo)
        self.assertEqual(primero.correo, "angel.aguilarsal@alumno.buap.mx")
