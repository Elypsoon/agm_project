import os
import uuid
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from src.models.models import Ponderacion, Actividad, Calificacion

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

    @patch("src.grpc.periodos_client.PeriodosClient.get_materia_by_id")
    def test_crear_y_obtener_ponderacion_docente(self, mock_materia):
        mock_materia.return_value = {
            "id": str(MATERIA_ID),
            "nrc": "00000",
            "clave": "MOCK 001",
            "nombre": "Materia Mock",
            "seccion": "001",
            "docente_id": str(DOCENTE_ID),
            "periodo_id": "pppppppp-pppp-pppp-pppp-pppppppppppp",
            "estado": "abierta",
        }
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

    @patch("src.grpc.periodos_client.PeriodosClient.get_materia_by_id")
    def test_crear_ponderacion_suma_incorrecta(self, mock_materia):
        mock_materia.return_value = {
            "id": str(MATERIA_ID),
            "docente_id": str(DOCENTE_ID),
            "estado": "abierta",
        }
        data = {
            "categorias": [
                {"nombre": "Examen", "porcentaje": 50.00},
                {"nombre": "Tareas", "porcentaje": 40.00}
            ]
        }
        resp = self.client.post(f"/api/ponderaciones/{MATERIA_ID}/", data, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("La suma de porcentajes debe ser 100.00", resp.data["detail"])

    @patch("src.grpc.periodos_client.PeriodosClient.get_materia_by_id")
    def test_crear_ponderacion_nombres_duplicados(self, mock_materia):
        mock_materia.return_value = {
            "id": str(MATERIA_ID),
            "docente_id": str(DOCENTE_ID),
            "estado": "abierta",
        }
        data = {
            "categorias": [
                {"nombre": "Examen", "porcentaje": 50.00},
                {"nombre": "examen", "porcentaje": 50.00}
            ]
        }
        resp = self.client.post(f"/api/ponderaciones/{MATERIA_ID}/", data, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("No se permiten ponderaciones con el mismo nombre", resp.data["detail"])

    @patch("src.grpc.periodos_client.PeriodosClient.get_materia_by_id")
    def test_crear_ponderacion_materia_cerrada(self, mock_materia):
        mock_materia.return_value = {
            "id": str(MATERIA_ID),
            "docente_id": str(DOCENTE_ID),
            "estado": "cerrada",
        }
        data = {
            "categorias": [
                {"nombre": "Examen", "porcentaje": 100.00}
            ]
        }
        resp = self.client.post(f"/api/ponderaciones/{MATERIA_ID}/", data, format="json")
        self.assertEqual(resp.status_code, 403)
        self.assertIn("La materia se encuentra cerrada", resp.data["detail"])

    @patch("src.grpc.periodos_client.PeriodosClient.get_materia_by_id")
    def test_crear_ponderacion_como_alumno_restringido(self, mock_materia):
        mock_materia.return_value = {
            "id": str(MATERIA_ID),
            "docente_id": str(DOCENTE_ID),
            "estado": "abierta",
        }
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

    @patch("src.grpc.periodos_client.PeriodosClient.get_materia_by_id")
    def test_crear_actividad_por_docente(self, mock_materia):
        mock_materia.return_value = {
            "id": str(MATERIA_ID),
            "docente_id": str(DOCENTE_ID),
            "estado": "abierta",
        }
        # Crear ponderación primero
        pond = Ponderacion.objects.create(materia_id=MATERIA_ID, nombre_categoria="Tareas", porcentaje=100.00)

        data = {
            "materia_id": str(MATERIA_ID),
            "ponderacion_id": str(pond.id),
            "nombre": "Tarea 1"
        }
        resp = self.client.post("/api/actividades/", data, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["data"]["nombre"], "Tarea 1")
        self.assertEqual(resp.data["data"]["orden"], 0)

    @patch("src.grpc.periodos_client.PeriodosClient.get_materia_by_id")
    def test_crear_actividad_materia_cerrada(self, mock_materia):
        mock_materia.return_value = {
            "id": str(MATERIA_ID),
            "docente_id": str(DOCENTE_ID),
            "estado": "cerrada",
        }
        pond = Ponderacion.objects.create(materia_id=MATERIA_ID, nombre_categoria="Tareas", porcentaje=100.00)

        data = {
            "materia_id": str(MATERIA_ID),
            "ponderacion_id": str(pond.id),
            "nombre": "Tarea 1"
        }
        resp = self.client.post("/api/actividades/", data, format="json")
        self.assertEqual(resp.status_code, 403)
        self.assertIn("La materia se encuentra cerrada", resp.data["detail"])

    @patch("src.grpc.alumnos_client.AlumnosClient.is_alumno_en_materia")
    @patch("src.grpc.periodos_client.PeriodosClient.get_materia_by_id")
    def test_crear_calificacion_por_docente(self, mock_materia, mock_alumno):
        mock_materia.return_value = {
            "id": str(MATERIA_ID),
            "docente_id": str(DOCENTE_ID),
            "estado": "abierta",
        }
        mock_alumno.return_value = True

        # Configuración inicial
        pond = Ponderacion.objects.create(materia_id=MATERIA_ID, nombre_categoria="Examen", porcentaje=100.00)
        act = Actividad.objects.create(ponderacion=pond, nombre="Examen Parcial", orden=0)

        data = {
            "actividad_id": str(act.id),
            "alumno_id": str(ALUMNO_ID),
            "valor": 95.50
        }
        resp = self.client.post("/api/calificaciones/", data, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Decimal(resp.data["data"]["valor"]), Decimal("95.50"))

    @patch("src.grpc.alumnos_client.AlumnosClient.is_alumno_en_materia")
    @patch("src.grpc.periodos_client.PeriodosClient.get_materia_by_id")
    def test_crear_calificacion_materia_cerrada(self, mock_materia, mock_alumno):
        mock_materia.return_value = {
            "id": str(MATERIA_ID),
            "docente_id": str(DOCENTE_ID),
            "estado": "cerrada",
        }
        mock_alumno.return_value = True

        pond = Ponderacion.objects.create(materia_id=MATERIA_ID, nombre_categoria="Examen", porcentaje=100.00)
        act = Actividad.objects.create(ponderacion=pond, nombre="Examen Parcial", orden=0)

        data = {
            "actividad_id": str(act.id),
            "alumno_id": str(ALUMNO_ID),
            "valor": 95.50
        }
        resp = self.client.post("/api/calificaciones/", data, format="json")
        self.assertEqual(resp.status_code, 403)
        self.assertIn("La materia se encuentra cerrada", resp.data["detail"])

    @patch("src.grpc.alumnos_client.AlumnosClient.get_alumnos_by_materia")
    @patch("src.grpc.periodos_client.PeriodosClient.get_materia_by_id")
    def test_obtener_concentrado(self, mock_materia, mock_alumnos):
        mock_materia.return_value = {"id": str(MATERIA_ID), "nombre": "Materia de Prueba", "estado": "abierta"}
        mock_alumnos.return_value = [
            {"id": str(ALUMNO_ID), "matricula": "202200001", "nombre_completo": "Alumno Uno"}
        ]

        # Crear ponderación, actividad y calificación
        pond = Ponderacion.objects.create(materia_id=MATERIA_ID, nombre_categoria="Examen", porcentaje=100.00)
        act = Actividad.objects.create(ponderacion=pond, nombre="Examen Final", orden=0)
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
            self.assertEqual(resp.data["alumnos"][0]["promedio_redondeado"], 9)  # 85.00 → 8.5 en escala 0-10, fracción 0.5 >= 0.5 → techo → 9

    @patch("src.grpc.alumnos_client.AlumnosClient.is_alumno_en_materia")
    @patch("src.grpc.periodos_client.PeriodosClient.get_materia_by_id")
    def test_crear_calificacion_alumno_no_inscrito(self, mock_materia, mock_alumno):
        mock_materia.return_value = {
            "id": str(MATERIA_ID),
            "docente_id": str(DOCENTE_ID),
            "estado": "abierta",
        }
        # Forzar que el alumno NO esté inscrito
        mock_alumno.return_value = False

        pond = Ponderacion.objects.create(materia_id=MATERIA_ID, nombre_categoria="Examen", porcentaje=100.00)
        act = Actividad.objects.create(ponderacion=pond, nombre="Examen Parcial", orden=0)

        data = {
            "actividad_id": str(act.id),
            "alumno_id": str(ALUMNO_ID),
            "valor": 95.50
        }
        resp = self.client.post("/api/calificaciones/", data, format="json")
        self.assertEqual(resp.status_code, 422)
        self.assertIn("no está inscrito o no está activo en la materia", resp.data["detail"])

    @patch("src.grpc.periodos_client.PeriodosClient.get_materia_by_id")
    def test_crear_ponderacion_docente_no_autorizado(self, mock_materia):
        # La materia le pertenece a un docente ajeno, pero el docente del token es DOCENTE_ID
        docente_ajeno = uuid.uuid4()
        mock_materia.return_value = {
            "id": str(MATERIA_ID),
            "docente_id": str(docente_ajeno),
            "estado": "abierta",
        }
        data = {
            "categorias": [
                {"nombre": "Examen", "porcentaje": 100.00}
            ]
        }
        resp = self.client.post(f"/api/ponderaciones/{MATERIA_ID}/", data, format="json")
        # Debe fallar por no estar autorizado el docente autenticado sobre esta materia
        self.assertEqual(resp.status_code, 403)
        self.assertIn("No tienes autorización para operar sobre esta materia.", resp.data["detail"])

    def test_estadisticas_materia_rest(self):
        # Crear ponderación, actividad y calificación para la materia
        pond = Ponderacion.objects.create(materia_id=MATERIA_ID, nombre_categoria="Examen", porcentaje=100.00)
        act = Actividad.objects.create(ponderacion=pond, nombre="Examen Final", orden=0)
        Calificacion.objects.create(actividad=act, alumno_id=ALUMNO_ID, valor=85.00)

        resp = self.client.get(f"/api/estadisticas/materia/{MATERIA_ID}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["total_alumnos"], 1)
        self.assertEqual(resp.data["promedio_grupo"], 85.0)  # El promedio real se guarda de 0 a 100 en BD y API
        self.assertEqual(resp.data["calificacion_max"], 85.0)
        self.assertEqual(resp.data["calificacion_min"], 85.0)

    def test_estadisticas_alumno_rest(self):
        pond = Ponderacion.objects.create(materia_id=MATERIA_ID, nombre_categoria="Tareas", porcentaje=100.00)
        act = Actividad.objects.create(ponderacion=pond, nombre="Tarea A", orden=0)
        Calificacion.objects.create(actividad=act, alumno_id=ALUMNO_ID, valor=92.50)

        resp = self.client.get(f"/api/estadisticas/alumno/{ALUMNO_ID}/materia/{MATERIA_ID}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["promedio_real"], 92.5)  # Escala interna 0-100 para alta precisión decimal
        self.assertEqual(resp.data["promedio_redondeado"], 9)  # BUAP: 92.5 -> 9.25 escala 0-10, fracción < 0.5 -> piso -> 9

    def test_estadisticas_materia_inexistente_rest(self):
        materia_falsa = uuid.uuid4()
        resp = self.client.get(f"/api/estadisticas/materia/{materia_falsa}/")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("No existe configuración de ponderación para esta materia.", resp.data["detail"])


