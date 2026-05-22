import os
import uuid
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from src.models.models import PonderacionConfig, CategoriaPonderacion, Actividad, Calificacion

MATERIA_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
ALUMNO_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
DOCENTE_ID = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")


class TestCalificacionesViews(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer test_token')

        # Mockear validación de token gRPC (por defecto Docente)
        self.auth_patcher = patch("src.utils.authentication.validar_token_en_auth", return_value={
            "valid": True,
            "user_id": str(DOCENTE_ID),
            "email": "docente.test@buap.mx",
            "role": "docente",
            "error": ""
        })
        self.auth_patcher.start()

    def tearDown(self):
        self.auth_patcher.stop()

    def test_crear_y_obtener_ponderacion_docente(self):
        data = {
            "categorias": [
                {"nombre": "Examen", "porcentaje": 50.00},
                {"nombre": "Tareas", "porcentaje": 30.00},
                {"nombre": "Proyecto", "porcentaje": 20.00}
            ]
        }
        
        # Crear ponderación
        resp = self.client.post(f"/api/ponderaciones/{MATERIA_ID}/", data, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["materia_id"], str(MATERIA_ID))
        self.assertFalse(resp.data["bloqueada"])
        self.assertEqual(len(resp.data["categorias"]), 3)

        # Obtener ponderación
        resp_get = self.client.get(f"/api/ponderaciones/{MATERIA_ID}/")
        self.assertEqual(resp_get.status_code, 200)
        self.assertEqual(resp_get.data["materia_id"], str(MATERIA_ID))

    def test_crear_ponderacion_suma_incorrecta(self):
        data = {
            "categorias": [
                {"nombre": "Examen", "porcentaje": 50.00},
                {"nombre": "Tareas", "porcentaje": 40.00}
            ]
        }
        resp = self.client.post(f"/api/ponderaciones/{MATERIA_ID}/", data, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("La suma de porcentajes debe ser 100.00", resp.data["detail"])

    def test_crear_ponderacion_como_alumno_restringido(self):
        # Cambiar el token mockeado a Alumno
        with patch("src.utils.authentication.validar_token_en_auth", return_value={
            "valid": True,
            "user_id": str(ALUMNO_ID),
            "email": "alumno.test@buap.mx",
            "role": "alumno",
            "error": ""
        }):
            data = {
                "categorias": [
                    {"nombre": "Examen", "porcentaje": 100.00}
                ]
            }
            resp = self.client.post(f"/api/ponderaciones/{MATERIA_ID}/", data, format="json")
            self.assertEqual(resp.status_code, 403)

    def test_crear_actividad_por_docente(self):
        # Crear ponderación primero
        config = PonderacionConfig.objects.create(materia_id=MATERIA_ID)
        cat = CategoriaPonderacion.objects.create(config=config, nombre="Tareas", porcentaje=100.00)

        data = {
            "materia_id": str(MATERIA_ID),
            "categoria_id": str(cat.id),
            "nombre": "Tarea 1"
        }
        resp = self.client.post("/api/actividades/", data, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["data"]["nombre"], "Tarea 1")
        self.assertEqual(resp.data["data"]["orden"], 0)

    def test_crear_calificacion_por_docente(self):
        # Configuración inicial
        config = PonderacionConfig.objects.create(materia_id=MATERIA_ID)
        cat = CategoriaPonderacion.objects.create(config=config, nombre="Examen", porcentaje=100.00)
        act = Actividad.objects.create(categoria=cat, nombre="Examen Parcial", orden=0)

        data = {
            "actividad_id": str(act.id),
            "alumno_id": str(ALUMNO_ID),
            "valor": 95.50
        }
        resp = self.client.post("/api/calificaciones/", data, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Decimal(resp.data["data"]["valor"]), Decimal("95.50"))

        # Validar que bloquee la ponderación
        config.refresh_from_db()
        self.assertTrue(config.bloqueada)

    @patch("src.grpc.alumnos_client.AlumnosClient.get_alumnos_by_materia")
    @patch("src.grpc.periodos_client.PeriodosClient.get_materia_by_id")
    def test_obtener_concentrado(self, mock_materia, mock_alumnos):
        mock_materia.return_value = {"id": str(MATERIA_ID), "nombre": "Materia de Prueba"}
        mock_alumnos.return_value = [
            {"id": str(ALUMNO_ID), "matricula": "202200001", "nombre_completo": "Alumno Uno"}
        ]

        # Crear ponderación, actividad y calificación
        config = PonderacionConfig.objects.create(materia_id=MATERIA_ID)
        cat = CategoriaPonderacion.objects.create(config=config, nombre="Examen", porcentaje=100.00)
        act = Actividad.objects.create(categoria=cat, nombre="Examen Final", orden=0)
        Calificacion.objects.create(actividad=act, alumno_id=ALUMNO_ID, valor=85.00)

        # GET al concentrado como Alumno
        with patch("src.utils.authentication.validar_token_en_auth", return_value={
            "valid": True,
            "user_id": str(ALUMNO_ID),
            "email": "alumno.test@buap.mx",
            "role": "alumno",
            "error": ""
        }):
            resp = self.client.get(f"/api/concentrado/{MATERIA_ID}/")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.data["materia_nombre"], "Materia de Prueba")
            self.assertEqual(len(resp.data["alumnos"]), 1)
            self.assertEqual(resp.data["alumnos"][0]["promedio_redondeado"], 85)
