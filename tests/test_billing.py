import uuid
from datetime import date, timedelta
from decimal import Decimal
import pytest
from starlette.testclient import TestClient

from app.main_api import app
from app.core.database import SessionLocal
from app.models.medicine import Category, Medicine
from app.models.batch import MedicineBatch
from app.models.sale import Sale, SaleItem


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def setup_test_medicines_and_batches():
    db = SessionLocal()
    try:
        # Create unique category
        cat_name = f"Test Category {uuid.uuid4().hex[:6]}"
        cat = Category(name=cat_name, description="Test category")
        db.add(cat)
        db.flush()

        # Create active medicine
        med_code = f"MED-{uuid.uuid4().hex[:6].upper()}"
        med = Medicine(
            name=f"Amoxicillin {uuid.uuid4().hex[:4]}",
            medicine_code=med_code,
            generic_name="Amoxicillin Trihydrate",
            category_id=cat.id,
            reorder_level=10,
        )
        db.add(med)
        db.flush()

        # Create active, valid batch with 100 units
        today = date.today()
        valid_batch = MedicineBatch(
            medicine_id=med.id,
            batch_number=f"LOT-VAL-{uuid.uuid4().hex[:4].upper()}",
            expiry_date=today + timedelta(days=365),
            cost_price=Decimal("10.00"),
            selling_price=Decimal("15.50"),
            quantity=100,
            is_active=True,
        )
        db.add(valid_batch)

        # Create expired batch with 50 units (expired 30 days ago)
        expired_batch = MedicineBatch(
            medicine_id=med.id,
            batch_number=f"LOT-EXP-{uuid.uuid4().hex[:4].upper()}",
            expiry_date=today - timedelta(days=30),
            cost_price=Decimal("8.00"),
            selling_price=Decimal("12.00"),
            quantity=50,
            is_active=True,
        )
        db.add(expired_batch)

        db.commit()
        db.refresh(valid_batch)
        db.refresh(expired_batch)
        db.refresh(med)

        yield {
            "medicine_id": str(med.id),
            "medicine_name": med.name,
            "valid_batch_id": str(valid_batch.id),
            "valid_batch_number": valid_batch.batch_number,
            "expired_batch_id": str(expired_batch.id),
        }
    finally:
        db.close()


def test_create_sale_success_and_stock_deduction(client, setup_test_medicines_and_batches):
    data = setup_test_medicines_and_batches
    valid_batch_id = data["valid_batch_id"]

    sale_payload = {
        "customer_name": "John Doe Patient",
        "customer_phone": "555-0199",
        "payment_method": "Cash",
        "discount_percent": 10.0,  # 10% discount
        "tax_percent": 5.0,        # 5% tax
        "cashier_name": "Dr. Sarah Pharmacist",
        "notes": "Dispensed 2 strips of antibiotics with oral care instructions.",
        "items": [
            {
                "batch_id": valid_batch_id,
                "quantity": 4,
                "unit_price": 15.50
            }
        ]
    }

    # Post sale
    response = client.post("/api/v1/sales", json=sale_payload)
    assert response.status_code == 201, response.text
    result = response.json()

    assert result["invoice_number"].startswith("INV-")
    assert result["customer_name"] == "John Doe Patient"
    assert len(result["items"]) == 1
    assert result["items"][0]["quantity"] == 4
    assert float(result["subtotal"]) == 62.00  # 4 * 15.50 = 62.00
    assert float(result["discount_amount"]) == 6.20  # 10% of 62.00
    # Taxable = 62.00 - 6.20 = 55.80. Tax = 5% of 55.80 = 2.79. Total = 55.80 + 2.79 = 58.59
    assert float(result["tax_amount"]) == 2.79
    assert float(result["total_amount"]) == 58.59

    # Verify inventory was deducted: 100 - 4 = 96
    db = SessionLocal()
    try:
        batch = db.query(MedicineBatch).filter_by(id=uuid.UUID(valid_batch_id)).first()
        assert batch.quantity == 96
    finally:
        db.close()


def test_tqm_block_expired_medicine_dispensation(client, setup_test_medicines_and_batches):
    data = setup_test_medicines_and_batches
    expired_batch_id = data["expired_batch_id"]

    sale_payload = {
        "customer_name": "Test Patient",
        "items": [
            {
                "batch_id": expired_batch_id,
                "quantity": 1
            }
        ]
    }

    response = client.post("/api/v1/sales", json=sale_payload)
    assert response.status_code == 400
    assert "CLINICAL SAFETY BLOCK" in response.json()["detail"]
    assert "expired" in response.json()["detail"].lower()


def test_tqm_insufficient_stock_rejection(client, setup_test_medicines_and_batches):
    data = setup_test_medicines_and_batches
    valid_batch_id = data["valid_batch_id"]

    # Attempt to sell 999 units when only 100 (or 96) available
    sale_payload = {
        "customer_name": "Large Order Patient",
        "items": [
            {
                "batch_id": valid_batch_id,
                "quantity": 999
            }
        ]
    }

    response = client.post("/api/v1/sales", json=sale_payload)
    assert response.status_code == 400
    assert "INSUFFICIENT STOCK" in response.json()["detail"]


def test_get_sale_by_id_and_invoice(client, setup_test_medicines_and_batches):
    data = setup_test_medicines_and_batches
    valid_batch_id = data["valid_batch_id"]

    sale_payload = {
        "customer_name": "Alice Walker",
        "items": [
            {
                "batch_id": valid_batch_id,
                "quantity": 2
            }
        ]
    }

    res_create = client.post("/api/v1/sales", json=sale_payload)
    assert res_create.status_code == 201
    sale_dict = res_create.json()
    sale_id = sale_dict["id"]
    invoice_number = sale_dict["invoice_number"]

    # Get by ID
    res_id = client.get(f"/api/v1/sales/{sale_id}")
    assert res_id.status_code == 200
    assert res_id.json()["invoice_number"] == invoice_number

    # Get by invoice
    res_inv = client.get(f"/api/v1/sales/invoice/{invoice_number}")
    assert res_inv.status_code == 200
    assert res_inv.json()["id"] == sale_id


def test_today_summary_kpis(client):
    res = client.get("/api/v1/sales/summary/today")
    assert res.status_code == 200
    data = res.json()
    assert "today_revenue" in data
    assert "today_bills_count" in data
    assert "today_units_dispensed" in data
    assert data["today_bills_count"] >= 1
