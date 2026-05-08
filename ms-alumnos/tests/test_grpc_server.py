"""
Tests del servidor gRPC — MS-3: Docentes & Alumnos.
Usa django.test.TestCase con servidor gRPC efímero.
"""

import uuid

import grpc
from concurrent import futures
from django.test import TransactionTestCase

from src.grpc import alumnos_pb2, alumnos_pb2_grpc
from src.grpc.server import AlumnosServiceServicer
from src.models.alumno import Alumno
from src.models.docente import Docente
from src.models.inscripcion import Inscripcion

MATERIA_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class GrpcTestBase(TransactionTestCase):
    """Base class: levanta servidor gRPC efímero con datos de prueba."""

    def setUp(self):
        self.alumno = Alumno.objects.create(
            matricula="202224429",
            nombre_completo="Angel G. Aguilar Saldivar",
            correo="angel.aguilarsal@alumno.buap.mx",
            tipo_formacion="Licenciatura",
            clave_acceso="test12345X",
        )
        self.docente = Docente.objects.create(
            nombre_completo="Mario Rossainz López",
            correo_institucional="mario.rossainz@correo.buap.mx",
            cubiculo="CCO2-209",
        )
        self.inscripcion = Inscripcion.objects.create(
            alumno=self.alumno,
            materia_id=MATERIA_ID,
            activo=True,
        )

        # Servidor gRPC efímero
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
        alumnos_pb2_grpc.add_AlumnosServiceServicer_to_server(
            AlumnosServiceServicer(), self.server
        )
        self.port = self.server.add_insecure_port("localhost:0")
        self.server.start()
        self.channel = grpc.insecure_channel(f"localhost:{self.port}")
        self.stub = alumnos_pb2_grpc.AlumnosServiceStub(self.channel)

    def tearDown(self):
        self.channel.close()
        self.server.stop(grace=0)


class TestGrpcGetAlumnosByMateria(GrpcTestBase):

    def test_retorna_alumnos_inscritos(self):
        resp = self.stub.GetAlumnosByMateria(
            alumnos_pb2.GetAlumnosByMateriaRequest(materia_id=str(MATERIA_ID))
        )
        self.assertEqual(resp.total, 1)
        self.assertEqual(resp.alumnos[0].matricula, "202224429")

    def test_materia_sin_alumnos(self):
        resp = self.stub.GetAlumnosByMateria(
            alumnos_pb2.GetAlumnosByMateriaRequest(
                materia_id="00000000-0000-0000-0000-000000000099"
            )
        )
        self.assertEqual(resp.total, 0)


class TestGrpcGetAlumnoById(GrpcTestBase):

    def test_retorna_alumno(self):
        resp = self.stub.GetAlumnoById(
            alumnos_pb2.GetAlumnoByIdRequest(alumno_id=str(self.alumno.id))
        )
        self.assertEqual(resp.nombre_completo, self.alumno.nombre_completo)

    def test_alumno_no_existente(self):
        with self.assertRaises(grpc.RpcError) as ctx:
            self.stub.GetAlumnoById(
                alumnos_pb2.GetAlumnoByIdRequest(
                    alumno_id="00000000-0000-0000-0000-000000000099"
                )
            )
        self.assertEqual(ctx.exception.code(), grpc.StatusCode.NOT_FOUND)


class TestGrpcIsAlumnoEnMateria(GrpcTestBase):

    def test_alumno_inscrito(self):
        resp = self.stub.IsAlumnoEnMateria(
            alumnos_pb2.IsAlumnoEnMateriaRequest(
                alumno_id=str(self.alumno.id), materia_id=str(MATERIA_ID),
            )
        )
        self.assertTrue(resp.inscrito)
        self.assertTrue(resp.activo)

    def test_alumno_no_inscrito(self):
        resp = self.stub.IsAlumnoEnMateria(
            alumnos_pb2.IsAlumnoEnMateriaRequest(
                alumno_id=str(self.alumno.id),
                materia_id="00000000-0000-0000-0000-000000000099",
            )
        )
        self.assertFalse(resp.inscrito)


class TestGrpcGetDocenteById(GrpcTestBase):

    def test_retorna_docente(self):
        resp = self.stub.GetDocenteById(
            alumnos_pb2.GetDocenteByIdRequest(docente_id=str(self.docente.id))
        )
        self.assertEqual(resp.nombre_completo, self.docente.nombre_completo)

    def test_docente_no_existente(self):
        with self.assertRaises(grpc.RpcError) as ctx:
            self.stub.GetDocenteById(
                alumnos_pb2.GetDocenteByIdRequest(
                    docente_id="00000000-0000-0000-0000-000000000099"
                )
            )
        self.assertEqual(ctx.exception.code(), grpc.StatusCode.NOT_FOUND)
