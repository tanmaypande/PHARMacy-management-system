from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.tqm import TQMRecord
from app.repositories.tqm_repository import TQMRepository
from app.repositories.audit_repository import AuditRepository
import uuid


class TQMService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TQMRepository(db)
        self.audit = AuditRepository(db)

    def list_records(self, category: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        records = self.repo.list_records(category=category, status=status)
        return [
            {
                "id": str(r.id),
                "title": r.title,
                "category": r.category,
                "severity": r.severity,
                "status": r.status,
                "description": r.description,
                "action_plan": r.action_plan,
                "reported_by": r.reported_by,
                "resolved_by": r.resolved_by,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M"),
                "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M")
            }
            for r in records
        ]

    def create_record(self, data: Dict[str, Any], actor: str = "Quality Auditor") -> Dict[str, Any]:
        title = data.get("title", "").strip()
        desc = data.get("description", "").strip()
        if not title:
            raise ValueError("Record title is required.")
        if not desc:
            raise ValueError("Description / Incident details are required.")

        record = TQMRecord(
            title=title,
            category=data.get("category", "Audit"),
            severity=data.get("severity", "Medium"),
            status=data.get("status", "Open"),
            description=desc,
            action_plan=data.get("action_plan"),
            reported_by=data.get("reported_by") or actor
        )
        created = self.repo.create(record)
        self.audit.log_action(actor, "CREATE_TQM_RECORD", "TQMRecord", str(created.id), f"Logged {created.category}: {created.title}")
        return {
            "id": str(created.id),
            "title": created.title,
            "status": created.status
        }

    def update_record(self, record_id: str, data: Dict[str, Any], actor: str = "Quality Auditor") -> Dict[str, Any]:
        rec = self.repo.get_by_id(uuid.UUID(record_id))
        if not rec:
            raise ValueError("TQM record not found.")

        if "title" in data and data["title"].strip():
            rec.title = data["title"].strip()
        if "category" in data:
            rec.category = data["category"]
        if "severity" in data:
            rec.severity = data["severity"]
        if "status" in data:
            rec.status = data["status"]
            if rec.status in ("Resolved", "Closed"):
                rec.resolved_by = actor
        if "description" in data:
            rec.description = data["description"]
        if "action_plan" in data:
            rec.action_plan = data["action_plan"]

        updated = self.repo.update(rec)
        self.audit.log_action(actor, "UPDATE_TQM_RECORD", "TQMRecord", str(updated.id), f"Updated {updated.category} status to {updated.status}")
        return {
            "id": str(updated.id),
            "title": updated.title,
            "status": updated.status
        }

    def delete_record(self, record_id: str, actor: str = "Quality Auditor") -> None:
        rec = self.repo.get_by_id(uuid.UUID(record_id))
        if not rec:
            raise ValueError("TQM record not found.")
        self.repo.delete(rec)
        self.audit.log_action(actor, "DELETE_TQM_RECORD", "TQMRecord", str(rec.id), f"Deleted record {rec.title}")

    def get_quality_dashboard_kpis(self) -> Dict[str, Any]:
        return self.repo.calculate_actual_kpis()
