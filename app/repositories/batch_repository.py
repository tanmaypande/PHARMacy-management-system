import uuid
from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session, joinedload
from app.models.batch import MedicineBatch
from app.models.medicine import Medicine


class BatchRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, batch_id: uuid.UUID) -> Optional[MedicineBatch]:
        stmt = (
            select(MedicineBatch)
            .options(joinedload(MedicineBatch.medicine), joinedload(MedicineBatch.supplier))
            .where(MedicineBatch.id == batch_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_medicine_and_batch_number(self, medicine_id: uuid.UUID, batch_number: str) -> Optional[MedicineBatch]:
        stmt = select(MedicineBatch).where(
            MedicineBatch.medicine_id == medicine_id,
            func.lower(MedicineBatch.batch_number) == func.lower(batch_number.strip())
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_all(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[MedicineBatch]:
        stmt = select(MedicineBatch).options(joinedload(MedicineBatch.medicine), joinedload(MedicineBatch.supplier))
        if active_only:
            stmt = stmt.where(MedicineBatch.is_active == True)
        stmt = stmt.order_by(MedicineBatch.expiry_date.asc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def list_by_medicine(self, medicine_id: uuid.UUID, active_only: bool = True) -> List[MedicineBatch]:
        stmt = (
            select(MedicineBatch)
            .options(joinedload(MedicineBatch.supplier))
            .where(MedicineBatch.medicine_id == medicine_id)
        )
        if active_only:
            stmt = stmt.where(MedicineBatch.is_active == True)
        stmt = stmt.order_by(MedicineBatch.expiry_date.asc())
        return list(self.db.execute(stmt).scalars().all())

    def list_expiring_soon(self, days: int = 30) -> List[MedicineBatch]:
        today = date.today()
        threshold = today + timedelta(days=days)
        stmt = (
            select(MedicineBatch)
            .options(joinedload(MedicineBatch.medicine))
            .where(
                MedicineBatch.is_active == True,
                MedicineBatch.quantity > 0,
                MedicineBatch.expiry_date >= today,
                MedicineBatch.expiry_date <= threshold
            )
            .order_by(MedicineBatch.expiry_date.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_expired(self) -> List[MedicineBatch]:
        today = date.today()
        stmt = (
            select(MedicineBatch)
            .options(joinedload(MedicineBatch.medicine))
            .where(
                MedicineBatch.is_active == True,
                MedicineBatch.expiry_date < today
            )
            .order_by(MedicineBatch.expiry_date.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def create(self, batch: MedicineBatch) -> MedicineBatch:
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def update(self, batch: MedicineBatch, update_data: dict) -> MedicineBatch:
        for key, value in update_data.items():
            if value is not None and hasattr(batch, key):
                setattr(batch, key, value)
        self.db.commit()
        self.db.refresh(batch)
        return batch
