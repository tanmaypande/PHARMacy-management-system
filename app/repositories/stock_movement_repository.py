import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.pharmacy import StockMovement


class StockMovementRepository:
    def __init__(self, db: Session):
        self.db = db

    def record_movement(
        self,
        batch_id: uuid.UUID,
        movement_type: str,
        quantity_change: int,
        balance_after: int,
        reason: str,
        performed_by: str,
        pharmacy_id: Optional[uuid.UUID] = None
    ) -> StockMovement:
        movement = StockMovement(
            pharmacy_id=pharmacy_id,
            batch_id=batch_id,
            movement_type=movement_type,
            quantity_change=quantity_change,
            balance_after=balance_after,
            reason=reason,
            performed_by=performed_by
        )
        self.db.add(movement)
        self.db.commit()
        self.db.refresh(movement)
        return movement

    def list_movements(
        self,
        pharmacy_id: Optional[uuid.UUID] = None,
        batch_id: Optional[uuid.UUID] = None,
        limit: int = 100
    ) -> List[StockMovement]:
        query = self.db.query(StockMovement)
        if pharmacy_id:
            query = query.filter(StockMovement.pharmacy_id == pharmacy_id)
        if batch_id:
            query = query.filter(StockMovement.batch_id == batch_id)
        return query.order_by(desc(StockMovement.created_at)).limit(limit).all()
