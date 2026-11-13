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
        headers = {
            "Content-Type": "application/json",
            "Connection": "close"
        }
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
    def list_categories(self, skip: int = 0, limit: int = 1000) -> List[Dict[str, Any]]:
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
        limit: int = 500
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

    def delete_medicine(self, medicine_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/medicines/{medicine_id}/hard"
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

    # Point of Sale & Dispensing Billing
    def create_sale(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/sales"
        res = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def list_sales(self, limit: int = 1000, offset: int = 0, search: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/sales?limit={limit}&offset={offset}"
        if search:
            url += f"&search={requests.utils.quote(search)}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def get_sale(self, sale_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/sales/{sale_id}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def get_sale_by_invoice(self, invoice_number: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/sales/invoice/{invoice_number}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def get_today_sales_summary(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/sales/summary/today"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def get_available_batches_for_sale(self, medicine_id: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/sales/batches/available"
        if medicine_id:
            url += f"?medicine_id={medicine_id}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def return_sale(self, sale_id: str, reason: str = "Customer Return") -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/sales/{sale_id}/return?reason={requests.utils.quote(reason)}"
        res = requests.post(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    # Auth & Users
    def login(self, username: str, password: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/auth/login"
        res = requests.post(url, json={"username": username, "password": password}, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def list_users(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/auth/users"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def create_user(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/auth/users"
        res = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def toggle_user_active(self, user_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/auth/users/{user_id}/toggle-active"
        res = requests.put(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    # Suppliers
    def list_suppliers(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/suppliers"
        if search:
            url += f"?search={requests.utils.quote(search)}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def create_supplier(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/suppliers"
        res = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def update_supplier(self, supplier_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/suppliers/{supplier_id}"
        res = requests.put(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def delete_supplier(self, supplier_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/suppliers/{supplier_id}"
        res = requests.delete(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    # Customers
    def list_customers(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/customers"
        if search:
            url += f"?search={requests.utils.quote(search)}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def create_customer(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/customers"
        res = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def update_customer(self, customer_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/customers/{customer_id}"
        res = requests.put(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def delete_customer(self, customer_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/customers/{customer_id}"
        res = requests.delete(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    # Purchases
    def list_purchases(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/purchases"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def create_purchase(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/purchases"
        res = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    # Prescriptions
    def list_prescriptions(self, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/prescriptions"
        if customer_id:
            url += f"?customer_id={customer_id}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def create_prescription(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/prescriptions"
        res = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def delete_prescription(self, prescription_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/prescriptions/{prescription_id}"
        res = requests.delete(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    # Reports, Settings & Backup
    def get_sales_report(self, days: int = 30) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/reports/sales-summary?days={days}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def get_inventory_valuation(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/reports/inventory-valuation"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def export_sales_csv(self, days: int = 30) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/reports/export-sales-csv?days={days}"
        res = requests.post(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def create_backup(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/reports/backup"
        res = requests.post(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def get_store_settings(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/reports/settings"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def update_store_settings(self, settings_dict: Dict[str, str]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/reports/settings"
        res = requests.post(url, json={"settings": settings_dict}, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    # TQM Quality Management
    def list_tqm_records(self, category: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/tqm/records"
        params = []
        if category:
            params.append(f"category={requests.utils.quote(category)}")
        if status:
            params.append(f"status={requests.utils.quote(status)}")
        if params:
            url += "?" + "&".join(params)
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def create_tqm_record(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/tqm/records"
        res = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def update_tqm_record(self, record_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/tqm/records/{record_id}"
        res = requests.put(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def delete_tqm_record(self, record_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/tqm/records/{record_id}"
        res = requests.delete(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def get_tqm_kpis(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/tqm/kpis"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    # Policies & SOPs
    def list_policies(self, search: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/policies"
        params = []
        if search:
            params.append(f"search={requests.utils.quote(search)}")
        if category:
            params.append(f"category={requests.utils.quote(category)}")
        if params:
            url += "?" + "&".join(params)
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def create_policy(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/policies"
        res = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def update_policy(self, policy_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/policies/{policy_id}"
        res = requests.put(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def delete_policy(self, policy_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/policies/{policy_id}"
        res = requests.delete(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    # ================= 1. Super Admin Panel Client =================
    def get_super_admin_dashboard(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/super-admin/dashboard"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def list_pharmacies(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/super-admin/pharmacies"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def register_pharmacy(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/super-admin/pharmacies"
        res = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def toggle_pharmacy_status(self, pharmacy_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/super-admin/pharmacies/{pharmacy_id}/toggle-status"
        res = requests.put(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def list_subscriptions(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/super-admin/subscriptions"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def list_support_tickets(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/super-admin/support-tickets"
        if status and status != "All":
            url += f"?status={status}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def reply_support_ticket(self, ticket_id: str, response: str, status: str = "Resolved") -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/super-admin/support-tickets/{ticket_id}/reply"
        res = requests.put(url, json={"response": response, "status": status}, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def get_super_admin_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/super-admin/audit-logs?limit={limit}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    # ================= 2. Pharmacy Owner Panel Client =================
    def get_owner_dashboard(self, pharmacy_id: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/owner/dashboard"
        if pharmacy_id:
            url += f"?pharmacy_id={pharmacy_id}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def list_expenses(self, pharmacy_id: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/owner/expenses"
        params = []
        if pharmacy_id:
            params.append(f"pharmacy_id={pharmacy_id}")
        if category and category != "All":
            params.append(f"category={category}")
        if params:
            url += "?" + "&".join(params)
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def add_expense(self, category: str, amount: float, description: str, pharmacy_id: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/owner/expenses"
        payload = {"category": category, "amount": amount, "description": description, "pharmacy_id": pharmacy_id}
        res = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def delete_expense(self, expense_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/owner/expenses/{expense_id}"
        res = requests.delete(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def get_profit_and_loss(self, pharmacy_id: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/owner/profit-loss"
        if pharmacy_id:
            url += f"?pharmacy_id={pharmacy_id}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def get_pharmacy_profile(self, pharmacy_id: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/owner/profile"
        if pharmacy_id:
            url += f"?pharmacy_id={pharmacy_id}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def update_pharmacy_profile(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/owner/profile"
        res = requests.put(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    # ================= 3. Pharmacist Panel Client =================
    def get_pharmacist_dashboard(self, pharmacy_id: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/pharmacist/dashboard"
        if pharmacy_id:
            url += f"?pharmacy_id={pharmacy_id}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def list_pharmacist_prescriptions(self, pharmacy_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/pharmacist/prescriptions"
        params = []
        if pharmacy_id:
            params.append(f"pharmacy_id={pharmacy_id}")
        if status and status != "All":
            params.append(f"status={status}")
        if params:
            url += "?" + "&".join(params)
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def verify_prescription(self, prescription_id: str, dispensing_notes: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/pharmacist/prescriptions/{prescription_id}/verify"
        res = requests.post(url, json={"dispensing_notes": dispensing_notes}, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def reject_prescription(self, prescription_id: str, reason: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/pharmacist/prescriptions/{prescription_id}/reject"
        res = requests.post(url, json={"reason": reason}, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def dispense_prescription(self, prescription_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/pharmacist/prescriptions/{prescription_id}/dispense"
        res = requests.post(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def get_patient_medication_history(self, customer_id: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/pharmacist/patient-history/{customer_id}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    # ================= 4 & 5. Purchase Orders & Inventory =================
    def list_purchase_orders(self, pharmacy_id: Optional[str] = None, supplier_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/purchase-orders"
        params = []
        if pharmacy_id:
            params.append(f"pharmacy_id={pharmacy_id}")
        if supplier_id:
            params.append(f"supplier_id={supplier_id}")
        if status and status != "All":
            params.append(f"status={status}")
        if params:
            url += "?" + "&".join(params)
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def create_purchase_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/purchase-orders"
        res = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def get_purchase_order_details(self, po_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/purchase-orders/{po_id}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def receive_purchase_order_goods(self, po_id: str, batches: List[Dict[str, Any]]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/purchase-orders/{po_id}/receive"
        res = requests.post(url, json={"batches": batches}, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def adjust_inventory_stock(self, batch_id: str, new_quantity: int, reason: str, pharmacy_id: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/purchase-orders/inventory/adjust"
        payload = {"batch_id": batch_id, "new_quantity": new_quantity, "reason": reason, "pharmacy_id": pharmacy_id}
        res = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def list_stock_movements(self, pharmacy_id: Optional[str] = None, batch_id: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/purchase-orders/inventory/movements"
        params = []
        if pharmacy_id:
            params.append(f"pharmacy_id={pharmacy_id}")
        if batch_id:
            params.append(f"batch_id={batch_id}")
        if params:
            url += "?" + "&".join(params)
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    # ================= 6. Supplier Portal Client =================
    def get_supplier_portal_dashboard(self, supplier_id: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/supplier-portal/dashboard"
        if supplier_id:
            url += f"?supplier_id={supplier_id}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def list_supplier_portal_orders(self, supplier_id: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/supplier-portal/orders"
        if supplier_id:
            url += f"?supplier_id={supplier_id}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def respond_supplier_order(self, po_id: str, status: str, quotation_notes: str = "") -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/supplier-portal/orders/{po_id}/respond"
        res = requests.post(url, json={"status": status, "quotation_notes": quotation_notes}, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def get_supplier_catalog(self, supplier_id: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/supplier-portal/catalog"
        if supplier_id:
            url += f"?supplier_id={supplier_id}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def get_supplier_payment_ledger(self, supplier_id: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/supplier-portal/payments"
        if supplier_id:
            url += f"?supplier_id={supplier_id}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    # ================= 7. Customer / Patient Portal Client =================
    def register_patient_account(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/customer-portal/register"
        res = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def get_customer_dashboard(self, customer_id: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/customer-portal/dashboard"
        if customer_id:
            url += f"?customer_id={customer_id}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def get_customer_catalog(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/customer-portal/catalog"
        if search:
            url += f"?search={requests.utils.quote(search)}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def upload_patient_prescription(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/customer-portal/prescriptions"
        res = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def list_my_prescriptions(self, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/customer-portal/prescriptions"
        if customer_id:
            url += f"?customer_id={customer_id}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def list_my_orders(self, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/v1/customer-portal/orders"
        if customer_id:
            url += f"?customer_id={customer_id}"
        res = requests.get(url, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)

    def submit_customer_support_ticket(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/customer-portal/support"
        res = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout)
        return self._handle_response(res)


