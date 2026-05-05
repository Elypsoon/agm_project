import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/agm_periodos_db"
)

# FastAPI Settings
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# gRPC Settings
GRPC_PORT = int(os.getenv("GRPC_PORT", 50052))
GRPC_HOST = os.getenv("GRPC_HOST", "0.0.0.0")

# REST API Settings
REST_PORT = int(os.getenv("REST_PORT", 3002))
REST_HOST = os.getenv("REST_HOST", "0.0.0.0")

# CORS
CORS_ORIGINS = [
    "http://localhost:4200",  # Angular Frontend
    # El resto de micorservicios
]

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Service naming
SERVICE_NAME = "ms-periodos"
SERVICE_VERSION = "1.0.0"
