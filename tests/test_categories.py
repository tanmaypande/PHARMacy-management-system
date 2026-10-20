import uuid
import pytest
from fastapi.testclient import TestClient
from app.main_api import app

client = TestClient(app)


def test_create_and_list_category():
    unique_name = f"Test Category {uuid.uuid4().hex[:6]}"
    # 1. Create
    res = client.post("/api/v1/categories", json={
        "name": unique_name,
        "description": "Therapeutic testing category"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == unique_name
    category_id = data["id"]

    # 2. List
    res_list = client.get("/api/v1/categories")
    assert res_list.status_code == 200
    names = [c["name"] for c in res_list.json()]
    assert unique_name in names

    # 3. Retrieve by ID
    res_single = client.get(f"/api/v1/categories/{category_id}")
    assert res_single.status_code == 200
    assert res_single.json()["id"] == category_id


def test_duplicate_category_rejected():
    unique_name = f"Duplicate Cat {uuid.uuid4().hex[:6]}"
    # Create first
    res1 = client.post("/api/v1/categories", json={"name": unique_name})
    assert res1.status_code == 201

    # Attempt duplicate
    res2 = client.post("/api/v1/categories", json={"name": unique_name})
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"].lower()


def test_update_and_delete_category():
    unique_name = f"Cat To Delete {uuid.uuid4().hex[:6]}"
    res = client.post("/api/v1/categories", json={"name": unique_name})
    assert res.status_code == 201
    cat_id = res.json()["id"]

    # Update
    updated_name = f"Updated {unique_name}"
    res_update = client.put(f"/api/v1/categories/{cat_id}", json={"name": updated_name})
    assert res_update.status_code == 200
    assert res_update.json()["name"] == updated_name

    # Delete
    res_del = client.delete(f"/api/v1/categories/{cat_id}")
    assert res_del.status_code == 204

    # Verify 404
    res_get = client.get(f"/api/v1/categories/{cat_id}")
    assert res_get.status_code == 404
