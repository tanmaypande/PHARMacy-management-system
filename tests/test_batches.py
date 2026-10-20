import uuid
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from app.main_api import app

client = TestClient(app)


def test_create_batch_and_stock_calculation():
    # 1. Create Category and Medicine
    cat_res = client.post("/api/v1/categories", json={"name": f"Vitamins {uuid.uuid4().hex[:6]}"})
    cat_id = cat_res.json()["id"]

    med_res = client.post("/api/v1/medicines", json={
        "medicine_code": f"VIT-{uuid.uuid4().hex[:6].upper()}",
        "name": "Vitamin C 500mg Chewable",
        "category_id": cat_id
    })
    med_id = med_res.json()["id"]

    # 2. Add valid batch (future expiry date)
    future_date = (date.today() + timedelta(days=180)).isoformat()
    batch_res = client.post("/api/v1/batches", json={
        "medicine_id": med_id,
        "batch_number": "BATCH-001",
        "expiry_date": future_date,
        "cost_price": "2.50",
        "selling_price": "5.00",
        "quantity": 100
    })
    assert batch_res.status_code == 201
    batch_data = batch_res.json()
    assert batch_data["quantity"] == 100
    assert batch_data["is_expired"] is False

    # 3. Verify total stock updated on Medicine
    med_updated = client.get(f"/api/v1/medicines/{med_id}").json()
    assert med_updated["total_stock"] == 100


def test_tqm_reject_expired_batch_entry():
    # Attempt to receive a batch that is already expired
    cat_res = client.post("/api/v1/categories", json={"name": f"Antibiotics {uuid.uuid4().hex[:6]}"})
    cat_id = cat_res.json()["id"]

    med_res = client.post("/api/v1/medicines", json={
        "medicine_code": f"CIP-{uuid.uuid4().hex[:6].upper()}",
        "name": "Ciprofloxacin 500mg",
        "category_id": cat_id
    })
    med_id = med_res.json()["id"]

    past_date = (date.today() - timedelta(days=10)).isoformat()
    res = client.post("/api/v1/batches", json={
        "medicine_id": med_id,
        "batch_number": "EXPIRED-LOT",
        "expiry_date": past_date,
        "cost_price": "3.00",
        "selling_price": "6.00",
        "quantity": 50
    })
    # Must be blocked by TQM Poka-Yoke rule
    assert res.status_code == 400
    assert "error prevention" in res.json()["detail"].lower()
    assert "has already passed" in res.json()["detail"].lower()


def test_duplicate_batch_number_rejected():
    cat_res = client.post("/api/v1/categories", json={"name": f"Dermatology {uuid.uuid4().hex[:6]}"})
    cat_id = cat_res.json()["id"]

    med_res = client.post("/api/v1/medicines", json={
        "medicine_code": f"DERM-{uuid.uuid4().hex[:6].upper()}",
        "name": "Hydrocortisone 1% Cream",
        "category_id": cat_id
    })
    med_id = med_res.json()["id"]

    future_date = (date.today() + timedelta(days=90)).isoformat()
    payload = {
        "medicine_id": med_id,
        "batch_number": "LOT-DUPLICATE",
        "expiry_date": future_date,
        "quantity": 25
    }
    res1 = client.post("/api/v1/batches", json=payload)
    assert res1.status_code == 201

    # Attempt same batch for same medicine
    res2 = client.post("/api/v1/batches", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"].lower()


def test_dashboard_metrics():
    res = client.get("/api/v1/dashboard/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "total_medicines" in data
    assert "total_categories" in data
    assert "total_batches" in data
    assert "low_stock_medicines" in data
    assert "expiring_soon_batches" in data
    assert isinstance(data["total_medicines"], int)
