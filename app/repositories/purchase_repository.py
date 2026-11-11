from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.purchase import Purchase, PurchaseItem
import uuid


class PurchaseRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, purchase_id: uuid.UUID) -> Optional[Purchase]:
        return self.db.get(Purchase, purchase_id)

    def get_by_invoice_number(self, invoice_number: str) -> Optional[Purchase]:
        stmt = select(Purchase).where(Purchase.invoice_number == invoice_number.strip())
        return self.db.scalars(stmt).first()

    def list_purchases(self, skip: int = 0, limit: int = 200) -> List[Purchase]:
        stmt = select(Purchase).order_by(Purchase.purchase_date.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).unique().all())

    def create(self, purchase: Purchase) -> Purchase:
        self.db.add(purchase)
        self.db.commit()
        self.db.refresh(purchase)
        return purchase
