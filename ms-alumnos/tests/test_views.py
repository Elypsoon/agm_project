"""
Tests de integración — Endpoints REST del MS-3.
Usa django.test.TestCase + rest_framework.test.APIClient.
"""

import os
import uuid
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from src.models.alumno import Alumno
from src.models.docente import Docente
from src.models.inscripcion import Inscripcion


MATERIA_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
MATERIA_ID_2 = uuid.UUID("00000000-0000-0000-0000-000000000002")

PDF_DOCENTES = os.path.join(os.path.dirname(__file__), "Personal Docente - FCC BUAP.pdf")
PDF_ALUMNOS = os.path.join(os.path.dirname(__file__), "ListaAlumnos_Servicios_Web.pdf")


class TestHealthCheck(TestCase):

    def test_health_check(self):
        client = APIClient()
        resp = client.get("/health/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertEqual(resp.json()["data"]["status"], "healthy")


class TestDocentes(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        self.patcher = patch("src.utils.auth_backend.validar_token_en_auth", return_value={
            "valid": True,
            "user_id": "test-user-id",
            "email": "test@buap.mx",
            "role": "admin"
        })
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_listar_vacio(self):
        resp = self.client.get("/docentes/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["total"], 0)

    def test_listar_con_datos(self):
        d = Docente.objects.create(
            nombre_completo="Mario Rossainz López",
            correo_institucional="mario.rossainz@correo.buap.mx",
            cubiculo="CCO2-209",
        )
        resp = self.client.get("/docentes/")
        self.assertEqual(resp.json()["data"]["total"], 1)
        self.assertEqual(resp.json()["data"]["docentes"][0]["nombre_completo"], d.nombre_completo)

    def test_buscar_por_nombre(self):
        Docente.objects.create(
            nombre_completo="Mario Rossainz López",
            correo_institucional="mario.rossainz@correo.buap.mx",
        )
        resp = self.client.get("/docentes/?search=rossainz")
        self.assertEqual(resp.json()["data"]["total"], 1)

    def test_buscar_sin_resultados(self):
        Docente.objects.create(
            nombre_completo="Mario Rossainz López",
            correo_institucional="mario.rossainz@correo.buap.mx",
        )
        resp = self.client.get("/docentes/?search=zzzzzzz")
        self.assertEqual(resp.json()["data"]["total"], 0)

    def test_obtener_por_id(self):
        d = Docente.objects.create(
            nombre_completo="Mario Rossainz López",
            correo_institucional="mario.rossainz@correo.buap.mx",
        )
        resp = self.client.get(f"/docentes/{d.id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["correo_institucional"], d.correo_institucional)

    def test_obtener_por_id_no_existente(self):
        resp = self.client.get("/docentes/00000000-0000-0000-0000-000000000099/")
        self.assertEqual(resp.status_code, 404)

    def test_paginacion(self):
        for i in range(3):
            Docente.objects.create(
                nombre_completo=f"Docente {i}",
                correo_institucional=f"docente{i}@correo.buap.mx",
            )
        resp = self.client.get("/docentes/?limit=2&page=1")
        self.assertEqual(len(resp.json()["data"]["docentes"]), 2)
        self.assertEqual(resp.json()["data"]["total"], 3)

        resp2 = self.client.get("/docentes/?limit=2&page=2")
        self.assertEqual(len(resp2.json()["data"]["docentes"]), 1)

    @patch("src.services.docente_service.registrar_usuario_en_auth", return_value=None)
    def test_importar_pdf_docentes(self, mock_auth):
        if not os.path.exists(PDF_DOCENTES):
            self.skipTest("PDF de docentes no disponible")

        with open(PDF_DOCENTES, "rb") as f:
            resp = self.client.post("/docentes/importar/", {"archivo": f}, format="multipart")

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertGreater(resp.json()["data"]["nuevos"], 100)

    def test_importar_archivo_no_pdf(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        archivo = SimpleUploadedFile("docentes.txt", b"datos falsos", content_type="text/plain")
        resp = self.client.post("/docentes/importar/", {"archivo": archivo}, format="multipart")
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()["success"])


class TestAlumnos(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer test_token')
        
        self.patcher = patch("src.utils.auth_backend.validar_token_en_auth", return_value={
            "valid": True,
            "user_id": "test-user-id",
            "email": "test@buap.mx",
            "role": "admin"
        })
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_listar_alumnos_vacio(self):
        resp = self.client.get("/alumnos/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["total"], 0)

    def test_buscar_alumno_por_nombre(self):
        self._crear_alumno()  # Crea a "Angel G. Aguilar Saldivar"
        resp = self.client.get("/alumnos/?search=aguilar")
        self.assertEqual(resp.json()["data"]["total"], 1)

    def test_paginacion_alumnos(self):
        for i in range(3):
            Alumno.objects.create(
                matricula=f"20222442{i}",
                nombre_completo=f"Alumno {i}",
                correo=f"alumno{i}@buap.mx",
                tipo_formacion="Licenciatura",
            )
        resp = self.client.get("/alumnos/?limit=2&page=1")
        self.assertEqual(len(resp.json()["data"]["alumnos"]), 2)
        self.assertEqual(resp.json()["data"]["total"], 3)

    def _crear_alumno(self):
        return Alumno.objects.create(
            matricula="202224429",
            nombre_completo="Angel G. Aguilar Saldivar",
            correo="angel.aguilarsal@alumno.buap.mx",
            tipo_formacion="Licenciatura",
            clave_acceso="test12345X",
        )

    def _inscribir(self, alumno, materia_id=MATERIA_ID):
        return Inscripcion.objects.create(
            alumno=alumno, materia_id=materia_id, activo=True,
        )

    def test_listar_por_materia_vacia(self):
        resp = self.client.get(f"/alumnos/materia/{MATERIA_ID}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["total"], 0)

    def test_listar_por_materia_con_datos(self):
        alumno = self._crear_alumno()
        self._inscribir(alumno)
        resp = self.client.get(f"/alumnos/materia/{MATERIA_ID}/")
        self.assertEqual(resp.json()["data"]["total"], 1)
        self.assertEqual(resp.json()["data"]["alumnos"][0]["matricula"], "202224429")

    def test_obtener_alumno_por_id(self):
        alumno = self._crear_alumno()
        self._inscribir(alumno)
        resp = self.client.get(f"/alumnos/{alumno.id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["matricula"], "202224429")
        self.assertIn("inscripciones", resp.json()["data"])
        self.assertEqual(len(resp.json()["data"]["inscripciones"]), 1)

    def test_obtener_alumno_no_existente(self):
        resp = self.client.get("/alumnos/00000000-0000-0000-0000-000000000099/")
        self.assertEqual(resp.status_code, 404)

    def test_baja_alumno(self):
        alumno = self._crear_alumno()
        self._inscribir(alumno)
        resp = self.client.delete(f"/alumnos/{alumno.id}/baja/?materia_id={MATERIA_ID}")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertIn("fecha_baja", resp.json()["data"])

    def test_baja_doble_rechazada(self):
        alumno = self._crear_alumno()
        self._inscribir(alumno)
        self.client.delete(f"/alumnos/{alumno.id}/baja/?materia_id={MATERIA_ID}")
        resp = self.client.delete(f"/alumnos/{alumno.id}/baja/?materia_id={MATERIA_ID}")
        self.assertEqual(resp.status_code, 400)

    def test_baja_sin_inscripcion(self):
        alumno = self._crear_alumno()
        resp = self.client.delete(f"/alumnos/{alumno.id}/baja/?materia_id={MATERIA_ID}")
        self.assertEqual(resp.status_code, 404)

    def test_alumno_dado_de_baja_no_aparece_en_listado(self):
        alumno = self._crear_alumno()
        self._inscribir(alumno)
        self.client.delete(f"/alumnos/{alumno.id}/baja/?materia_id={MATERIA_ID}")
        resp = self.client.get(f"/alumnos/materia/{MATERIA_ID}/")
        self.assertEqual(resp.json()["data"]["total"], 0)

    @patch("src.services.alumno_service.registrar_usuario_en_auth", return_value=None)
    def test_importar_pdf_alumnos(self, mock_auth):
        if not os.path.exists(PDF_ALUMNOS):
            self.skipTest("PDF de alumnos no disponible")

        with open(PDF_ALUMNOS, "rb") as f:
            resp = self.client.post(
                f"/alumnos/importar/{MATERIA_ID}/", {"archivo": f}, format="multipart"
            )
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["alumnos_nuevos"], 30)
        self.assertEqual(data["data"]["inscripciones_nuevas"], 30)
        self.assertEqual(data["data"]["curso"]["materia"], "Servicios Web")

    @patch("src.services.alumno_service.registrar_usuario_en_auth", return_value=None)
    def test_reimportar_no_duplica(self, mock_auth):
        if not os.path.exists(PDF_ALUMNOS):
            self.skipTest("PDF de alumnos no disponible")

        with open(PDF_ALUMNOS, "rb") as f1:
            self.client.post(f"/alumnos/importar/{MATERIA_ID}/", {"archivo": f1}, format="multipart")
        with open(PDF_ALUMNOS, "rb") as f2:
            resp = self.client.post(f"/alumnos/importar/{MATERIA_ID}/", {"archivo": f2}, format="multipart")

        data = resp.json()
        self.assertEqual(data["data"]["alumnos_nuevos"], 0)
        self.assertEqual(data["data"]["ya_inscritos"], 30)

    @patch("src.services.alumno_service.registrar_usuario_en_auth", return_value=None)
    def test_importar_a_otra_materia(self, mock_auth):
        if not os.path.exists(PDF_ALUMNOS):
            self.skipTest("PDF de alumnos no disponible")

        with open(PDF_ALUMNOS, "rb") as f1:
            self.client.post(f"/alumnos/importar/{MATERIA_ID}/", {"archivo": f1}, format="multipart")
        with open(PDF_ALUMNOS, "rb") as f2:
            resp = self.client.post(f"/alumnos/importar/{MATERIA_ID_2}/", {"archivo": f2}, format="multipart")

        data = resp.json()
        self.assertEqual(data["data"]["alumnos_nuevos"], 0)
        self.assertEqual(data["data"]["inscripciones_nuevas"], 30)

    def test_importar_archivo_no_pdf(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        archivo = SimpleUploadedFile("alumnos.xlsx", b"datos", content_type="application/octet-stream")
        resp = self.client.post(
            f"/alumnos/importar/{MATERIA_ID}/", {"archivo": archivo}, format="multipart"
        )
        self.assertFalse(resp.json()["success"])
