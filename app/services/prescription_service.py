from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, date
from sqlalchemy.orm import Session
from app.models.prescription import Prescription
from app.repositories.prescription_repository import PrescriptionRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.audit_repository import AuditRepository
import uuid


class PrescriptionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PrescriptionRepository(db)
        self.cust_repo = CustomerRepository(db)
        self.audit = AuditRepository(db)

    def list_prescriptions(self, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if customer_id:
            prescriptions = self.repo.list_by_customer(uuid.UUID(customer_id))
        else:
            prescriptions = self.repo.list_all()

        return [
            {
                "id": str(p.id),
                "customer_id": str(p.customer_id),
                "customer_name": p.customer.name if p.customer else "Unknown",
                "doctor_name": p.doctor_name,
                "doctor_license": p.doctor_license,
                "prescription_date": p.prescription_date.strftime("%Y-%m-%d"),
                "diagnosis": p.diagnosis,
                "notes": p.notes,
                "created_at": p.created_at.strftime("%Y-%m-%d %H:%M")
            }
            for p in prescriptions
        ]

    def create_prescription(self, data: Dict[str, Any], actor: str = "system") -> Dict[str, Any]:
        customer_id_str = data.get("customer_id")
        if not customer_id_str:
            raise ValueError("Customer / Patient is required.")
        customer = self.cust_repo.get_by_id(uuid.UUID(customer_id_str))
        if not customer:
            raise ValueError("Invalid Customer ID.")

        doc_name = data.get("doctor_name", "").strip()
        if not doc_name:
            raise ValueError("Doctor name is required.")

        p_date_str = data.get("prescription_date")
        if p_date_str:
            p_date = datetime.strptime(p_date_str, "%Y-%m-%d").date()
        else:
            p_date = date.today()

        prescription = Prescription(
            customer_id=customer.id,
            doctor_name=doc_name,
            doctor_license=data.get("doctor_license"),
            prescription_date=p_date,
            diagnosis=data.get("diagnosis"),
            notes=data.get("notes")
        )
        created = self.repo.create(prescription)
        self.audit.log_action(actor, "CREATE_PRESCRIPTION", "Prescription", str(created.id), f"Recorded Rx for {customer.name} by Dr. {doc_name}")
        return {
            "id": str(created.id),
            "customer_name": customer.name,
            "doctor_name": created.doctor_name,
            "prescription_date": created.prescription_date.strftime("%Y-%m-%d")
        }

    def delete_prescription(self, prescription_id: str, actor: str = "system") -> None:
        p = self.repo.get_by_id(uuid.UUID(prescription_id))
        if not p:
            raise ValueError("Prescription not found.")
        self.repo.delete(p)
        self.audit.log_action(actor, "DELETE_PRESCRIPTION", "Prescription", str(p.id), "Deleted prescription record")
