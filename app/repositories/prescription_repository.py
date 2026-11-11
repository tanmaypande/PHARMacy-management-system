from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.prescription import Prescription
import uuid


class PrescriptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, prescription_id: uuid.UUID) -> Optional[Prescription]:
        return self.db.get(Prescription, prescription_id)

    def list_by_customer(self, customer_id: uuid.UUID) -> List[Prescription]:
        stmt = select(Prescription).where(Prescription.customer_id == customer_id).order_by(Prescription.prescription_date.desc())
        return list(self.db.scalars(stmt).all())

    def list_all(self, skip: int = 0, limit: int = 200) -> List[Prescription]:
        stmt = select(Prescription).order_by(Prescription.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create(self, prescription: Prescription) -> Prescription:
        self.db.add(prescription)
        self.db.commit()
        self.db.refresh(prescription)
        return prescription

    def delete(self, prescription: Prescription) -> None:
        self.db.delete(prescription)
        self.db.commit()
