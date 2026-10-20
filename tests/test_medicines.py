import uuid
import pytest
from fastapi.testclient import TestClient
from app.main_api import app

client = TestClient(app)


def test_create_and_get_medicine():
    # 1. Create a category first
    cat_res = client.post("/api/v1/categories", json={
        "name": f"Analgesics {uuid.uuid4().hex[:6]}"
    })
    assert cat_res.status_code == 201
    cat_id = cat_res.json()["id"]

    # 2. Create medicine
    med_code = f"MED-{uuid.uuid4().hex[:6].upper()}"
    med_payload = {
        "medicine_code": med_code,
        "name": "Paracetamol 500mg Extra",
        "generic_name": "Acetaminophen",
        "category_id": cat_id,
        "manufacturer": "GSK Healthcare",
        "unit_of_measurement": "Tablets",
        "reorder_level": 15,
        "prescription_required": False,
        "is_active": True
    }
    res = client.post("/api/v1/medicines", json=med_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["medicine_code"] == med_code
    assert data["name"] == "Paracetamol 500mg Extra"
    assert data["category_name"] is not None
    med_id = data["id"]

    # 3. Retrieve medicine by ID
    res_get = client.get(f"/api/v1/medicines/{med_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == med_id


def test_duplicate_medicine_code_rejected():
    cat_res = client.post("/api/v1/categories", json={
        "name": f"Antibiotics {uuid.uuid4().hex[:6]}"
    })
    cat_id = cat_res.json()["id"]

    med_code = f"DUP-{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "medicine_code": med_code,
        "name": "Amoxicillin 250mg",
        "category_id": cat_id
    }
    res1 = client.post("/api/v1/medicines", json=payload)
    assert res1.status_code == 201

    # Attempt duplicate code
    payload2 = {
        "medicine_code": med_code,
        "name": "Different Drug Same Code",
        "category_id": cat_id
    }
    res2 = client.post("/api/v1/medicines", json=payload2)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"].lower()


def test_medicine_search_and_deactivate():
    cat_res = client.post("/api/v1/categories", json={
        "name": f"Cardiology {uuid.uuid4().hex[:6]}"
    })
    cat_id = cat_res.json()["id"]

    code = f"ATV-{uuid.uuid4().hex[:6].upper()}"
    client.post("/api/v1/medicines", json={
        "medicine_code": code,
        "name": "Atorvastatin 20mg",
        "generic_name": "Atorvastatin Calcium",
        "category_id": cat_id
    })

    # Search by brand
    res_search = client.get("/api/v1/medicines?search=Atorva")
    assert res_search.status_code == 200
    codes = [m["medicine_code"] for m in res_search.json()]
    assert code in codes

    # Soft delete (deactivate)
    med_id = [m["id"] for m in res_search.json() if m["medicine_code"] == code][0]
    res_deact = client.delete(f"/api/v1/medicines/{med_id}")
    assert res_deact.status_code == 200
    assert res_deact.json()["is_active"] is False
