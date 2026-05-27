import sys
import os

# 🎯 1. Calculate the absolute path to your local 'src/grpc' folder
current_dir = os.path.dirname(os.path.abspath(__file__))
# Back up to 'src' and go into 'grpc'
grpc_folder_path = os.path.abspath(os.path.join(current_dir, "..", "grpc"))

# 🎯 2. Inject it at the absolute front of Python's search paths (Index 0)
# This forces Python to look inside YOUR folder before checking global site-packages!
if grpc_folder_path not in sys.path:
    sys.path.insert(0, grpc_folder_path)

# 🎯 3. Now import the files directly by their file names!
try:
    import alumnos_pb2
    import alumnos_pb2_grpc
    print("🟢 gRPC Stub compilation files linked successfully!")
except ImportError as e:
    print(f"🔴 Couldn't find files in: {grpc_folder_path}")
    print(f"Error details: {e}")
    sys.exit(1)

# Now import the core library under an alias so there's zero naming confusion
import grpc as official_grpc

def run_test():
    # 🎯 2. Target your local host port for MS-3 (Alumnos/Docentes)
    # Check your docker-compose.yml for ms-alumnos gRPC mapping. It's usually 50053 or 50052.
    grpc_target = "localhost:50053" 
    
    print(f"🛰️ Opening direct gRPC channel to {grpc_target}...")
    channel = official_grpc.insecure_channel(grpc_target)
    stub = alumnos_pb2_grpc.AlumnosServiceStub(channel) # or DocentesServiceStub depending on your proto service name

    # The string layout test parameters
    test_name = "SANCHEZ ROMAN GUILLERMINA"
    print(f"🕵️ Sending name string token: '{test_name}'")

    try:
        # 🎯 3. Package the request matching the proto signature parameters
        request = alumnos_pb2.GetDocenteByNameRequest(nombre_completo=test_name) # Ensure request type matches proto definition
        
        # Fire the execution thread!
        response = stub.GetDocenteByName(request, timeout=5)
        
        print("\n🟢 SUCCESS! gRPC Server responded with real records:")
        print(f"  - UUID ID: {response.id}")
        print(f"  - Full Name: {response.nombre_completo}")
        print(f"  - Email: {response.correo_institucional}")
        print(f"  - Cubicle: {response.cubiculo}")

    except official_grpc.RpcError as e:
        print(f"\n🔴 CRASHED: gRPC request was explicitly rejected!")
        print(f"  - Status Code: {e.code()}")
        print(f"  - Error Details: {e.details()}")

if __name__ == "__main__":
    run_test()