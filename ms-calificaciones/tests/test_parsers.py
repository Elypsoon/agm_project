import os
from decimal import Decimal
from django.test import TestCase

from src.parsers.file_parser import parsear_archivo

# Rutas de los archivos de Teams reales en la carpeta tests
CSV_PATH = os.path.join(
    os.path.dirname(__file__),
    "Calificaciones de PRIMAVERA 2026 - C1202625 - DESARROLLO DE SITIOS WEB - 48308_ 29_04_2026, 03_25 p.csv"
)
XLSX_PATH = os.path.join(
    os.path.dirname(__file__),
    "Calificaciones de PRIMAVERA 2026 - C1202625 - DESARROLLO DE SITIOS WEB - 48308_ 29_04_2026, 03_25 p.m-.xlsx"
)


class TestFileParsers(TestCase):

    def test_parsear_archivo_csv_real(self):
        if not os.path.exists(CSV_PATH):
            self.skipTest(f"El archivo CSV real no se encuentra en {CSV_PATH}")

        with open(CSV_PATH, "rb") as f:
            contenido = f.read()

        registros, errores = parsear_archivo("calificaciones.csv", contenido)
        
        # Validar que se hayan parseado registros
        self.assertGreater(len(registros), 0)
        self.assertEqual(len(errores), 0)

        # Buscar un registro específico (EDUARDO BALLINAS BALLINAS)
        eduardo_reg = [r for r in registros if r['correo'] == 'bb202321840@alm.buap.mx']
        self.assertGreater(len(eduardo_reg), 0)
        self.assertEqual(eduardo_reg[0]['nombre_actividad'], 'Práctica 3: Blog de café')
        self.assertEqual(eduardo_reg[0]['valor'], Decimal('0'))
        self.assertEqual(eduardo_reg[0]['comentario'], 'No entregado')
        self.assertEqual(eduardo_reg[0]['estado'], 'Entregado')

        # Buscar otro registro con 100 puntos y comentario (GERSON CONTRERAS GONZALEZ)
        gerson_reg = [r for r in registros if r['correo'] == 'gerson.contreras@alumno.buap.mx']
        self.assertGreater(len(gerson_reg), 0)
        self.assertEqual(gerson_reg[0]['valor'], Decimal('100'))
        self.assertIn('Excelente trabajo', gerson_reg[0]['comentario'])

    def test_parsear_archivo_xlsx_real(self):
        if not os.path.exists(XLSX_PATH):
            self.skipTest(f"El archivo XLSX real no se encuentra en {XLSX_PATH}")

        with open(XLSX_PATH, "rb") as f:
            contenido = f.read()

        registros, errores = parsear_archivo("calificaciones.xlsx", contenido)

        # Validar que se hayan parseado registros
        self.assertGreater(len(registros), 0)
        self.assertEqual(len(errores), 0)

        # Validar consistencia
        primer_registro = registros[0]
        self.assertIn('@', primer_registro['correo'])
        self.assertGreater(len(primer_registro['nombre_actividad']), 0)
        self.assertIsInstance(primer_registro['valor'], Decimal)

    def test_formato_no_soportado_lanza_excepcion(self):
        with self.assertRaises(ValueError) as ctx:
            parsear_archivo("grupo.txt", b"datos")
        self.assertIn("Formato de archivo no soportado", str(ctx.exception))
