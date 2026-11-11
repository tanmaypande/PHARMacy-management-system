from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.policy import Policy
from app.repositories.policy_repository import PolicyRepository
from app.repositories.audit_repository import AuditRepository
import uuid


class PolicyService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PolicyRepository(db)
        self.audit = AuditRepository(db)

    def seed_standard_policies_if_empty(self) -> None:
        """Seeds initial healthcare SOPs and regulatory governance protocols if empty."""
        existing = self.repo.list_policies(limit=1)
        if existing:
            return

        standards = [
            {
                "title": "Cold Chain Vaccine & Biological Storage SOP",
                "category": "Medicine Storage & Cold Chain",
                "version": "1.0",
                "responsible_role": "Pharmacist",
                "content": "All temperature-sensitive biopharmaceuticals, insulins, and vaccines must be continuously monitored between +2°C and +8°C. Thermometers must be calibrated monthly, and temperature logbooks signed twice daily."
            },
            {
                "title": "Zero-Expired Drug Dispensation Policy (FEFO)",
                "category": "Expiry & Quarantine",
                "version": "1.0",
                "responsible_role": "Cashier",
                "content": "Medicines must strictly be dispensed using First-Expiry-First-Out (FEFO). Any batch expiring within 30 days must be flagged for return to vendor or clinical prioritization. Expired medications are automatically quarantined."
            },
            {
                "title": "Schedule H & H1 Controlled Drug Dispensing Compliance",
                "category": "Prescription Verification",
                "version": "1.0",
                "responsible_role": "Pharmacist",
                "content": "No Schedule H, H1, or X formulation may be dispensed without a valid registered medical practitioner prescription containing doctor license number, patient identity, date, and dosage instructions."
            },
            {
                "title": "Patient Health Information Privacy & Data Security",
                "category": "Data Security & HIPAA",
                "version": "1.0",
                "responsible_role": "All Staff",
                "content": "Patient contact details, medication profiles, and clinical histories are confidential personal health data. Passwords must never be shared, and terminals must be locked when unattended."
            }
        ]

        for s in standards:
            pol = Policy(
                title=s["title"],
                category=s["category"],
                version=s["version"],
                responsible_role=s["responsible_role"],
                content=s["content"],
                is_active=True
            )
            self.repo.create(pol)

    def list_policies(self, search: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        self.seed_standard_policies_if_empty()
        policies = self.repo.list_policies(search=search, category=category)
        return [
            {
                "id": str(p.id),
                "title": p.title,
                "category": p.category,
                "version": p.version,
                "content": p.content,
                "responsible_role": p.responsible_role,
                "is_active": p.is_active,
                "created_at": p.created_at.strftime("%Y-%m-%d"),
                "updated_at": p.updated_at.strftime("%Y-%m-%d")
            }
            for p in policies
        ]

    def create_policy(self, data: Dict[str, Any], actor: str = "Administrator") -> Dict[str, Any]:
        title = data.get("title", "").strip()
        content = data.get("content", "").strip()
        if not title:
            raise ValueError("Policy title is required.")
        if not content:
            raise ValueError("Policy content / SOP text is required.")

        policy = Policy(
            title=title,
            category=data.get("category", "Store Governance"),
            version=data.get("version", "1.0"),
            responsible_role=data.get("responsible_role", "All Staff"),
            content=content,
            is_active=data.get("is_active", True)
        )
        created = self.repo.create(policy)
        self.audit.log_action(actor, "CREATE_POLICY", "Policy", str(created.id), f"Created SOP policy: {created.title}")
        return {"id": str(created.id), "title": created.title}

    def update_policy(self, policy_id: str, data: Dict[str, Any], actor: str = "Administrator") -> Dict[str, Any]:
        p = self.repo.get_by_id(uuid.UUID(policy_id))
        if not p:
            raise ValueError("Policy not found.")

        if "title" in data and data["title"].strip():
            p.title = data["title"].strip()
        if "category" in data:
            p.category = data["category"]
        if "version" in data:
            p.version = data["version"]
        if "responsible_role" in data:
            p.responsible_role = data["responsible_role"]
        if "content" in data and data["content"].strip():
            p.content = data["content"].strip()
        if "is_active" in data:
            p.is_active = bool(data["is_active"])

        updated = self.repo.update(p)
        self.audit.log_action(actor, "UPDATE_POLICY", "Policy", str(updated.id), f"Updated policy: {updated.title}")
        return {"id": str(updated.id), "title": updated.title}

    def delete_policy(self, policy_id: str, actor: str = "Administrator") -> None:
        p = self.repo.get_by_id(uuid.UUID(policy_id))
        if not p:
            raise ValueError("Policy not found.")
        self.repo.delete(p)
        self.audit.log_action(actor, "DELETE_POLICY", "Policy", str(p.id), f"Deleted policy: {p.title}")
