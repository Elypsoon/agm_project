"""
Configuración de la base de datos — SQLAlchemy engine y sesión.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.config.settings import settings

# ---------------------------------------------------------------------------
# Engine (pool de conexiones a PostgreSQL)
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verifica que la conexión sigue viva antes de usarla
)

# ---------------------------------------------------------------------------
# SessionLocal — fábrica de sesiones
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Dependency para FastAPI: obtener sesión por request
# ---------------------------------------------------------------------------
def get_db() -> Session:
    """
    Generador que proporciona una sesión de BD por cada request HTTP.
    Se cierra automáticamente al finalizar.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
