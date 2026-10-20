import requests
from typing import Dict, Any, List, Optional
import uuid


class APIClient:
    """
    Dedicated HTTP client for the CustomTkinter desktop interface.
    Ensures the UI NEVER connects directly to PostgreSQL or executes SQL.
    All business rules, validations, and ACID database operations
    are delegated to the FastAPI backend service over HTTP.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.auth_token: Optional[str] = None

    def set_auth_token(self, token: str):
        self.auth_token = token

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    def _handle_response(self, response: requests.Response) -> Any:
        if response.status_code in (200, 201):
            return response.json()
        elif response.status_code == 204:
            return True
        else:
            try:
                error_detail = response.json().get("detail", response.text)
            except Exception:
                error_detail = response.text
            raise RuntimeError(f"API Error ({response.status_code}): {error_detail}")

    # Health & System
    def get_health(self) -> Dict[str, Any]:
        url = f"{self.base_url}/health"
        try:
            response = requests.get(url, headers=self._headers(), timeout=self.timeout)
            if response.status_code in (200, 503):
                return response.json()
            return {"status": "error", "api_service": "unreachable", "database": {"database_connected": False}}
        except Exception as exc:
            return {"status": "error", "api_service": "offline", "database": {"database_connected": False, "message": str(exc)}}

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/dashboard/metrics"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    # Categories
    def list_categories(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/categories?skip={skip}&limit={limit}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def create_category(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/categories"
        payload = {"name": name, "description": description}
        res = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def update_category(self, category_id: str, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/categories/{category_id}"
        payload = {"name": name, "description": description}
        res = requests.put(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def delete_category(self, category_id: str) -> bool:
        url = f"{self.base_url}/api/v1/categories/{category_id}"
        res = requests.delete(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    # Medicines
    def list_medicines(
        self,
        search: Optional[str] = None,
        category_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        params = [f"skip={skip}", f"limit={limit}"]
        if search:
            params.append(f"search={requests.utils.quote(search)}")
        if category_id:
            params.append(f"category_id={category_id}")
        if is_active is not None:
            params.append(f"is_active={'true' if is_active else 'false'}")

        query_str = "&".join(params)
        url = f"{self.base_url}/api/v1/medicines?{query_str}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def get_medicine(self, medicine_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/medicines/{medicine_id}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def create_medicine(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/medicines"
        res = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def update_medicine(self, medicine_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/medicines/{medicine_id}"
        res = requests.put(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def deactivate_medicine(self, medicine_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/medicines/{medicine_id}"
        res = requests.delete(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    # Batches (Inventory)
    def list_batches(self, medicine_id: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/batches"
        if medicine_id:
            url += f"?medicine_id={medicine_id}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def create_batch(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/batches"
        res = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def list_expiring_soon(self, days: int = 30) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/batches/expiring-soon?days={days}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)
