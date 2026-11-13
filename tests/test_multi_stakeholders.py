import pytest
import time
import uuid
from fastapi.testclient import TestClient
from app.main_api import app
from app.core.database import SessionLocal
from app.models.pharmacy import Pharmacy
from app.models.supplier import Supplier
from app.models.customer import Customer
from app.models.medicine import Medicine, Category
from app.models.batch import MedicineBatch
from app.models.prescription import Prescription
from datetime import date, timedelta
from decimal import Decimal

client = TestClient(app)


def test_super_admin_endpoints():
    uid = uuid.uuid4().hex[:8]
    # 1. Dashboard
    res = client.get("/api/v1/super-admin/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "total_registered_pharmacies" in data
    assert data["total_registered_pharmacies"] >= 1

    # 2. List Pharmacies
    res = client.get("/api/v1/super-admin/pharmacies")
    assert res.status_code == 200
    pharmacies = res.json()
    assert len(pharmacies) >= 1

    # 3. Register New Pharmacy
    new_reg = {
        "name": "Apollo Care Dispensary",
        "license_number": f"DL-APOLLO-{uid}",
        "owner_name": "Dr. Sunita Rao",
        "phone": "+91 91122 33445",
        "email": f"apollo_{uid}@care.com",
        "address": "45 Green Park, Metro City",
        "subscription_plan": "Enterprise",
        "owner_username": f"apollo_owner_{uid}",
        "owner_password": "apollo_password_123"
    }
    res = client.post("/api/v1/super-admin/pharmacies", json=new_reg)
    assert res.status_code == 201
    created_p = res.json()
    assert created_p["name"] == "Apollo Care Dispensary"

    # 4. Toggle Status
    res = client.put(f"/api/v1/super-admin/pharmacies/{created_p['pharmacy_id']}/toggle-status")
    assert res.status_code == 200
    assert res.json()["status"] == "suspended"

    # 5. List Subscriptions
    res = client.get("/api/v1/super-admin/subscriptions")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # 6. Support Tickets
    res = client.get("/api/v1/super-admin/support-tickets")
    assert res.status_code == 200
    tickets = res.json()
    if tickets:
        tck_id = tickets[0]["id"]
        res_reply = client.put(f"/api/v1/super-admin/support-tickets/{tck_id}/reply", json={"response": "Your seat limit has been upgraded.", "status": "Resolved"})
        assert res_reply.status_code == 200


def test_owner_endpoints():
    # 1. Dashboard
    res = client.get("/api/v1/owner/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "total_revenue" in data
    assert "total_expenses" in data

    # 2. Add and list expense
    exp_payload = {
        "category": "Utilities",
        "amount": 1500.50,
        "description": "Monthly water & refrigeration maintenance"
    }
    res = client.post("/api/v1/owner/expenses", json=exp_payload)
    assert res.status_code == 201
    exp_id = res.json()["id"]

    res_list = client.get("/api/v1/owner/expenses")
    assert res_list.status_code == 200
    assert any(e["id"] == exp_id for e in res_list.json())

    # 3. P&L Report
    res_pnl = client.get("/api/v1/owner/profit-loss")
    assert res_pnl.status_code == 200
    pnl = res_pnl.json()
    assert "gross_sales" in pnl
    assert "net_profit" in pnl

    # 4. Delete Expense
    res_del = client.delete(f"/api/v1/owner/expenses/{exp_id}")
    assert res_del.status_code == 200

    # 5. Profile
    res_prof = client.get("/api/v1/owner/profile")
    assert res_prof.status_code == 200
    assert "name" in res_prof.json()


def test_pharmacist_endpoints():
    with SessionLocal() as db:
        rx = db.query(Prescription).first()
        if not rx:
            cust = db.query(Customer).first()
            rx = Prescription(
                prescription_number="RX-TEST-001",
                customer_id=cust.id if cust else None,
                doctor_name="Dr. V. Mehta",
                status="Pending"
            )
            db.add(rx)
            db.commit()
            db.refresh(rx)
        rx_id = str(rx.id)
        cust_id = str(rx.customer_id) if rx.customer_id else None

    # 1. Dashboard
    res = client.get("/api/v1/pharmacist/dashboard")
    assert res.status_code == 200
    assert "pending_prescriptions" in res.json()

    # 2. List Prescriptions
    res = client.get("/api/v1/pharmacist/prescriptions")
    assert res.status_code == 200

    # 3. Verify Prescription
    res_v = client.post(f"/api/v1/pharmacist/prescriptions/{rx_id}/verify", json={"dispensing_notes": "Dosage verified: 500mg TDS after food."})
    assert res_v.status_code == 200
    assert res_v.json()["status"] == "Verified"

    # 4. Dispense Prescription
    res_d = client.post(f"/api/v1/pharmacist/prescriptions/{rx_id}/dispense")
    assert res_d.status_code == 200
    assert res_d.json()["status"] == "Dispensed"

    # 5. Patient history
    if cust_id:
        res_h = client.get(f"/api/v1/pharmacist/patient-history/{cust_id}")
        assert res_h.status_code == 200


def test_purchase_orders_workflow():
    uid = uuid.uuid4().hex[:8]
    with SessionLocal() as db:
        supp = db.query(Supplier).first()
        med = db.query(Medicine).first()
        supp_id = str(supp.id)
        med_id = str(med.id)

    # 1. Inventory Manager creates PO
    po_payload = {
        "supplier_id": supp_id,
        "items": [
            {"medicine_id": med_id, "quantity": 100, "unit_cost_price": 25.0}
        ],
        "notes": "Urgent stock replenishment"
    }
    res_po = client.post("/api/v1/purchase-orders", json=po_payload)
    assert res_po.status_code == 201
    po_id = res_po.json()["id"]
    assert res_po.json()["status"] == "Pending"

    # 2. Supplier views assigned POs
    res_supp_orders = client.get(f"/api/v1/supplier-portal/orders?supplier_id={supp_id}")
    assert res_supp_orders.status_code == 200
    assert any(o["id"] == po_id for o in res_supp_orders.json())

    # 3. Supplier accepts order with quotation notes
    res_resp = client.post(
        f"/api/v1/supplier-portal/orders/{po_id}/respond",
        json={"status": "Confirmed", "quotation_notes": "Order confirmed. Dispatching via express courier."}
    )
    assert res_resp.status_code == 200
    assert res_resp.json()["status"] == "Confirmed"

    # 4. Inventory Manager receives order goods (Workflow B Completion)
    receive_payload = {
        "batches": [
            {
                "medicine_id": med_id,
                "quantity": 100,
                "cost_price": 25.0,
                "selling_price": 35.0,
                "batch_number": f"PO-LOT-{uid}",
                "expiry_date": "2028-06-30"
            }
        ]
    }
    res_recv = client.post(f"/api/v1/purchase-orders/{po_id}/receive", json=receive_payload)
    assert res_recv.status_code == 200
    assert res_recv.json()["status"] == "Received"

    # 5. Check stock movements
    res_mov = client.get("/api/v1/purchase-orders/inventory/movements")
    assert res_mov.status_code == 200
    assert len(res_mov.json()) >= 1


def test_customer_portal_workflow():
    uid = uuid.uuid4().hex[:8]
    # 1. Patient self-registration
    patient_payload = {
        "name": "Deepak Verma",
        "phone": "+91 98888 11111",
        "email": f"deepak_{uid}@verma.com",
        "address": "77 Lotus Boulevard",
        "password": "patient_secure_123"
    }
    res_reg = client.post("/api/v1/customer-portal/register", json=patient_payload)
    assert res_reg.status_code == 201
    cust_id = res_reg.json()["customer_id"]

    # 2. Browse catalog
    res_cat = client.get("/api/v1/customer-portal/catalog")
    assert res_cat.status_code == 200
    assert len(res_cat.json()) >= 1

    # 3. Upload prescription
    upload_payload = {
        "customer_id": cust_id,
        "doctor_name": "Dr. Neha Kulkarni, MD",
        "doctor_registration": "MCI-778899",
        "notes": "Paracetamol 650mg TDS for 5 days"
    }
    res_rx = client.post("/api/v1/customer-portal/prescriptions", json=upload_payload)
    assert res_rx.status_code == 201
    assert res_rx.json()["status"] == "Pending"

    # 4. View My Prescriptions
    res_my_rx = client.get(f"/api/v1/customer-portal/prescriptions?customer_id={cust_id}")
    assert res_my_rx.status_code == 200
    assert len(res_my_rx.json()) >= 1

    # 5. Submit Support Ticket
    ticket_payload = {
        "customer_id": cust_id,
        "sender_name": "Deepak Verma",
        "sender_email": patient_payload["email"],
        "subject": "Inquiry regarding home delivery timings",
        "message": "Do you offer same-day evening delivery for urgent prescriptions?"
    }
    res_tck = client.post("/api/v1/customer-portal/support", json=ticket_payload)
    assert res_tck.status_code == 201
    assert res_tck.json()["status"] == "Open"
