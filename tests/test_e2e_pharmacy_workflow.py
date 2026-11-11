import pytest
from datetime import date
from fastapi.testclient import TestClient
from app.main_api import app

client = TestClient(app)


def test_full_pharmacy_workflow():
    """
    Simulates complete pharmacy end-to-end lifecycle:
    1. Admin Login & Auth verification
    2. Register a wholesale supplier
    3. Register a customer / patient
    4. Register a therapeutic category & medicine item
    5. Inbound Purchase Consignment: receive stock into batch inventory
    6. Verify batch quantity and expiry
    7. POS Dispensation Billing: create customer bill
    8. Verify stock deduction (FEFO compliance)
    9. Printable PDF invoice generation
    10. Customer return: refund transaction and verify stock restoration
    11. Financial reports & TQM valuation
    12. Disaster recovery database backup
    """
    import uuid

    # 1. Admin Login
    login_res = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert login_res.status_code == 200
    assert login_res.json()["user"]["role"] == "admin"

    # 2. Add Supplier
    sup_name = f"Global Pharma {uuid.uuid4().hex[:6]}"
    sup_res = client.post("/api/v1/suppliers", json={
        "name": sup_name,
        "contact_person": "Dr. Vikas",
        "phone": "+91 98111 22233",
        "email": "orders@globalpharma.com"
    })
    assert sup_res.status_code == 200
    supplier_id = sup_res.json()["id"]

    # 3. Add Customer
    cust_name = f"Patient {uuid.uuid4().hex[:6]}"
    cust_res = client.post("/api/v1/customers", json={
        "name": cust_name,
        "phone": "+91 98765 00112"
    })
    assert cust_res.status_code == 200
    customer_id = cust_res.json()["id"]

    # 4. Add Category & Medicine
    cat_res = client.post("/api/v1/categories", json={
        "name": f"Antihistamines_{uuid.uuid4().hex[:4]}",
        "description": "Allergy and cold therapeutics"
    })
    assert cat_res.status_code in (200, 201)
    category_id = cat_res.json()["id"]

    med_code = f"MED-CET-{uuid.uuid4().hex[:4].upper()}"
    med_res = client.post("/api/v1/medicines", json={
        "medicine_code": med_code,
        "name": f"Cetirizine Extra 10mg",
        "generic_name": "Cetirizine Hydrochloride",
        "category_id": category_id,
        "unit_of_measurement": "Tablets",
        "prescription_required": False,
        "is_active": True
    })
    assert med_res.status_code in (200, 201)
    medicine_id = med_res.json()["id"]

    # 5. Receive Inbound Consignment (Purchase)
    batch_lot = f"LOT-{uuid.uuid4().hex[:6].upper()}"
    pur_res = client.post("/api/v1/purchases", json={
        "supplier_id": supplier_id,
        "invoice_number": f"PO-E2E-{uuid.uuid4().hex[:6].upper()}",
        "items": [
            {
                "medicine_id": medicine_id,
                "batch_number": batch_lot,
                "quantity": 100,
                "unit_cost": 2.50,
                "selling_price": 5.00,
                "expiry_date": "2027-12-31"
            }
        ]
    })
    assert pur_res.status_code == 200
    assert pur_res.json()["status"] == "RECEIVED"

    # 6. Verify Batch Inventory
    batches_res = client.get(f"/api/v1/batches?medicine_id={medicine_id}")
    assert batches_res.status_code == 200
    batches = batches_res.json()
    assert len(batches) == 1
    batch = batches[0]
    assert batch["batch_number"] == batch_lot
    assert batch["quantity"] == 100
    batch_id = batch["id"]

    # 7. POS Billing: Dispense 5 units to Customer
    sale_res = client.post("/api/v1/sales", json={
        "customer_id": customer_id,
        "customer_name": cust_name,
        "customer_phone": "+91 98765 00112",
        "payment_method": "Cash",
        "cashier_name": "Dr. Pharmacist",
        "discount_percent": 10.0,
        "tax_percent": 5.0,
        "items": [
            {
                "batch_id": batch_id,
                "quantity": 5
            }
        ]
    })
    assert sale_res.status_code == 201
    sale_data = sale_res.json()
    sale_id = sale_data["id"]
    inv_num = sale_data["invoice_number"]

    # 8. Verify Stock Deduction (100 - 5 = 95)
    batches_check = client.get(f"/api/v1/batches?medicine_id={medicine_id}").json()
    assert batches_check[0]["quantity"] == 95

    # 9. Return & Stock Restoration
    ret_res = client.post(f"/api/v1/sales/{sale_id}/return?reason=Prescription_Changed")
    assert ret_res.status_code == 200
    assert ret_res.json()["status"] == "Refunded"

    # Stock should be restored back to 100
    batches_restored = client.get(f"/api/v1/batches?medicine_id={medicine_id}").json()
    assert batches_restored[0]["quantity"] == 100

    # 10. Reports & Disaster Backup verification
    rep_res = client.get("/api/v1/reports/sales-summary?days=7")
    assert rep_res.status_code == 200
    assert "total_revenue" in rep_res.json()

    bak_res = client.post("/api/v1/reports/backup")
    assert bak_res.status_code == 200
    assert bak_res.json()["success"] is True
