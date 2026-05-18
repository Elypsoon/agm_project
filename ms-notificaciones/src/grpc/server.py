import os
import sys
import grpc
from concurrent import futures
import uuid

# 1. Configuración CRÍTICA: Inicializar Django antes de importar modelos
# Esto permite que este script independiente use la BD y settings de Django
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
        print(f"📥 [gRPC] Petición de Bienvenida recibida para alumno ID: {request.alumno_id}")
        
        # En el flujo real, aquí harías otra llamada gRPC al MS-3 para obtener el correo del alumno.
        # Por ahora usaremos un correo de prueba de tu configuración SMTP.
        to_email = "alumno_prueba@buap.mx" 
        clave_temporal = str(uuid.uuid4())[:8].upper()

        success = send_academic_email(
            template_name='bienvenida',
            context={'materia_id': request.materia_id, 'clave_acceso': clave_temporal},
            to_email=to_email,
            subject='¡Bienvenido al Sistema AGM!',
            tipo='bienvenida'
        )
        return pb2.BoolResponse(success=success)

    def SendBajaNotif(self, request, context):
        print(f"📥 [gRPC] Petición de Baja recibida para alumno ID: {request.alumno_id}")
        to_email = "docente_prueba@buap.mx"
        
        success = send_academic_email(
            template_name='baja',
            context={'alumno_id': request.alumno_id},
            to_email=to_email,
            subject='Aviso de Baja de Alumno',
            tipo='baja'
        )
        return pb2.BoolResponse(success=success)

    def SendCierreMateria(self, request, context):
        print(f"📥 [gRPC] Petición de Cierre recibida para materia ID: {request.materia_id}")
        to_email = "grupo_prueba@buap.mx"
        
        success = send_academic_email(
            template_name='cierre-materia',
            context={'materia_id': request.materia_id},
            to_email=to_email,
            subject='Calificaciones Finales Publicadas',
            tipo='cierre'
        )
        return pb2.BoolResponse(success=success)

def serve():
    # Inicializamos el servidor multihilo
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_NotificacionesServiceServicer_to_server(NotificacionesServicer(), server)
    
    # Puerto asignado para MS-6 Notificaciones
    port = os.environ.get('GRPC_PORT', '50056')
    server.add_insecure_port(f'[::]:{port}')
    print(f"🚀 Servidor gRPC de Notificaciones (MS-6) escuchando en puerto {port}")
    
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()