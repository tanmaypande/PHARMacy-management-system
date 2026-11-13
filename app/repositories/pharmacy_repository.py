import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.pharmacy import Pharmacy, Subscription


class PharmacyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, pharmacy_id: uuid.UUID) -> Optional[Pharmacy]:
        return self.db.query(Pharmacy).filter(Pharmacy.id == pharmacy_id).first()

    def get_by_license(self, license_number: str) -> Optional[Pharmacy]:
        return self.db.query(Pharmacy).filter(Pharmacy.license_number == license_number).first()

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Pharmacy]:
        return self.db.query(Pharmacy).order_by(desc(Pharmacy.created_at)).offset(skip).limit(limit).all()

    def count_total(self) -> int:
        return self.db.query(Pharmacy).count()

    def count_active(self) -> int:
        return self.db.query(Pharmacy).filter(Pharmacy.status == "active").count()

    def count_suspended(self) -> int:
        return self.db.query(Pharmacy).filter(Pharmacy.status == "suspended").count()

    def create(self, pharmacy: Pharmacy) -> Pharmacy:
        self.db.add(pharmacy)
        self.db.commit()
        self.db.refresh(pharmacy)
        return pharmacy

    def update(self, pharmacy: Pharmacy) -> Pharmacy:
        self.db.commit()
        self.db.refresh(pharmacy)
        return pharmacy

    def list_subscriptions(self) -> List[Subscription]:
        return self.db.query(Subscription).order_by(desc(Subscription.start_date)).all()

    def create_subscription(self, sub: Subscription) -> Subscription:
        self.db.add(sub)
        self.db.commit()
        self.db.refresh(sub)
        return sub
