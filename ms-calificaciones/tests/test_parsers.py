import os
from decimal import Decimal
from django.test import TestCase

from src.parsers.file_parser import parsear_archivo, parsear_csv, parsear_xlsx

CSV_PATH = os.path.join(
    os.path.dirname(__file__),
    "Lista_Grupo_Servicios_Web(Actividades_Version_Final).csv"
)
XLSX_PATH = os.path.join(
    os.path.dirname(__file__),
    "Lista_Grupo_Servicios_Web.xlsx"
)


class TestFileParsers(TestCase):

    def test_parsear_archivo_csv_real(self):
        if not os.path.exists(CSV_PATH):
            self.skipTest(f"El archivo CSV real no se encuentra en {CSV_PATH}")

        with open(CSV_PATH, "rb") as f:
            contenido = f.read()

        registros, errores = parsear_csv(contenido)
        
        # Validar que se hayan parseado registros
        self.assertGreater(len(registros), 0)
        self.assertEqual(len(errores), 0)

        # Buscar el registro del alumno '202224429' (ANGEL G. AGUILAR SALDIVAR)
        angel_registros = [r for r in registros if r['matricula'] == '202224429']
        self.assertGreater(len(angel_registros), 0)

        # Validar que los valores se mantengan en escala de 0 a 100
        # Ej. si el archivo tiene 1, en BD se registra como 100.00
        for reg in angel_registros:
            self.assertGreaterEqual(reg['valor'], Decimal('0.00'))
            self.assertLessEqual(reg['valor'], Decimal('100.00'))

    def test_parsear_archivo_xlsx_real(self):
        if not os.path.exists(XLSX_PATH):
            self.skipTest(f"El archivo XLSX real no se encuentra en {XLSX_PATH}")

        with open(XLSX_PATH, "rb") as f:
            contenido = f.read()

        registros, errores = parsear_xlsx(contenido)

        # Validar que se hayan parseado registros
        self.assertGreater(len(registros), 0)
        self.assertEqual(len(errores), 0)

        # Validar consistencia de matrícula
        primer_registro = registros[0]
        self.assertTrue(primer_registro['matricula'].isdigit())
        self.assertGreater(len(primer_registro['nombre_actividad']), 0)
        self.assertIsInstance(primer_registro['valor'], Decimal)

    def test_parsear_archivo_general(self):
        if os.path.exists(CSV_PATH):
            with open(CSV_PATH, "rb") as f:
                registros, _ = parsear_archivo("grupo.csv", f.read())
                self.assertGreater(len(registros), 0)

        if os.path.exists(XLSX_PATH):
            with open(XLSX_PATH, "rb") as f:
                registros, _ = parsear_archivo("grupo.xlsx", f.read())
                self.assertGreater(len(registros), 0)

    def test_formato_no_soportado_lanza_excepcion(self):
        with self.assertRaises(ValueError) as ctx:
            parsear_archivo("grupo.txt", b"datos")
        self.assertIn("Formato de archivo no soportado", str(ctx.exception))
