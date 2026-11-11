from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.purchase import Purchase, PurchaseItem
from app.models.batch import MedicineBatch
from app.models.medicine import Medicine
from app.repositories.purchase_repository import PurchaseRepository
from app.repositories.supplier_repository import SupplierRepository
from app.repositories.batch_repository import BatchRepository
from app.repositories.audit_repository import AuditRepository
import uuid


class PurchaseService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PurchaseRepository(db)
        self.supplier_repo = SupplierRepository(db)
        self.batch_repo = BatchRepository(db)
        self.audit = AuditRepository(db)

    def list_purchases(self) -> List[Dict[str, Any]]:
        purchases = self.repo.list_purchases()
        return [
            {
                "id": str(p.id),
                "invoice_number": p.invoice_number,
                "supplier_name": p.supplier.name if p.supplier else "Unknown",
                "supplier_id": str(p.supplier_id),
                "purchase_date": p.purchase_date.strftime("%Y-%m-%d %H:%M"),
                "total_amount": float(p.total_amount),
                "status": p.status,
                "items_count": len(p.items)
            }
            for p in purchases
        ]

    def create_purchase(self, data: Dict[str, Any], actor: str = "system") -> Dict[str, Any]:
        """
        Receives inbound purchase consignment.
        TQM Error Prevention:
        - Automatically creates physical inventory batch for each received line item.
        - Updates stock quantity directly with strict check constraints.
        - Atomic transaction: entire delivery rolls back if any line item is invalid.
        """
        supplier_id_str = data.get("supplier_id")
        if not supplier_id_str:
            raise ValueError("Supplier is required.")
        supplier = self.supplier_repo.get_by_id(uuid.UUID(supplier_id_str))
        if not supplier:
            raise ValueError("Invalid supplier ID.")

        items_data = data.get("items", [])
        if not items_data:
            raise ValueError("At least one medicine item must be in the purchase invoice.")

        inv_number = data.get("invoice_number", "").strip()
        if not inv_number:
            inv_number = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        if self.repo.get_by_invoice_number(inv_number):
            raise ValueError(f"Purchase invoice '{inv_number}' already exists.")

        total_amount = Decimal("0.00")
        purchase_items = []

        for item in items_data:
            med_id = uuid.UUID(item["medicine_id"])
            medicine = self.db.get(Medicine, med_id)
            if not medicine:
                raise ValueError(f"Medicine ID {med_id} not found.")

            batch_num = item["batch_number"].strip()
            qty = int(item["quantity"])
            cost = Decimal(str(item["unit_cost"]))
            selling = Decimal(str(item.get("selling_price", cost * Decimal("1.25"))))
            exp_date_str = item.get("expiry_date")

            if qty <= 0:
                raise ValueError("Quantity must be greater than 0.")
            if cost < 0:
                raise ValueError("Unit cost cannot be negative.")

            subtotal = cost * Decimal(qty)
            total_amount += subtotal

            p_item = PurchaseItem(
                medicine_id=med_id,
                batch_number=batch_num,
                quantity=qty,
                unit_cost=cost,
                subtotal=subtotal
            )
            purchase_items.append(p_item)

            # Receive or create physical stock batch
            existing_batch = self.batch_repo.get_by_medicine_and_batch_number(med_id, batch_num)
            if existing_batch:
                self.batch_repo.update(existing_batch, {
                    "quantity": existing_batch.quantity + qty,
                    "cost_price": cost,
                    "selling_price": selling
                })
            else:
                if not exp_date_str:
                    # Default 1 year from now if not given
                    exp_date = date.today().replace(year=date.today().year + 1)
                else:
                    exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d").date()

                new_batch = MedicineBatch(
                    medicine_id=med_id,
                    supplier_id=supplier.id,
                    batch_number=batch_num,
                    expiry_date=exp_date,
                    cost_price=cost,
                    selling_price=selling,
                    quantity=qty,
                    is_active=True
                )
                self.batch_repo.create(new_batch)

        purchase = Purchase(
            invoice_number=inv_number,
            supplier_id=supplier.id,
            total_amount=total_amount,
            status="RECEIVED",
            notes=data.get("notes"),
            items=purchase_items
        )
        created = self.repo.create(purchase)
        self.audit.log_action(actor, "CREATE_PURCHASE", "Purchase", str(created.id), f"Received PO {created.invoice_number} total ₹{float(total_amount):.2f}")

        return {
            "id": str(created.id),
            "invoice_number": created.invoice_number,
            "total_amount": float(created.total_amount),
            "status": created.status
        }
