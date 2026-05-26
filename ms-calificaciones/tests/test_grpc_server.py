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
    """Clase base para pruebas de integración de los servicios gRPC de Calificaciones.

    Levanta un servidor gRPC efímero en un puerto libre local y configura un stub
    para realizar llamadas a través de la red simulada. Prepara datos mínimos en la
    base de datos de pruebas (materia con ponderación, actividad y calificación).
    """

    def setUp(self):
        """Inicializa los datos de prueba en la base de datos y levanta el servidor gRPC."""
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
        """Detiene el servidor gRPC efímero y cierra las conexiones a la base de datos."""
        self.channel.close()
        self.server.stop(grace=0)
        from django.db import connections
        connections.close_all()


class TestGrpcGetConcentrado(GrpcCalificacionesTestBase):
    """Pruebas para el endpoint gRPC `GetConcentrado`."""

    @patch("src.grpc.alumnos_client.AlumnosClient.get_alumnos_by_materia")
    @patch("src.grpc.periodos_client.PeriodosClient.get_materia_by_id")
    def test_retorna_concentrado_correcto(self, mock_materia, mock_alumnos):
        """Verifica que GetConcentrado retorne el concentrado correcto del grupo.

        Comprueba que se devuelva la jerarquía de categorías con sus actividades y
        las notas individuales indexadas por actividad para cada alumno.
        """
        mock_materia.return_value = {"id": str(MATERIA_ID), "nombre": "Materia gRPC"}
        mock_alumnos.return_value = [
            {"id": str(ALUMNO_ID), "matricula": "202200001", "nombre_completo": "Alumno gRPC"}
        ]

        resp = self.stub.GetConcentrado(
            calificaciones_pb2.MateriaIdRequest(materia_id=str(MATERIA_ID))
        )
        self.assertEqual(resp.materia_nombre, "Materia gRPC")

        # Verificar jerarquía de categorías (devuelta una vez a nivel de materia)
        self.assertEqual(len(resp.categorias), 1)
        cat = resp.categorias[0]
        self.assertEqual(cat.nombre_categoria, "Proyecto")
        self.assertEqual(cat.porcentaje, 100.0)
        self.assertEqual(len(cat.actividades), 1)
        self.assertEqual(cat.actividades[0].actividad_nombre, "Entrega Final")
        self.assertEqual(cat.actividades[0].actividad_id, str(self.actividad.id))

        # Verificar datos de alumno: promedio y calificaciones por actividad
        self.assertEqual(len(resp.alumnos), 1)
        alumno = resp.alumnos[0]
        self.assertEqual(alumno.alumno_nombre, "Alumno gRPC")
        self.assertEqual(alumno.alumno_matricula, "202200001")
        self.assertEqual(alumno.promedio_redondeado, 9)  # 92.50 -> 9.25 en escala 0-10, fracción < 0.5 -> piso -> 9
        self.assertEqual(len(alumno.calificaciones), 1)
        self.assertEqual(alumno.calificaciones[0].actividad_id, str(self.actividad.id))
        self.assertEqual(alumno.calificaciones[0].valor, 92.50)

    def test_materia_no_existente(self):
        """Comprueba que intentar obtener el concentrado de una materia inexistente retorne NOT_FOUND."""
        with self.assertRaises(grpc.RpcError) as ctx:
            self.stub.GetConcentrado(
                calificaciones_pb2.MateriaIdRequest(
                    materia_id="00000000-0000-0000-0000-000000000099"
                )
            )
        self.assertEqual(ctx.exception.code(), grpc.StatusCode.NOT_FOUND)


class TestGrpcGetPromedioAlumno(GrpcCalificacionesTestBase):
    """Pruebas para el endpoint gRPC `GetPromedioAlumno`."""

    def test_promedio_existente(self):
        """Verifica que GetPromedioAlumno retorne el promedio real y redondeado correcto del alumno solicitado."""
        resp = self.stub.GetPromedioAlumno(
            calificaciones_pb2.AlumnoMateriaRequest(
                materia_id=str(MATERIA_ID), alumno_id=str(ALUMNO_ID)
            )
        )
        self.assertEqual(resp.promedio_real, 92.50)
        self.assertEqual(resp.promedio_redondeado, 9)  # 9.25 en escala 0-10, fracción < 0.5 -> piso -> 9


class TestGrpcGetEstadisticasMateria(GrpcCalificacionesTestBase):
    """Pruebas para el endpoint gRPC `GetEstadisticasMateria`."""

    def test_estadisticas_correctas(self):
        """Verifica que GetEstadisticasMateria calcule las estadísticas globales (promedio, min, max, total) correctas del grupo."""
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
