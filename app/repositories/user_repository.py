from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User
import uuid


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        return self.db.scalars(stmt).first()

    def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        stmt = select(User).order_by(User.created_at.asc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()
