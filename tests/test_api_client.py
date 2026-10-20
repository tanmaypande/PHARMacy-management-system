import pytest
import requests
from app.client.api_client import APIClient


def test_api_client_initialization():
    client = APIClient(base_url="http://127.0.0.1:8000")
    assert client.base_url == "http://127.0.0.1:8000"
    assert client.timeout == 5.0

    client.set_auth_token("test-jwt-token")
    headers = client._headers()
    assert headers["Authorization"] == "Bearer test-jwt-token"
    assert headers["Content-Type"] == "application/json"


def test_api_client_error_handling_structure():
    client = APIClient(base_url="http://127.0.0.1:9999")  # Non-existent port
    health = client.get_health()
    assert health["status"] == "error"
    assert health["api_service"] == "offline"
    assert health["database"]["database_connected"] is False
