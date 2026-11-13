import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.prescription import Prescription
from app.models.customer import Customer
from app.models.batch import MedicineBatch
from app.models.sale import Sale, SaleItem
from app.repositories.audit_repository import AuditRepository


class PharmacistService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_repo = AuditRepository(db)

    def get_dashboard_metrics(self, pharmacy_id: Optional[str] = None) -> Dict[str, Any]:
        p_id = uuid.UUID(pharmacy_id) if pharmacy_id else None

        rx_q = self.db.query(Prescription)
        if p_id:
            rx_q = rx_q.filter(Prescription.pharmacy_id == p_id)

        pending = rx_q.filter(Prescription.status == "Pending").count()
        verified = rx_q.filter(Prescription.status == "Verified").count()
        dispensed = rx_q.filter(Prescription.status == "Dispensed").count()
        rejected = rx_q.filter(Prescription.status == "Rejected").count()

        # Near expiry batches
        today = datetime.now(timezone.utc).date()
        exp_soon = (
            self.db.query(MedicineBatch)
            .filter(MedicineBatch.expiry_date <= today + timedelta(days=30), MedicineBatch.quantity > 0)
            .count()
        )

        return {
            "pending_prescriptions": pending,
            "verified_prescriptions": verified,
            "dispensed_prescriptions": dispensed,
            "rejected_prescriptions": rejected,
            "near_expiry_batches": exp_soon
        }

    def list_prescriptions(self, pharmacy_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        p_id = uuid.UUID(pharmacy_id) if pharmacy_id else None
        query = self.db.query(Prescription)
        if p_id:
            query = query.filter(Prescription.pharmacy_id == p_id)
        if status and status != "All":
            query = query.filter(Prescription.status == status)

        prescriptions = query.order_by(Prescription.created_at.desc()).all()
        result = []
        for rx in prescriptions:
            patient_name = rx.customer.name if rx.customer else "Unknown Patient"
            result.append({
                "id": str(rx.id),
                "rx_number": rx.prescription_number or f"RX-{str(rx.id)[:8].upper()}",
                "patient_name": patient_name,
                "customer_id": str(rx.customer_id) if rx.customer_id else "",
                "doctor_name": rx.doctor_name,
                "doctor_registration": rx.doctor_registration or "",
                "status": rx.status or "Pending",
                "notes": rx.notes or "",
                "dispensing_notes": getattr(rx, "dispensing_notes", "") or "",
                "verified_by": getattr(rx, "verified_by", "") or "",
                "created_at": rx.created_at.strftime("%Y-%m-%d %H:%M")
            })
        return result

    def verify_prescription(
        self,
        prescription_id: str,
        dispensing_notes: str,
        pharmacist_username: str = "pharmacist"
    ) -> Dict[str, Any]:
        rx = self.db.query(Prescription).filter(Prescription.id == uuid.UUID(prescription_id)).first()
        if not rx:
            raise ValueError("Prescription not found.")

        rx.status = "Verified"
        rx.verified_by = pharmacist_username
        rx.dispensing_notes = dispensing_notes.strip()
        rx.verified_at = datetime.now(timezone.utc)
        self.db.commit()

        self.audit_repo.log_action(
            pharmacist_username,
            "VERIFY_PRESCRIPTION",
            "Prescription",
            str(rx.id),
            f"Pharmacist verified Rx {rx.prescription_number}. Notes: {dispensing_notes}"
        )
        return {
            "id": str(rx.id),
            "rx_number": rx.prescription_number,
            "status": rx.status,
            "verified_by": rx.verified_by,
            "dispensing_notes": rx.dispensing_notes
        }

    def reject_prescription(
        self,
        prescription_id: str,
        reason: str,
        pharmacist_username: str = "pharmacist"
    ) -> Dict[str, Any]:
        rx = self.db.query(Prescription).filter(Prescription.id == uuid.UUID(prescription_id)).first()
        if not rx:
            raise ValueError("Prescription not found.")

        rx.status = "Rejected"
        rx.verified_by = pharmacist_username
        rx.dispensing_notes = f"REJECTED: {reason.strip()}"
        rx.verified_at = datetime.now(timezone.utc)
        self.db.commit()

        self.audit_repo.log_action(
            pharmacist_username,
            "REJECT_PRESCRIPTION",
            "Prescription",
            str(rx.id),
            f"Rejected Rx {rx.prescription_number} due to: {reason}"
        )
        return {
            "id": str(rx.id),
            "rx_number": rx.prescription_number,
            "status": rx.status,
            "reason": rx.dispensing_notes
        }

    def dispense_prescription(
        self,
        prescription_id: str,
        pharmacist_username: str = "pharmacist"
    ) -> Dict[str, Any]:
        rx = self.db.query(Prescription).filter(Prescription.id == uuid.UUID(prescription_id)).first()
        if not rx:
            raise ValueError("Prescription not found.")

        if rx.status != "Verified":
            raise ValueError("Prescription must be verified by a licensed pharmacist before clinical dispensing.")

        rx.status = "Dispensed"
        self.db.commit()

        self.audit_repo.log_action(
            pharmacist_username,
            "DISPENSE_PRESCRIPTION",
            "Prescription",
            str(rx.id),
            f"Prescription {rx.prescription_number} dispensed successfully."
        )
        return {
            "id": str(rx.id),
            "rx_number": rx.prescription_number,
            "status": rx.status
        }

    def get_patient_medication_history(self, customer_id: str) -> List[Dict[str, Any]]:
        c_id = uuid.UUID(customer_id)
        prescriptions = (
            self.db.query(Prescription)
            .filter(Prescription.customer_id == c_id)
            .order_by(Prescription.created_at.desc())
            .all()
        )
        sales = (
            self.db.query(Sale)
            .filter(Sale.customer_id == c_id)
            .order_by(Sale.created_at.desc())
            .all()
        )

        history = []
        for s in sales:
            for item in s.items:
                med_name = item.medicine.name if item.medicine else "Unknown Medicine"
                batch_no = item.batch.batch_number if item.batch else "N/A"
                history.append({
                    "date": s.created_at.strftime("%Y-%m-%d"),
                    "invoice_number": s.invoice_number,
                    "medicine_name": med_name,
                    "batch_number": batch_no,
                    "quantity": item.quantity,
                    "prescriber": "Doctor Recorded",
                    "payment_status": s.payment_status
                })
        return history
