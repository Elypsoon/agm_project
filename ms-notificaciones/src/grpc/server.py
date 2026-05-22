import os
import sys
import grpc
from concurrent import futures
import uuid
import threading

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.core.settings')

import django
django.setup()

# 2. Importaciones de gRPC y servicios 
import src.grpc.notificaciones_pb2 as pb2
import src.grpc.notificaciones_pb2_grpc as pb2_grpc
from src.services.email_service import send_academic_email

class NotificacionesServicer(pb2_grpc.NotificacionesServiceServicer):
    
    def SendBienvenida(self, request, context):
        print(f"[gRPC] Solicitud de Bienvenida para alumno ID: {request.alumno_id}")
        
        perfil = AlumnosGRPCClient.obtener_datos_alumno(request.alumno_id)
        if not perfil:
            print(f"[-] Error: No se pudo obtener el correo del alumno {request.alumno_id} desde MS-3")
            return pb2.BoolResponse(success=False)

        clave_temporal = str(uuid.uuid4())[:8].upper()

        def procesar_bienvenida():
            send_academic_email(
                template_name='bienvenida',
                context={
                    'materia_id': request.materia_id, 
                    'clave_acceso': clave_temporal,
                    'alumno_id': request.alumno_id,
                    'nombre_alumno': perfil['nombre']
                },
                to_email=perfil['email'],
                subject='¡Bienvenido al Sistema AGM!',
                tipo='bienvenida'
            )
        threading.Thread(target=procesar_bienvenida).start()
        return pb2.BoolResponse(success=True)

    def SendBajaNotif(self, request, context):
        print(f"[gRPC] Solicitud de Baja: Alumno {request.alumno_id} con Docente {request.docente_id}")
        
        alumno = AlumnosGRPCClient.obtener_datos_alumno(request.alumno_id)
        docente = AlumnosGRPCClient.obtener_datos_docente(request.docente_id)
        
        if not alumno or not docente:
            print("[-] Error: Datos incompletos desde MS-3 para procesar la baja.")
            return pb2.BoolResponse(success=False)

        def procesar_baja():
            send_academic_email(
                template_name='baja',
                context={
                    'alumno_id': request.alumno_id, 
                    'nombre_alumno': alumno['nombre'],
                    'nombre_docente': docente['nombre']
                },
                to_email=docente['email'],
                subject='Aviso de Baja de Alumno',
                tipo='baja'
            )
            
        threading.Thread(target=procesar_baja).start()
        return pb2.BoolResponse(success=True)

    def SendCierreMateria(self, request, context):
        print(f"[gRPC] Petición masiva de Cierre de Materia: {request.materia_id}")
        
        alumnos_inscritos = AlumnosGRPCClient.obtener_lista_grupo(request.materia_id)
        
        if not alumnos_inscritos:
            print(f"[-] Grupo vacío o MS-3 desconectado para la materia {request.materia_id}.")
            return pb2.BoolResponse(success=False)

        # Definimos el trabajo pesado en una función interna
        def procesar_envio_masivo(lista_alumnos, id_materia):
            for alumno in lista_alumnos:
                send_academic_email(
                    template_name='cierre-materia',
                    context={'materia_id': id_materia, 'nombre_alumno': alumno['nombre']},
                    to_email=alumno['email'],
                    subject='Calificaciones Finales Publicadas',
                    tipo='cierre'
                )
            print(f"[+] Envío masivo completado para {len(lista_alumnos)} alumnos.")

        # Disparamos el hilo en segundo plano (Background Task)
        hilo = threading.Thread(target=procesar_envio_masivo, args=(alumnos_inscritos, request.materia_id))
        hilo.start()

        # Retornamos éxito INMEDIATAMENTE para no bloquear la red gRPC
        return pb2.BoolResponse(success=True)

def serve():
    # Inicializamos el servidor multihilo
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_NotificacionesServiceServicer_to_server(NotificacionesServicer(), server)
    
    # Puerto asignado para MS-6 Notificaciones
    port = os.environ.get('GRPC_PORT', '50056')
    server.add_insecure_port(f'[::]:{port}')
    print(f"Servidor gRPC de Notificaciones (MS-6) escuchando en puerto {port}")
    
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()