import sys
import os
import grpc

# 🎯 Absolute Path Fix: Force python to see the source root
current_dir = os.path.dirname(os.path.abspath(__file__))
# Back up to the 'src' directory level
src_path = os.path.abspath(os.path.join(current_dir, ".."))
if src_path not in sys.path:
    sys.path.append(src_path)

# 🎯 Now you can use clean, direct absolute imports with no relative dots!
try:
    from grpc import alumnos_pb2
    from grpc import alumnos_pb2_grpc
except ImportError:
    # Fallback in case your stubs folder is named exactly 'grpc' inside src
    from grpc import alumnos_pb2  # Change 'grpc_folder' to whatever your folder is called (e.g. 'grpc' or 'stubs')
    from grpc import alumnos_pb2_grpc

def run_test():
    # 🎯 2. Target your local host port for MS-3 (Alumnos/Docentes)
    # Check your docker-compose.yml for ms-alumnos gRPC mapping. It's usually 50053 or 50052.
    grpc_target = "localhost:50053" 
    
    print(f"🛰️ Opening direct gRPC channel to {grpc_target}...")
    channel = grpc.insecure_channel(grpc_target)
    stub = alumnos_pb2_grpc.AlumnosServiceStub(channel) # or DocentesServiceStub depending on your proto service name

    # The string layout test parameters
    test_name = "SANCHEZ ROMAN GUILLERMINA"
    print(f"🕵️ Sending name string token: '{test_name}'")

    try:
        # 🎯 3. Package the request matching the proto signature parameters
        request = alumnos_pb2.DocenteNameRequest(nombre_completo=test_name) # Ensure request type matches proto definition
        
        # Fire the execution thread!
        response = stub.GetDocenteByName(request, timeout=5)
        
        print("\n🟢 SUCCESS! gRPC Server responded with real records:")
        print(f"  - UUID ID: {response.id}")
        print(f"  - Full Name: {response.nombre_completo}")
        print(f"  - Email: {response.correo_institucional}")
        print(f"  - Cubicle: {response.cubiculo}")

    except grpc.RpcError as e:
        print(f"\n🔴 CRASHED: gRPC request was explicitly rejected!")
        print(f"  - Status Code: {e.code()}")
        print(f"  - Error Details: {e.details()}")

if __name__ == "__main__":
    run_test()