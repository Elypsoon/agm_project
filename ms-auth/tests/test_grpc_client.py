import grpc
import sys
import os

# Ajuste dinámico del path de módulos.
# Se sube un nivel desde 'tests/' para llegar a la raíz del servicio
# y desde ahí localizar los stubs generados por protoc.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRPC_FOLDER = os.path.join(BASE_DIR, 'src', 'grpc')
sys.path.append(GRPC_FOLDER)

import auth_pb2
import auth_pb2_grpc

def run_test():
    # Conexión al servidor local; el puerto 50051 debe estar expuesto en Docker.
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = auth_pb2_grpc.AuthServiceStub(channel)

        # Sustituye este valor por un access token válido obtenido desde /docs.
        token_a_probar = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzc4MjMxODI0LCJpYXQiOjE3NzgyMjgyMjQsImp0aSI6IjYzYTUxNWNiYTc0OTQ5Y2VhN2VmZWQ1YTM3ODhhYjZjIiwidXNlcl9pZCI6IjY5MWZiMDVhLWZiNjUtNDk3MC04YWYyLTQ1YzM1NjJlNDVjZiJ9.tNQXOOcBl7-hb839iAHBmNG6T4gsgrg78HRCW9gIBlQ"

        print(f"🛰️  Enviando petición gRPC al puerto 50051...")
        
        try:
            response = stub.ValidateToken(auth_pb2.ValidateTokenRequest(access_token=token_a_probar))
            
            if response.valid:
                print("[AUTH_OK] gRPC respondió correctamente:")
                print(f"Usuario: {response.email}")
                print(f"Rol: {response.role}")
                print(f"UUID: {response.user_id}")
            else:
                print("[AUTH_DENIED] El servidor rechazó el token.")
                print(f"Razón: {response.error}")
                
        except Exception as e:
            print(f"[CONNECTION_ERROR] No se pudo hablar con el servidor: {e}")

if __name__ == '__main__':
    run_test()