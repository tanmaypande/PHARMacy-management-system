import uuid
from typing import Dict, Any, List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.pharmacy import Pharmacy, Expense
from app.models.sale import Sale, SaleItem
from app.models.purchase import Purchase
from app.models.medicine import Medicine
from app.models.batch import MedicineBatch
from app.models.prescription import Prescription
from app.models.user import User
from app.repositories.expense_repository import ExpenseRepository
from app.repositories.pharmacy_repository import PharmacyRepository
from app.repositories.audit_repository import AuditRepository


class OwnerService:
    def __init__(self, db: Session):
        self.db = db
        self.expense_repo = ExpenseRepository(db)
        self.pharmacy_repo = PharmacyRepository(db)
        self.audit_repo = AuditRepository(db)

    def get_business_dashboard(self, pharmacy_id: Optional[str] = None) -> Dict[str, Any]:
        p_id = uuid.UUID(pharmacy_id) if pharmacy_id else None

        # 1. Total Revenue
        sale_q = self.db.query(func.coalesce(func.sum(Sale.total_amount), Decimal("0.00"))).filter(Sale.payment_status == "Paid")
        if p_id:
            sale_q = sale_q.filter(Sale.pharmacy_id == p_id)
        total_revenue = sale_q.scalar() or Decimal("0.00")

        # 2. Total Expenses
        total_expenses = self.expense_repo.get_total_expenses(p_id)

        # 3. Total COGS (Purchases)
        purch_q = self.db.query(func.coalesce(func.sum(Purchase.total_amount), Decimal("0.00")))
        if p_id:
            purch_q = purch_q.filter(Purchase.pharmacy_id == p_id)
        total_cogs = purch_q.scalar() or Decimal("0.00")

        # Net Profit
        net_profit = total_revenue - total_expenses

        # 4. Medicine Count
        med_q = self.db.query(Medicine).filter(Medicine.is_active == True)
        if p_id:
            med_q = med_q.filter(Medicine.pharmacy_id == p_id)
        total_medicines = med_q.count()

        # 5. Low Stock Medicines
        low_stock_count = 0
        all_meds = med_q.all()
        for m in all_meds:
            stock = sum(b.current_stock for b in m.batches if b.current_stock > 0)
            if stock <= m.reorder_level:
                low_stock_count += 1

        # 6. Staff Count
        user_q = self.db.query(User).filter(User.is_active == True)
        if p_id:
            user_q = user_q.filter(User.pharmacy_id == p_id)
        total_employees = user_q.count()

        # 7. Pending Prescriptions
        rx_q = self.db.query(Prescription).filter(Prescription.status == "Pending")
        if p_id:
            rx_q = rx_q.filter(Prescription.pharmacy_id == p_id)
        pending_prescriptions = rx_q.count()

        return {
            "total_revenue": float(total_revenue),
            "total_expenses": float(total_expenses),
            "total_cogs": float(total_cogs),
            "net_profit": float(net_profit),
            "total_medicines": total_medicines,
            "low_stock_items": low_stock_count,
            "total_employees": total_employees,
            "pending_prescriptions": pending_prescriptions
        }

    def list_expenses(self, pharmacy_id: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        p_id = uuid.UUID(pharmacy_id) if pharmacy_id else None
        expenses = self.expense_repo.list_expenses(pharmacy_id=p_id, category=category)
        return [
            {
                "id": str(e.id),
                "category": e.category,
                "amount": float(e.amount),
                "description": e.description,
                "expense_date": e.expense_date.strftime("%Y-%m-%d"),
                "recorded_by": e.recorded_by
            }
            for e in expenses
        ]

    def add_expense(
        self,
        pharmacy_id: Optional[str],
        category: str,
        amount: float,
        description: str,
        recorded_by: str = "owner"
    ) -> Dict[str, Any]:
        p_id = uuid.UUID(pharmacy_id) if pharmacy_id else None
        if not p_id:
            default_p = self.pharmacy_repo.list_all(limit=1)
            p_id = default_p[0].id if default_p else None

        if not p_id:
            raise ValueError("No registered pharmacy found for expense association.")

        expense = Expense(
            pharmacy_id=p_id,
            category=category.strip(),
            amount=Decimal(str(amount)),
            description=description.strip(),
            recorded_by=recorded_by
        )
        created = self.expense_repo.create(expense)
        self.audit_repo.log_action(
            recorded_by,
            "ADD_EXPENSE",
            "Expense",
            str(created.id),
            f"Added {category} expense of ₹{amount:.2f}: {description}"
        )
        return {
            "id": str(created.id),
            "category": created.category,
            "amount": float(created.amount),
            "description": created.description
        }

    def delete_expense(self, expense_id: str, actor_username: str = "owner") -> bool:
        success = self.expense_repo.delete(uuid.UUID(expense_id))
        if success:
            self.audit_repo.log_action(actor_username, "DELETE_EXPENSE", "Expense", expense_id, "Expense deleted")
        return success

    def get_profit_and_loss(self, pharmacy_id: Optional[str] = None) -> Dict[str, Any]:
        p_id = uuid.UUID(pharmacy_id) if pharmacy_id else None

        sale_q = self.db.query(func.coalesce(func.sum(Sale.total_amount), Decimal("0.00"))).filter(Sale.payment_status == "Paid")
        if p_id:
            sale_q = sale_q.filter(Sale.pharmacy_id == p_id)
        gross_sales = sale_q.scalar() or Decimal("0.00")

        purch_q = self.db.query(func.coalesce(func.sum(Purchase.total_amount), Decimal("0.00")))
        if p_id:
            purch_q = purch_q.filter(Purchase.pharmacy_id == p_id)
        cogs = purch_q.scalar() or Decimal("0.00")

        gross_margin = gross_sales - cogs
        total_expenses = self.expense_repo.get_total_expenses(p_id)
        net_profit = gross_margin - total_expenses
        margin_pct = (float(net_profit) / float(gross_sales) * 100.0) if gross_sales > 0 else 0.0

        # Expenses by category breakdown
        cat_q = (
            self.db.query(Expense.category, func.sum(Expense.amount))
            .group_by(Expense.category)
        )
        if p_id:
            cat_q = cat_q.filter(Expense.pharmacy_id == p_id)
        category_breakdown = [
            {"category": cat, "amount": float(amt)}
            for cat, amt in cat_q.all()
        ]

        return {
            "gross_sales": float(gross_sales),
            "cost_of_goods_sold": float(cogs),
            "gross_margin": float(gross_margin),
            "total_expenses": float(total_expenses),
            "net_profit": float(net_profit),
            "net_margin_percentage": round(margin_pct, 2),
            "expenses_breakdown": category_breakdown
        }

    def get_pharmacy_profile(self, pharmacy_id: Optional[str] = None) -> Dict[str, Any]:
        p_id = uuid.UUID(pharmacy_id) if pharmacy_id else None
        p = self.pharmacy_repo.get_by_id(p_id) if p_id else self.pharmacy_repo.list_all(limit=1)[0]
        return {
            "id": str(p.id),
            "name": p.name,
            "license_number": p.license_number,
            "owner_name": p.owner_name,
            "phone": p.phone,
            "email": p.email,
            "address": p.address or "",
            "status": p.status,
            "subscription_plan": p.subscription_plan
        }

    def update_pharmacy_profile(
        self,
        pharmacy_id: Optional[str],
        name: str,
        phone: str,
        email: str,
        address: str,
        actor_username: str = "owner"
    ) -> Dict[str, Any]:
        p_id = uuid.UUID(pharmacy_id) if pharmacy_id else None
        p = self.pharmacy_repo.get_by_id(p_id) if p_id else self.pharmacy_repo.list_all(limit=1)[0]
        p.name = name.strip()
        p.phone = phone.strip()
        p.email = email.strip()
        p.address = address.strip()
        updated = self.pharmacy_repo.update(p)
        self.audit_repo.log_action(actor_username, "UPDATE_PROFILE", "Pharmacy", str(p.id), "Updated dispensary contact details")
        return {
            "id": str(updated.id),
            "name": updated.name,
            "phone": updated.phone,
            "email": updated.email,
            "address": updated.address
        }
