from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from app.models.policy import Policy
import uuid


class PolicyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, policy_id: uuid.UUID) -> Optional[Policy]:
        return self.db.get(Policy, policy_id)

    def list_policies(self, search: Optional[str] = None, category: Optional[str] = None, active_only: bool = False, limit: int = 100, skip: int = 0) -> List[Policy]:
        stmt = select(Policy)
        if category and category != "All Categories":
            stmt = stmt.where(Policy.category == category)
        if active_only:
            stmt = stmt.where(Policy.is_active.is_(True))
        if search:
            q = f"%{search.strip()}%"
            stmt = stmt.where(or_(Policy.title.ilike(q), Policy.content.ilike(q), Policy.responsible_role.ilike(q)))
        stmt = stmt.order_by(Policy.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create(self, policy: Policy) -> Policy:
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def update(self, policy: Policy) -> Policy:
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def delete(self, policy: Policy) -> None:
        self.db.delete(policy)
        self.db.commit()
