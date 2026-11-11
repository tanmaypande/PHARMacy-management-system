from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from app.models.customer import Customer
import uuid


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, customer_id: uuid.UUID) -> Optional[Customer]:
        return self.db.get(Customer, customer_id)

    def get_by_phone(self, phone: str) -> Optional[Customer]:
        stmt = select(Customer).where(Customer.phone == phone.strip())
        return self.db.scalars(stmt).first()

    def list_customers(self, search: Optional[str] = None, skip: int = 0, limit: int = 200) -> List[Customer]:
        stmt = select(Customer)
        if search:
            q = f"%{search.strip()}%"
            stmt = stmt.where(or_(Customer.name.ilike(q), Customer.phone.ilike(q), Customer.email.ilike(q)))
        stmt = stmt.order_by(Customer.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def update(self, customer: Customer) -> Customer:
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def delete(self, customer: Customer) -> None:
        self.db.delete(customer)
        self.db.commit()
