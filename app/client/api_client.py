import requests
from typing import Dict, Any, Optional

class APIClient:
    """
    Dedicated HTTP client for the CustomTkinter desktop interface.
    Ensures the UI never accesses the database or business services directly.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 4.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.auth_token: Optional[str] = None

    def set_auth_token(self, token: str):
        """Stores the JWT token for authenticated requests."""
        self.auth_token = token

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    def get_health(self) -> Dict[str, Any]:
        """
        Calls the backend /health endpoint to check both API and PostgreSQL status.
        """
        url = f"{self.base_url}/health"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
            # Both 200 (healthy) and 503 (database degraded) return JSON diagnostic payloads
            if response.status_code in (200, 503):
                return response.json()
            return {
                "status": "error",
                "api_service": "unreachable",
                "database": {"database_connected": False, "message": f"HTTP {response.status_code}"}
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "api_service": "offline",
                "database": {"database_connected": False, "message": "Backend API server is not running"}
            }
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "api_service": "timeout",
                "database": {"database_connected": False, "message": "Backend API request timed out"}
            }
        except Exception as exc:
            return {
                "status": "error",
                "api_service": "unknown_error",
                "database": {"database_connected": False, "message": str(exc)}
            }
