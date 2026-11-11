from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from app.models.supplier import Supplier
import uuid


class SupplierRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, supplier_id: uuid.UUID) -> Optional[Supplier]:
        return self.db.get(Supplier, supplier_id)

    def get_by_name(self, name: str) -> Optional[Supplier]:
        stmt = select(Supplier).where(Supplier.name.ilike(name.strip()))
        return self.db.scalars(stmt).first()

    def list_suppliers(self, search: Optional[str] = None, skip: int = 0, limit: int = 200) -> List[Supplier]:
        stmt = select(Supplier)
        if search:
            q = f"%{search.strip()}%"
            stmt = stmt.where(or_(Supplier.name.ilike(q), Supplier.contact_person.ilike(q), Supplier.phone.ilike(q)))
        stmt = stmt.order_by(Supplier.name.asc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create(self, supplier: Supplier) -> Supplier:
        self.db.add(supplier)
        self.db.commit()
        self.db.refresh(supplier)
        return supplier

    def update(self, supplier: Supplier) -> Supplier:
        self.db.commit()
        self.db.refresh(supplier)
        return supplier

    def delete(self, supplier: Supplier) -> None:
        self.db.delete(supplier)
        self.db.commit()
