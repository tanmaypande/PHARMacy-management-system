import logging
from typing import Generator, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from app.core.config import settings

logger = logging.getLogger("pharmacy.database")

# SQLAlchemy 2.x Declarative Base class
class Base(DeclarativeBase):
    pass

# Engine configured for PostgreSQL 18 with psycopg 3
# pool_pre_ping=True validates connection liveness before checking out from pool
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=(settings.ENVIRONMENT == "development_debug")
)

# Thread-local session factory for repositories and services
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional database session per request.
    Ensures sessions are cleanly closed when request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_database_health() -> Dict[str, Any]:
    """
    Performs a lightweight connectivity check ('SELECT 1') against PostgreSQL.
    Safely catches connection failures without exposing credentials.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
            if result == 1:
                return {
                    "database_connected": True,
                    "message": "Successfully connected to PostgreSQL database"
                }
            return {
                "database_connected": False,
                "message": "Unexpected query response from database"
            }
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}")
        # Return generic safe error message - never leak password or database URL
        error_type = exc.__class__.__name__
        return {
            "database_connected": False,
            "message": f"Cannot connect to database ({error_type}). Check PostgreSQL service and .env credentials."
        }
