import uuid
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.models.pharmacy import Expense


class ExpenseRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_expenses(
        self,
        pharmacy_id: Optional[uuid.UUID] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Expense]:
        query = self.db.query(Expense)
        if pharmacy_id:
            query = query.filter(Expense.pharmacy_id == pharmacy_id)
        if category and category != "All":
            query = query.filter(Expense.category == category)
        return query.order_by(desc(Expense.expense_date)).offset(skip).limit(limit).all()

    def get_total_expenses(self, pharmacy_id: Optional[uuid.UUID] = None) -> Decimal:
        query = self.db.query(func.coalesce(func.sum(Expense.amount), Decimal("0.00")))
        if pharmacy_id:
            query = query.filter(Expense.pharmacy_id == pharmacy_id)
        return query.scalar() or Decimal("0.00")

    def create(self, expense: Expense) -> Expense:
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def delete(self, expense_id: uuid.UUID) -> bool:
        expense = self.db.query(Expense).filter(Expense.id == expense_id).first()
        if expense:
            self.db.delete(expense)
            self.db.commit()
            return True
        return False
