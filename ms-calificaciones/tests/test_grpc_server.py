import uuid
from decimal import Decimal
from unittest.mock import patch
from concurrent import futures
import grpc
from django.test import TransactionTestCase

from src.grpc import calificaciones_pb2, calificaciones_pb2_grpc
from src.grpc.handlers.calificaciones_handler import CalificacionesServicer
from src.models.models import Ponderacion, Actividad, Calificacion

MATERIA_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
ALUMNO_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


class GrpcCalificacionesTestBase(TransactionTestCase):

    def setUp(self):
        # Configurar datos en BD de pruebas
        self.ponderacion = Ponderacion.objects.create(
            materia_id=MATERIA_ID,
            nombre_categoria="Proyecto",
            porcentaje=100.00,
            orden=0
        )
        self.actividad = Actividad.objects.create(
            ponderacion=self.ponderacion,
            nombre="Entrega Final",
            orden=0
        )
        self.calificacion = Calificacion.objects.create(
            actividad=self.actividad, alumno_id=ALUMNO_ID, valor=92.50
        )

        # Servidor gRPC efímero
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
        calificaciones_pb2_grpc.add_CalificacionesServiceServicer_to_server(
            CalificacionesServicer(), self.server
        )
        self.port = self.server.add_insecure_port("localhost:0")
        self.server.start()
        self.channel = grpc.insecure_channel(f"localhost:{self.port}")
        self.stub = calificaciones_pb2_grpc.CalificacionesServiceStub(self.channel)

    def tearDown(self):
        self.channel.close()
        self.server.stop(grace=0)
        from django.db import connections
        connections.close_all()


class TestGrpcGetConcentrado(GrpcCalificacionesTestBase):

    @patch("src.grpc.alumnos_client.AlumnosClient.get_alumnos_by_materia")
    @patch("src.grpc.periodos_client.PeriodosClient.get_materia_by_id")
    def test_retorna_concentrado_correcto(self, mock_materia, mock_alumnos):
        mock_materia.return_value = {"id": str(MATERIA_ID), "nombre": "Materia gRPC"}
        mock_alumnos.return_value = [
            {"id": str(ALUMNO_ID), "matricula": "202200001", "nombre_completo": "Alumno gRPC"}
        ]

        resp = self.stub.GetConcentrado(
            calificaciones_pb2.MateriaIdRequest(materia_id=str(MATERIA_ID))
        )
        self.assertEqual(resp.materia_nombre, "Materia gRPC")
        self.assertEqual(len(resp.alumnos), 1)
        self.assertEqual(resp.alumnos[0].alumno_nombre, "Alumno gRPC")
        self.assertEqual(resp.alumnos[0].promedio_redondeado, 9)  # 92.50 → 9.25 en escala 0-10, fracción < 0.5 → piso → 9

    def test_materia_no_existente(self):
        with self.assertRaises(grpc.RpcError) as ctx:
            self.stub.GetConcentrado(
                calificaciones_pb2.MateriaIdRequest(
                    materia_id="00000000-0000-0000-0000-000000000099"
                )
            )
        self.assertEqual(ctx.exception.code(), grpc.StatusCode.NOT_FOUND)


class TestGrpcGetPromedioAlumno(GrpcCalificacionesTestBase):

    def test_promedio_existente(self):
        resp = self.stub.GetPromedioAlumno(
            calificaciones_pb2.AlumnoMateriaRequest(
                materia_id=str(MATERIA_ID), alumno_id=str(ALUMNO_ID)
            )
        )
        self.assertEqual(resp.promedio_real, 92.50)
        self.assertEqual(resp.promedio_redondeado, 9)  # 9.25 en escala 0-10, fracción < 0.5 → piso → 9


class TestGrpcGetEstadisticasMateria(GrpcCalificacionesTestBase):

    def test_estadisticas_correctas(self):
        # Agregar una segunda calificación para validar min, max y promedio
        alumno2 = uuid.uuid4()
        Calificacion.objects.create(
            actividad=self.actividad, alumno_id=alumno2, valor=78.00
        )

        resp = self.stub.GetEstadisticasMateria(
            calificaciones_pb2.MateriaIdRequest(materia_id=str(MATERIA_ID))
        )
        self.assertEqual(resp.total_alumnos, 2)
        self.assertEqual(resp.calificacion_max, 92.50)
        self.assertEqual(resp.calificacion_min, 78.00)
        self.assertEqual(resp.promedio_grupo, 85.25)
