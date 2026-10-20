import uuid
from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, joinedload
from app.models.medicine import Medicine, Category
from app.models.batch import MedicineBatch


class MedicineRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, medicine_id: uuid.UUID) -> Optional[Medicine]:
        stmt = (
            select(Medicine)
            .options(joinedload(Medicine.category), joinedload(Medicine.batches))
            .where(Medicine.id == medicine_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_by_code(self, medicine_code: str) -> Optional[Medicine]:
        stmt = select(Medicine).where(func.lower(Medicine.medicine_code) == func.lower(medicine_code.strip()))
        return self.db.execute(stmt).scalar_one_or_none()

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Medicine], int]:
        stmt = select(Medicine).options(joinedload(Medicine.category), joinedload(Medicine.batches))

        # Search filter (name, code, or generic name)
        if search:
            search_term = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Medicine.name).like(search_term),
                    func.lower(Medicine.medicine_code).like(search_term),
                    func.lower(Medicine.generic_name).like(search_term),
                )
            )

        # Category filter
        if category_id:
            stmt = stmt.where(Medicine.category_id == category_id)

        # Active status filter
        if is_active is not None:
            stmt = stmt.where(Medicine.is_active == is_active)

        # Count total
        count_stmt = select(func.count(Medicine.id))
        if search:
            count_stmt = count_stmt.where(
                or_(
                    func.lower(Medicine.name).like(search_term),
                    func.lower(Medicine.medicine_code).like(search_term),
                    func.lower(Medicine.generic_name).like(search_term),
                )
            )
        if category_id:
            count_stmt = count_stmt.where(Medicine.category_id == category_id)
        if is_active is not None:
            count_stmt = count_stmt.where(Medicine.is_active == is_active)

        total = self.db.execute(count_stmt).scalar() or 0

        # Pagination & Ordering
        stmt = stmt.order_by(Medicine.name.asc()).offset(skip).limit(limit)
        results = list(self.db.execute(stmt).unique().scalars().all())
        return results, total

    def get_total_stock(self, medicine_id: uuid.UUID) -> int:
        stmt = select(func.coalesce(func.sum(MedicineBatch.quantity), 0)).where(
            MedicineBatch.medicine_id == medicine_id,
            MedicineBatch.is_active == True
        )
        return self.db.execute(stmt).scalar() or 0

    def create(self, medicine: Medicine) -> Medicine:
        self.db.add(medicine)
        self.db.commit()
        self.db.refresh(medicine)
        return medicine

    def update(self, medicine: Medicine, update_data: dict) -> Medicine:
        for key, value in update_data.items():
            if value is not None and hasattr(medicine, key):
                setattr(medicine, key, value)
        self.db.commit()
        self.db.refresh(medicine)
        return medicine

    def delete(self, medicine: Medicine) -> None:
        self.db.delete(medicine)
        self.db.commit()
