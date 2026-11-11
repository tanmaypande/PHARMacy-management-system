import pytest
from fastapi.testclient import TestClient
from app.main_api import app

client = TestClient(app)


def test_tqm_and_policies_workflow():
    import uuid

    # 1. TQM KPIs endpoint
    kpis_res = client.get("/api/v1/tqm/kpis")
    assert kpis_res.status_code == 200
    kpis = kpis_res.json()
    assert "billing_accuracy_percentage" in kpis
    assert "expired_stock_percentage" in kpis
    assert "total_batches_audited" in kpis

    # 2. Log TQM Quality Audit / CAPA record
    title = f"Cold Chain Verification Lot_{uuid.uuid4().hex[:4]}"
    create_tqm = client.post("/api/v1/tqm/records", json={
        "title": title,
        "category": "Audit",
        "severity": "High",
        "status": "Open",
        "description": "Temperature probe logged +9.1C momentarily during morning defreeze cycle.",
        "action_plan": "Recalibrate refrigeration thermostat sensor and replace backup seal.",
        "reported_by": "Quality Lead"
    })
    assert create_tqm.status_code == 200
    tqm_id = create_tqm.json()["id"]

    # 3. List TQM records and verify presence
    list_tqm = client.get("/api/v1/tqm/records")
    assert list_tqm.status_code == 200
    assert any(r["id"] == tqm_id for r in list_tqm.json())

    # 4. Resolve TQM record
    update_tqm = client.put(f"/api/v1/tqm/records/{tqm_id}", json={
        "title": title,
        "category": "Audit",
        "severity": "Medium",
        "status": "Resolved",
        "description": "Thermostat recalibrated and backup seal verified.",
        "action_plan": "Routine bi-weekly monitoring scheduled."
    })
    assert update_tqm.status_code == 200
    assert update_tqm.json()["status"] == "Resolved"

    # 5. Policies list (auto-seeds SOP standards)
    list_pol = client.get("/api/v1/policies")
    assert list_pol.status_code == 200
    policies = list_pol.json()
    assert len(policies) >= 4  # Standard seeded policies present

    # 6. Create custom pharmacy SOP policy
    pol_title = f"Narcotics Handling SOP_{uuid.uuid4().hex[:4]}"
    create_pol = client.post("/api/v1/policies", json={
        "title": pol_title,
        "category": "Prescription Verification",
        "version": "1.1",
        "responsible_role": "Pharmacist",
        "content": "Schedule X narcotics require double-lock safe storage and dual-pharmacist countersignatures on dispensation.",
        "is_active": True
    })
    assert create_pol.status_code == 200
    pol_id = create_pol.json()["id"]

    # 7. Search policy
    search_pol = client.get(f"/api/v1/policies?search={pol_title[:10]}")
    assert search_pol.status_code == 200
    assert len(search_pol.json()) >= 1

    # Cleanup
    client.delete(f"/api/v1/tqm/records/{tqm_id}")
    client.delete(f"/api/v1/policies/{pol_id}")
