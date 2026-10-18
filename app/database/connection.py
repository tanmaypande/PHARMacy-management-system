"""
Canonical database re-export module.
Delegates to app.core.database to ensure a single SQLAlchemy engine
and sessionmaker instance across the entire application.
"""
from app.core.database import Base, engine, SessionLocal, get_db, check_database_health

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "check_database_health"
]
