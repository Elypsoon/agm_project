import grpc
from concurrent import futures
import os
import django
import sys

# Configuración de rutas de módulos.
# El servidor gRPC se ejecuta fuera del proceso de Django, por lo que
# es necesario registrar manualmente las rutas antes de cualquier importación.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)                                      # Raíz del proyecto (encuentra 'src').
sys.path.append(os.path.join(BASE_DIR, 'src', 'grpc'))        # Archivos generados por protoc.

# Inicializar Django antes de importar modelos ORM.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.config.settings')
django.setup()

# Importar los stubs generados por protoc a partir de auth.proto.
import auth_pb2
import auth_pb2_grpc

# Importar modelos y utilidades de autenticación.
from src.models.models import User
from rest_framework_simplejwt.tokens import AccessToken

class AuthService(auth_pb2_grpc.AuthServiceServicer):
    def ValidateToken(self, request, context):
        try:
            # Decodifica el token y extrae el user_id del payload.
            token = AccessToken(request.access_token)
            user_id = token['user_id']

            # Confirmar que el usuario exista y esté activo en la base de datos.
            user = User.objects.get(id=user_id)

            return auth_pb2.ValidateTokenResponse(
                valid=True,
                user_id=str(user.id),
                email=user.email,
                role=user.role
            )
        except Exception as e:
            print(f"Error en validación: {e}")
            return auth_pb2.ValidateTokenResponse(valid=False, error=str(e))

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthService(), server)
    server.add_insecure_port('[::]:50051')
    print("🚀 Servidor gRPC de AGM listo en el puerto 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()