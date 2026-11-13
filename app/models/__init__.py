"""
SQLAlchemy Domain Models for Pharmacy Management System.
Exposes all database entity models so they attach to Base.metadata for migrations and table creation.
"""
from app.models.medicine import Category, Medicine
from app.models.supplier import Supplier
from app.models.batch import MedicineBatch
from app.models.customer import Customer
from app.models.sale import Sale, SaleItem
from app.models.user import User, AuditLog
from app.models.purchase import Purchase, PurchaseItem
from app.models.prescription import Prescription
from app.models.store_setting import StoreSetting
from app.models.tqm import TQMRecord
from app.models.policy import Policy
from app.models.pharmacy import (
    Pharmacy,
    Subscription,
    Expense,
    StockMovement,
    SupportTicket,
    Notification
)
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.role import Role, Permission, RolePermission

__all__ = [
    "Category",
    "Medicine",
    "Supplier",
    "MedicineBatch",
    "Customer",
    "Sale",
    "SaleItem",
    "User",
    "AuditLog",
    "Purchase",
    "PurchaseItem",
    "Prescription",
    "StoreSetting",
    "TQMRecord",
    "Policy",
    "Pharmacy",
    "Subscription",
    "Expense",
    "StockMovement",
    "SupportTicket",
    "Notification",
    "PurchaseOrder",
    "PurchaseOrderItem",
    "Role",
    "Permission",
    "RolePermission",
]
