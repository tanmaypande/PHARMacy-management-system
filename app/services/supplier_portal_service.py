import uuid
from typing import Dict, Any, List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.supplier import Supplier
from app.models.purchase_order import PurchaseOrder
from app.models.purchase import Purchase
from app.models.batch import MedicineBatch
from app.models.medicine import Medicine


class SupplierPortalService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_metrics(self, supplier_id: Optional[str] = None) -> Dict[str, Any]:
        s_id = uuid.UUID(supplier_id) if supplier_id else None
        if not s_id:
            first_supp = self.db.query(Supplier).first()
            s_id = first_supp.id if first_supp else None

        if not s_id:
            return {
                "assigned_orders": 0,
                "pending_confirmation": 0,
                "completed_orders": 0,
                "total_business_value": 0.0
            }

        total_orders = self.db.query(PurchaseOrder).filter(PurchaseOrder.supplier_id == s_id).count()
        pending = self.db.query(PurchaseOrder).filter(PurchaseOrder.supplier_id == s_id, PurchaseOrder.status == "Pending").count()
        received = self.db.query(PurchaseOrder).filter(PurchaseOrder.supplier_id == s_id, PurchaseOrder.status == "Received").count()

        tot_val = (
            self.db.query(func.coalesce(func.sum(PurchaseOrder.total_amount), Decimal("0.00")))
            .filter(PurchaseOrder.supplier_id == s_id)
            .scalar() or Decimal("0.00")
        )

        return {
            "assigned_orders": total_orders,
            "pending_confirmation": pending,
            "completed_orders": received,
            "total_business_value": float(tot_val)
        }

    def list_orders(self, supplier_id: Optional[str] = None) -> List[Dict[str, Any]]:
        s_id = uuid.UUID(supplier_id) if supplier_id else None
        if not s_id:
            first_supp = self.db.query(Supplier).first()
            s_id = first_supp.id if first_supp else None

        if not s_id:
            return []

        orders = (
            self.db.query(PurchaseOrder)
            .filter(PurchaseOrder.supplier_id == s_id)
            .order_by(PurchaseOrder.order_date.desc())
            .all()
        )
        return [
            {
                "id": str(o.id),
                "po_number": o.po_number,
                "order_date": o.order_date.strftime("%Y-%m-%d"),
                "status": o.status,
                "total_amount": float(o.total_amount),
                "items_count": len(o.items),
                "notes": o.notes or "",
                "supplier_notes": o.supplier_quotation_notes or ""
            }
            for o in orders
        ]

    def get_supplied_catalog(self, supplier_id: Optional[str] = None) -> List[Dict[str, Any]]:
        s_id = uuid.UUID(supplier_id) if supplier_id else None
        if not s_id:
            first_supp = self.db.query(Supplier).first()
            s_id = first_supp.id if first_supp else None

        if not s_id:
            return []

        batches = (
            self.db.query(MedicineBatch)
            .filter(MedicineBatch.supplier_id == s_id)
            .all()
        )
        result = []
        for b in batches:
            med = b.medicine
            result.append({
                "batch_id": str(b.id),
                "medicine_name": med.name if med else "Unknown Drug",
                "batch_number": b.batch_number,
                "cost_price": float(b.cost_price),
                "current_stock": b.current_stock,
                "expiry_date": b.expiry_date.strftime("%Y-%m-%d")
            })
        return result

    def get_payment_ledger(self, supplier_id: Optional[str] = None) -> List[Dict[str, Any]]:
        s_id = uuid.UUID(supplier_id) if supplier_id else None
        if not s_id:
            first_supp = self.db.query(Supplier).first()
            s_id = first_supp.id if first_supp else None

        if not s_id:
            return []

        purchases = (
            self.db.query(Purchase)
            .filter(Purchase.supplier_id == s_id)
            .order_by(Purchase.purchase_date.desc())
            .all()
        )
        return [
            {
                "id": str(p.id),
                "invoice_number": p.invoice_number,
                "purchase_date": p.purchase_date.strftime("%Y-%m-%d"),
                "total_amount": float(p.total_amount),
                "payment_status": "Settled"
            }
            for p in purchases
        ]
