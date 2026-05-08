"""
MS-3: Docentes & Alumnos — Punto de entrada de la aplicacion FastAPI
"""

import threading
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.config.database import engine
from src.models import Base
from src.routes import docentes, alumnos
from src.grpc.server import crear_servidor_grpc

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: ejecuta codigo al iniciar y al apagar la aplicacion
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    # Crear tablas automaticamente (en produccion se usaria Alembic)
    Base.metadata.create_all(bind=engine)
    logger.info(f"MS-3 Docentes & Alumnos iniciado en puerto {settings.REST_PORT}")
    logger.info(f"Base de datos: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

    # Iniciar servidor gRPC en un hilo separado
    grpc_server = crear_servidor_grpc(settings.GRPC_PORT)
    grpc_server.start()
    logger.info(f"Servidor gRPC escuchando en puerto {settings.GRPC_PORT}")

    yield

    # --- Shutdown ---
    logger.info("Deteniendo servidor gRPC...")
    grpc_server.stop(grace=5)
    logger.info("MS-3 Docentes & Alumnos detenido")


# ---------------------------------------------------------------------------
# Aplicacion FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(
    title="MS-3 - Docentes & Alumnos",
    description="Microservicio de gestion de docentes y alumnos del sistema AGM",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
app.include_router(docentes.router, prefix="/docentes", tags=["Docentes"])
app.include_router(alumnos.router, prefix="/alumnos", tags=["Alumnos"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Sistema"])
def health_check():
    """Endpoint de salud para verificar que el servicio esta activo."""
    return {
        "success": True,
        "data": {
            "service": "ms-alumnos",
            "status": "healthy",
            "version": "1.0.0",
            "ports": {
                "rest": settings.REST_PORT,
                "grpc": settings.GRPC_PORT,
            },
        },
        "message": "MS-3 Docentes & Alumnos operativo",
    }
