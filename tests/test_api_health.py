from fastapi.testclient import TestClient
from app.main_api import app

client = TestClient(app)

def test_health_check():
    """Verify the API health check endpoint returns 200 OK and expected JSON."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Pharmacy API is running"}
