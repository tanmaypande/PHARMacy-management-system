import uuid
from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from fastapi import HTTPException, status
from app.models.medicine import Medicine, Category
from app.models.batch import MedicineBatch
from app.repositories.batch_repository import BatchRepository
from app.repositories.medicine_repository import MedicineRepository
from app.api.schemas.batch import BatchCreate, BatchUpdate, BatchResponse
from app.api.schemas.dashboard import DashboardMetrics


class InventoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BatchRepository(db)
        self.med_repo = MedicineRepository(db)

    def _to_response(self, batch: MedicineBatch) -> BatchResponse:
        today = date.today()
        is_exp = batch.expiry_date < today
        days_left = (batch.expiry_date - today).days

        return BatchResponse(
            id=batch.id,
            medicine_id=batch.medicine_id,
            medicine_name=batch.medicine.name if batch.medicine else None,
            medicine_code=batch.medicine.medicine_code if batch.medicine else None,
            supplier_id=batch.supplier_id,
            supplier_name=batch.supplier.name if batch.supplier else None,
            batch_number=batch.batch_number,
            expiry_date=batch.expiry_date,
            cost_price=batch.cost_price,
            selling_price=batch.selling_price,
            quantity=batch.quantity,
            is_active=batch.is_active,
            is_expired=is_exp,
            days_until_expiry=days_left,
            created_at=batch.created_at,
            updated_at=batch.updated_at
        )

    def create_batch(self, payload: BatchCreate) -> BatchResponse:
        # Validate medicine exists
        medicine = self.med_repo.get_by_id(payload.medicine_id)
        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medicine with ID '{payload.medicine_id}' was not found"
            )

        # TQM Poka-Yoke: Strictly prevent adding expired stock
        if payload.expiry_date <= date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"TQM Error Prevention: Cannot accept batch '{payload.batch_number}' because expiry date ({payload.expiry_date}) has already passed."
            )

        # Prevent duplicate batch number for the same medicine
        existing = self.repo.get_by_medicine_and_batch_number(payload.medicine_id, payload.batch_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Batch number '{payload.batch_number}' already exists for medicine '{medicine.name}'"
            )

        new_batch = MedicineBatch(
            medicine_id=payload.medicine_id,
            supplier_id=payload.supplier_id,
            batch_number=payload.batch_number.strip().upper(),
            expiry_date=payload.expiry_date,
            cost_price=payload.cost_price,
            selling_price=payload.selling_price,
            quantity=payload.quantity,
            is_active=payload.is_active
        )
        saved = self.repo.create(new_batch)
        reloaded = self.repo.get_by_id(saved.id)
        return self._to_response(reloaded or saved)

    def list_batches(
        self,
        medicine_id: Optional[uuid.UUID] = None,
        active_only: bool = True
    ) -> List[BatchResponse]:
        if medicine_id:
            batches = self.repo.list_by_medicine(medicine_id, active_only=active_only)
        else:
            batches = self.repo.list_all(active_only=active_only)
        return [self._to_response(b) for b in batches]

    def list_expiring_soon(self, days: int = 30) -> List[BatchResponse]:
        batches = self.repo.list_expiring_soon(days=days)
        return [self._to_response(b) for b in batches]

    def list_expired(self) -> List[BatchResponse]:
        batches = self.repo.list_expired()
        return [self._to_response(b) for b in batches]

    def get_dashboard_metrics(self) -> DashboardMetrics:
        today = date.today()
        threshold = today + timedelta(days=30)

        total_meds = self.db.execute(select(func.count(Medicine.id))).scalar() or 0
        active_meds = self.db.execute(select(func.count(Medicine.id)).where(Medicine.is_active == True)).scalar() or 0
        total_cats = self.db.execute(select(func.count(Category.id))).scalar() or 0
        total_batches = self.db.execute(select(func.count(MedicineBatch.id)).where(MedicineBatch.is_active == True)).scalar() or 0
        total_stock = self.db.execute(select(func.coalesce(func.sum(MedicineBatch.quantity), 0)).where(MedicineBatch.is_active == True)).scalar() or 0

        # Expired batches
        expired = self.db.execute(
            select(func.count(MedicineBatch.id)).where(
                MedicineBatch.is_active == True,
                MedicineBatch.expiry_date < today
            )
        ).scalar() or 0

        # Expiring soon batches
        expiring_soon = self.db.execute(
            select(func.count(MedicineBatch.id)).where(
                MedicineBatch.is_active == True,
                MedicineBatch.quantity > 0,
                MedicineBatch.expiry_date >= today,
                MedicineBatch.expiry_date <= threshold
            )
        ).scalar() or 0

        # Low stock medicines (medicines where sum(batch qty) <= reorder_level)
        all_meds = self.med_repo.list_all(limit=1000)[0]
        low_stock_count = 0
        for m in all_meds:
            stock = sum(b.quantity for b in m.batches if b.is_active and b.expiry_date >= today)
            if stock <= m.reorder_level:
                low_stock_count += 1

        return DashboardMetrics(
            total_medicines=total_meds,
            active_medicines=active_meds,
            total_categories=total_cats,
            total_batches=total_batches,
            total_stock_units=int(total_stock),
            low_stock_medicines=low_stock_count,
            expiring_soon_batches=expiring_soon,
            expired_batches=expired
        )

    def adjust_stock(
        self,
        batch_id: uuid.UUID,
        new_quantity: int,
        reason: str,
        performed_by: str = "inventory",
        pharmacy_id: Optional[uuid.UUID] = None
    ) -> dict:
        if new_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TQM Error Prevention: Stock quantity cannot be negative."
            )

        batch = self.repo.get_by_id(batch_id)
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with ID '{batch_id}' was not found"
            )

        old_qty = batch.current_stock
        diff = new_quantity - old_qty
        batch.current_stock = new_quantity
        self.db.commit()

        # Record movement
        from app.repositories.stock_movement_repository import StockMovementRepository
        from app.repositories.audit_repository import AuditRepository
        stock_repo = StockMovementRepository(self.db)
        audit_repo = AuditRepository(self.db)

        movement = stock_repo.record_movement(
            batch_id=batch.id,
            movement_type="ADJUSTMENT",
            quantity_change=diff,
            balance_after=new_quantity,
            reason=reason.strip(),
            performed_by=performed_by,
            pharmacy_id=pharmacy_id
        )

        audit_repo.log_action(
            performed_by,
            "ADJUST_STOCK",
            "MedicineBatch",
            str(batch.id),
            f"Physical adjustment on batch {batch.batch_number}: {old_qty} -> {new_quantity}. Reason: {reason}"
        )

        return {
            "batch_id": str(batch.id),
            "batch_number": batch.batch_number,
            "previous_stock": old_qty,
            "new_stock": batch.current_stock,
            "movement_id": str(movement.id)
        }

    def list_movements(
        self,
        pharmacy_id: Optional[uuid.UUID] = None,
        batch_id: Optional[uuid.UUID] = None,
        limit: int = 100
    ) -> List[dict]:
        from app.repositories.stock_movement_repository import StockMovementRepository
        stock_repo = StockMovementRepository(self.db)
        movements = stock_repo.list_movements(pharmacy_id=pharmacy_id, batch_id=batch_id, limit=limit)
        result = []
        for m in movements:
            batch = self.repo.get_by_id(m.batch_id)
            med_name = batch.medicine.name if batch and batch.medicine else "Medicine Batch"
            batch_num = batch.batch_number if batch else "LOT"
            result.append({
                "id": str(m.id),
                "timestamp": m.created_at.strftime("%Y-%m-%d %H:%M"),
                "medicine_name": med_name,
                "batch_number": batch_num,
                "movement_type": m.movement_type,
                "quantity_change": m.quantity_change,
                "balance_after": m.balance_after,
                "reason": m.reason,
                "performed_by": m.performed_by
            })
        return result
