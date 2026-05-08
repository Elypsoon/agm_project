"""
Configuración centralizada — lee variables de entorno con Pydantic Settings.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Todas las variables de entorno del microservicio."""

    # --- Base de datos ---
    DB_HOST: str = "db-alumnos"
    DB_PORT: int = 5432
    DB_NAME: str = "agm_alumnos_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "alumnos_dev_2026"

    # --- Servidor ---
    REST_PORT: int = 3003
    GRPC_PORT: int = 50053

    # --- gRPC a otros microservicios ---
    AUTH_GRPC_HOST: str = "ms-auth"
    AUTH_GRPC_PORT: int = 50051
    NOTIFICACIONES_GRPC_HOST: str = "ms-notificaciones"
    NOTIFICACIONES_GRPC_PORT: int = 50056
    PERIODOS_GRPC_HOST: str = "ms-periodos"
    PERIODOS_GRPC_PORT: int = 50052

    # --- CORS ---
    CORS_ORIGIN: str = "http://localhost:4200"

    @property
    def DATABASE_URL(self) -> str:
        """URL de conexión para SQLAlchemy."""
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instancia global — importar desde aquí
settings = Settings()
