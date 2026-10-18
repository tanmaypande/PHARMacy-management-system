from fastapi.testclient import TestClient
from app.main_api import app
from app.core.database import check_database_health

client = TestClient(app)

def test_health_endpoint_contract():
    """
    Verifies that the /health endpoint adheres to our monitoring contract.
    Ensures that no database passwords or credentials are leaked in the payload.
    """
    response = client.get("/health")
    # Endpoint returns 200 if DB is reachable or 503 if DB is unreachable
    assert response.status_code in (200, 503)
    
    data = response.json()
    assert "status" in data
    assert "api_service" in data
    assert data["api_service"] == "running"
    assert "database" in data
    assert "database_connected" in data["database"]
    assert "message" in data["database"]

    # Security verification: Ensure raw credentials are never exposed
    payload_str = response.text.lower()
    assert "password" not in payload_str
    assert "postgresql://" not in payload_str
    assert "postgresql+psycopg://" not in payload_str

def test_check_database_health_isolated():
    """
    Directly tests the check_database_health() function.
    Must return a structured dictionary containing 'database_connected' and 'message'.
    """
    result = check_database_health()
    assert isinstance(result, dict)
    assert "database_connected" in result
    assert isinstance(result["database_connected"], bool)
    assert "message" in result
    assert isinstance(result["message"], str)
