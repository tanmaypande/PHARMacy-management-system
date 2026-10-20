import uuid
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.medicine import Category, Medicine


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, category_id: uuid.UUID) -> Optional[Category]:
        return self.db.get(Category, category_id)

    def get_by_name(self, name: str) -> Optional[Category]:
        stmt = select(Category).where(func.lower(Category.name) == func.lower(name.strip()))
        return self.db.execute(stmt).scalar_one_or_none()

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Category]:
        stmt = select(Category).order_by(Category.name.asc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count_medicines(self, category_id: uuid.UUID) -> int:
        stmt = select(func.count(Medicine.id)).where(Medicine.category_id == category_id)
        return self.db.execute(stmt).scalar() or 0

    def create(self, category: Category) -> Category:
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(self, category: Category, update_data: dict) -> Category:
        for key, value in update_data.items():
            if value is not None and hasattr(category, key):
                setattr(category, key, value)
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category: Category) -> None:
        self.db.delete(category)
        self.db.commit()
