import pytest
from sqlalchemy import text
from app.core.database import engine, check_database_health

def test_sqlalchemy_live_connection():
    """
    Verifies that SQLAlchemy 2.x and psycopg 3 can successfully connect
    to the PostgreSQL 'pharmacy_management' database and execute a basic query.
    """
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar()
        assert result == 1

def test_database_health_helper():
    """
    Verifies that the check_database_health helper reports a connected status
    against the live PostgreSQL instance without raising exceptions.
    """
    health = check_database_health()
    assert health["database_connected"] is True
    assert "Successfully connected" in health["message"]
