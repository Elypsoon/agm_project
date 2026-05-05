"""
MS-2: Periodos & Materias
FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import threading
import logging

from src.config import (
    DEBUG,
    ENVIRONMENT,
    CORS_ORIGINS,
    SERVICE_NAME,
    SERVICE_VERSION,
)
from src.database import create_all_tables
from src.routes import periodos, materias
from src.grpc.server import serve

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting MS-2: Periodos & Materias")
    create_all_tables()
    logger.info("Database tables created")
    
    # Start gRPC server in background thread
    def run_grpc_server():
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(serve())
        except Exception as e:
            logger.error(f"Error in gRPC server: {e}")
    
    grpc_thread = threading.Thread(target=run_grpc_server, daemon=True)
    grpc_thread.start()
    logger.info("gRPC server started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MS-2")


# Create FastAPI app
app = FastAPI(
    title=SERVICE_NAME,
    version=SERVICE_VERSION,
    description="Microservicio de Periodos y Materias",
    debug=DEBUG,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "environment": ENVIRONMENT,
    }


# Include routers
app.include_router(periodos.router)
app.include_router(materias.router)


# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {SERVICE_NAME}",
        "version": SERVICE_VERSION,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    from src.config import REST_HOST, REST_PORT
    
    uvicorn.run(
        "src.main:app",
        host=REST_HOST,
        port=REST_PORT,
        reload=DEBUG,
    )
