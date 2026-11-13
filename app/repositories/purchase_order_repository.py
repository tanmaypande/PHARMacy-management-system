import uuid
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, po_id: uuid.UUID) -> Optional[PurchaseOrder]:
        return (
            self.db.query(PurchaseOrder)
            .options(joinedload(PurchaseOrder.items))
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

    def list_orders(
        self,
        pharmacy_id: Optional[uuid.UUID] = None,
        supplier_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[PurchaseOrder]:
        query = self.db.query(PurchaseOrder).options(joinedload(PurchaseOrder.items))
        if pharmacy_id:
            query = query.filter(PurchaseOrder.pharmacy_id == pharmacy_id)
        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)
        if status and status != "All":
            query = query.filter(PurchaseOrder.status == status)
        return query.order_by(desc(PurchaseOrder.order_date)).offset(skip).limit(limit).all()

    def count_orders(
        self,
        pharmacy_id: Optional[uuid.UUID] = None,
        supplier_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None
    ) -> int:
        query = self.db.query(PurchaseOrder)
        if pharmacy_id:
            query = query.filter(PurchaseOrder.pharmacy_id == pharmacy_id)
        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)
        if status and status != "All":
            query = query.filter(PurchaseOrder.status == status)
        return query.count()

    def create(self, order: PurchaseOrder) -> PurchaseOrder:
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def update(self, order: PurchaseOrder) -> PurchaseOrder:
        self.db.commit()
        self.db.refresh(order)
        return order
