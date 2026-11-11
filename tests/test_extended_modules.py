import pytest
from fastapi.testclient import TestClient
from app.main_api import app
from app.services.auth_service import hash_password, verify_password

client = TestClient(app)


def test_password_hashing():
    pwd = "secret_password_123"
    h = hash_password(pwd)
    assert h != pwd
    assert verify_password(pwd, h) is True
    assert verify_password("wrong_password", h) is False


def test_auth_login_endpoint():
    # Login with default seeded admin credentials
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "admin"


def test_auth_invalid_credentials():
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert resp.status_code == 401


def test_create_and_list_users():
    import uuid
    uname = f"cashier_{uuid.uuid4().hex[:6]}"
    resp = client.post("/api/v1/auth/users", json={
        "username": uname,
        "password": "pass1234",
        "full_name": "Test Cashier",
        "role": "cashier"
    })
    assert resp.status_code == 200
    user_data = resp.json()
    assert user_data["username"] == uname
    assert user_data["role"] == "cashier"

    # Verify in list
    list_resp = client.get("/api/v1/auth/users")
    assert list_resp.status_code == 200
    users = list_resp.json()
    assert any(u["username"] == uname for u in users)


def test_supplier_crud():
    import uuid
    name = f"Distributor {uuid.uuid4().hex[:6]}"
    create_resp = client.post("/api/v1/suppliers", json={
        "name": name,
        "contact_person": "Mr. Vendor",
        "phone": "+91 99999 11111",
        "email": "vendor@test.com"
    })
    assert create_resp.status_code == 200
    sup_id = create_resp.json()["id"]

    # List & Search
    list_resp = client.get(f"/api/v1/suppliers?search={name[:6]}")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # Delete
    del_resp = client.delete(f"/api/v1/suppliers/{sup_id}")
    assert del_resp.status_code == 200


def test_customer_crud():
    import uuid
    name = f"Patient {uuid.uuid4().hex[:6]}"
    phone = f"98765{uuid.uuid4().hex[:5]}"
    create_resp = client.post("/api/v1/customers", json={
        "name": name,
        "phone": phone,
        "email": "patient@example.com"
    })
    assert create_resp.status_code == 200
    cust_id = create_resp.json()["id"]

    # Search
    list_resp = client.get(f"/api/v1/customers?search={name[:6]}")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # Delete
    del_resp = client.delete(f"/api/v1/customers/{cust_id}")
    assert del_resp.status_code == 200


def test_prescriptions_flow():
    import uuid
    cust_resp = client.post("/api/v1/customers", json={
        "name": f"Rx Patient {uuid.uuid4().hex[:6]}",
        "phone": "9998887776"
    })
    cust_id = cust_resp.json()["id"]

    # Create Rx
    rx_resp = client.post("/api/v1/prescriptions", json={
        "customer_id": cust_id,
        "doctor_name": "Dr. Sharma",
        "diagnosis": "Seasonal Viral",
        "notes": "Paracetamol 500mg TDS"
    })
    assert rx_resp.status_code == 200
    rx_id = rx_resp.json()["id"]

    # List Rx for customer
    rx_list = client.get(f"/api/v1/prescriptions?customer_id={cust_id}")
    assert rx_list.status_code == 200
    assert len(rx_list.json()) == 1

    # Cleanup
    client.delete(f"/api/v1/prescriptions/{rx_id}")
    client.delete(f"/api/v1/customers/{cust_id}")


def test_reports_and_analytics():
    rep_resp = client.get("/api/v1/reports/sales-summary?days=30")
    assert rep_resp.status_code == 200
    data = rep_resp.json()
    assert "total_revenue" in data
    assert "total_profit" in data
    assert "daily_trend" in data

    val_resp = client.get("/api/v1/reports/inventory-valuation")
    assert val_resp.status_code == 200
    val_data = val_resp.json()
    assert "total_cost_value" in val_data
    assert "total_retail_value" in val_data


def test_store_settings_and_backup():
    # Save settings
    set_resp = client.post("/api/v1/reports/settings", json={
        "settings": {
            "store_name": "MediCare Premier Pharmacy",
            "store_gstin": "GSTIN-TEST-290011"
        }
    })
    assert set_resp.status_code == 200

    # Get settings
    get_resp = client.get("/api/v1/reports/settings")
    assert get_resp.status_code == 200
    assert get_resp.json().get("store_name") == "MediCare Premier Pharmacy"

    # Backup
    bak_resp = client.post("/api/v1/reports/backup")
    assert bak_resp.status_code == 200
    assert bak_resp.json().get("success") is True


def test_pdf_invoice_generation():
    import os
    from app.utils.pdf_utils import generate_invoice_pdf
    sample_sale = {
        "invoice_number": "INV-TEST-0001",
        "customer_name": "John Doe",
        "customer_phone": "+91 98765 43210",
        "payment_method": "Cash",
        "subtotal": 150.00,
        "discount_amount": 10.00,
        "tax_amount": 7.00,
        "total_amount": 147.00,
        "items": [
            {
                "medicine_name": "Paracetamol 500mg",
                "batch_number": "BATCH-001",
                "quantity": 2,
                "unit_price": 75.00,
                "subtotal": 150.00
            }
        ]
    }
    out_pdf = "tests/test_invoice.pdf"
    res_path = generate_invoice_pdf(sample_sale, out_pdf)
    assert os.path.exists(res_path)
    assert os.path.getsize(res_path) > 1000
    if os.path.exists(res_path):
        os.remove(res_path)
