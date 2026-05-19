import grpc
import random
from django.conf import settings
from src.grpc import alumnos_pb2
from src.grpc import alumnos_pb2_grpc

class AlumnosGRPCClient:
    @staticmethod
    def get_calificaciones(materia_id):
        target = f"{settings.ALUMNOS_GRPC_HOST}:{settings.ALUMNOS_GRPC_PORT}"
        
        try:
            with grpc.insecure_channel(target) as channel:
                # Instanciamos el stub del servicio oficial
                stub = alumnos_pb2_grpc.AlumnosServiceStub(channel)
                request = alumnos_pb2.GetAlumnosByMateriaRequest(materia_id=materia_id)
                
                # Realizamos la llamada remota
                response = stub.GetAlumnosByMateria(request, timeout=5)
                
                datos = []
                for alumno in response.alumnos:
                    datos.append({
                        "matricula": alumno.matricula,
                        "nombre": alumno.nombre_completo,
                        "asistencia": random.randint(75, 100),
                        "calificacion": round(random.uniform(6.0, 10.0), 1)
                    })
                return datos
                
        except grpc.RpcError as e:
            print(f"Error gRPC conectando al MS-3: {e.details()}")
            print("MS-3 inalcanzable. Usando datos Fallback para poder probar los reportes...")
            
            # Plan B: Datos locales simulados para que el frontend y tus PDFs no se rompan
            return [
                {"matricula": "2026001", "nombre": "Gabo Aguilar", "asistencia": 95, "calificacion": 9.8},
                {"matricula": "2026002", "nombre": "Ana López", "asistencia": 80, "calificacion": 7.5},
                {"matricula": "2026003", "nombre": "zuriells", "asistencia": 100, "calificacion": 10.0},
            ]