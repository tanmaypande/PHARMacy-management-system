import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.batch import MedicineBatch
from app.models.medicine import Medicine
from app.models.supplier import Supplier
from app.models.purchase import Purchase, PurchaseItem
from app.repositories.purchase_order_repository import PurchaseOrderRepository
from app.repositories.stock_movement_repository import StockMovementRepository
from app.repositories.audit_repository import AuditRepository


class PurchaseOrderService:
    def __init__(self, db: Session):
        self.db = db
        self.po_repo = PurchaseOrderRepository(db)
        self.stock_repo = StockMovementRepository(db)
        self.audit_repo = AuditRepository(db)

    def create_purchase_order(
        self,
        supplier_id: str,
        items: List[Dict[str, Any]],
        notes: Optional[str] = None,
        pharmacy_id: Optional[str] = None,
        created_by: str = "inventory"
    ) -> Dict[str, Any]:
        p_id = uuid.UUID(pharmacy_id) if pharmacy_id else None
        s_id = uuid.UUID(supplier_id)

        # Generate unique PO number
        seq = self.po_repo.count_orders() + 1
        po_number = f"PO-{datetime.now(timezone.utc).year}-{seq:04d}"

        total_amount = Decimal("0.00")
        po_items = []
        for item in items:
            med_id = uuid.UUID(item["medicine_id"])
            qty = int(item["quantity"])
            cost = Decimal(str(item["unit_cost_price"]))
            subtotal = cost * qty
            total_amount += subtotal

            po_items.append(
                PurchaseOrderItem(
                    medicine_id=med_id,
                    quantity_ordered=qty,
                    quantity_received=0,
                    unit_cost_price=cost,
                    subtotal=subtotal
                )
            )

        po = PurchaseOrder(
            po_number=po_number,
            pharmacy_id=p_id,
            supplier_id=s_id,
            status="Pending",
            total_amount=total_amount,
            notes=notes,
            created_by=created_by,
            items=po_items
        )
        created = self.po_repo.create(po)
        self.audit_repo.log_action(
            created_by,
            "CREATE_PURCHASE_ORDER",
            "PurchaseOrder",
            str(created.id),
            f"Created wholesale order {created.po_number} to supplier (Total ₹{total_amount:.2f})"
        )
        return {
            "id": str(created.id),
            "po_number": created.po_number,
            "status": created.status,
            "total_amount": float(created.total_amount)
        }

    def list_orders(
        self,
        pharmacy_id: Optional[str] = None,
        supplier_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        p_id = uuid.UUID(pharmacy_id) if pharmacy_id else None
        s_id = uuid.UUID(supplier_id) if supplier_id else None
        orders = self.po_repo.list_orders(pharmacy_id=p_id, supplier_id=s_id, status=status)

        result = []
        for o in orders:
            supp_name = o.supplier.name if hasattr(o, "supplier") and o.supplier else "Unknown Supplier"
            if not supp_name or supp_name == "Unknown Supplier":
                supp = self.db.query(Supplier).filter(Supplier.id == o.supplier_id).first()
                supp_name = supp.name if supp else "Wholesale Supplier"

            result.append({
                "id": str(o.id),
                "po_number": o.po_number,
                "supplier_name": supp_name,
                "supplier_id": str(o.supplier_id),
                "order_date": o.order_date.strftime("%Y-%m-%d"),
                "status": o.status,
                "total_amount": float(o.total_amount),
                "items_count": len(o.items),
                "notes": o.notes or "",
                "supplier_notes": o.supplier_quotation_notes or ""
            })
        return result

    def get_order_details(self, po_id: str) -> Dict[str, Any]:
        po = self.po_repo.get_by_id(uuid.UUID(po_id))
        if not po:
            raise ValueError("Purchase Order not found.")

        items_data = []
        for item in po.items:
            med = self.db.query(Medicine).filter(Medicine.id == item.medicine_id).first()
            items_data.append({
                "id": str(item.id),
                "medicine_id": str(item.medicine_id),
                "medicine_name": med.name if med else "Medicine Item",
                "quantity_ordered": item.quantity_ordered,
                "quantity_received": item.quantity_received,
                "unit_cost_price": float(item.unit_cost_price),
                "subtotal": float(item.subtotal)
            })

        supp = self.db.query(Supplier).filter(Supplier.id == po.supplier_id).first()
        return {
            "id": str(po.id),
            "po_number": po.po_number,
            "supplier_name": supp.name if supp else "Vendor",
            "supplier_phone": supp.phone if supp else "",
            "supplier_email": supp.email if supp else "",
            "order_date": po.order_date.strftime("%Y-%m-%d"),
            "expected_delivery_date": po.expected_delivery_date.strftime("%Y-%m-%d") if po.expected_delivery_date else "",
            "status": po.status,
            "total_amount": float(po.total_amount),
            "notes": po.notes or "",
            "supplier_notes": po.supplier_quotation_notes or "",
            "items": items_data
        }

    def supplier_respond_order(
        self,
        po_id: str,
        status: str,
        quotation_notes: str,
        actor_username: str = "supplier"
    ) -> Dict[str, Any]:
        po = self.po_repo.get_by_id(uuid.UUID(po_id))
        if not po:
            raise ValueError("Purchase Order not found.")

        valid_statuses = ["Confirmed", "Rejected", "Shipped"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid response status. Must be one of {valid_statuses}")

        po.status = status
        po.supplier_quotation_notes = quotation_notes.strip()
        updated = self.po_repo.update(po)

        self.audit_repo.log_action(
            actor_username,
            "SUPPLIER_RESPOND_PO",
            "PurchaseOrder",
            str(po.id),
            f"Supplier responded to {po.po_number}: status={status}, notes={quotation_notes}"
        )
        return {
            "id": str(updated.id),
            "po_number": updated.po_number,
            "status": updated.status,
            "supplier_notes": updated.supplier_quotation_notes
        }

    def receive_order_goods(
        self,
        po_id: str,
        received_batches: List[Dict[str, Any]],
        actor_username: str = "inventory"
    ) -> Dict[str, Any]:
        """
        Cross-Panel Workflow B Completion:
        Goods intake against PO -> creates/increments inventory batches,
        logs StockMovement audit trail, and marks PO as 'Received'.
        """
        po = self.po_repo.get_by_id(uuid.UUID(po_id))
        if not po:
            raise ValueError("Purchase Order not found.")

        # Update batches and stock
        for b_info in received_batches:
            med_id = uuid.UUID(b_info["medicine_id"])
            batch_num = b_info.get("batch_number", f"LOT-{datetime.now(timezone.utc).strftime('%m%d%H%M')}")
            qty = int(b_info["quantity"])
            cost = Decimal(str(b_info.get("cost_price", 10.00)))
            selling = Decimal(str(b_info.get("selling_price", cost * Decimal("1.25"))))
            exp_date = datetime.strptime(b_info.get("expiry_date", "2027-12-31"), "%Y-%m-%d").date()

            # Find or create batch
            batch = (
                self.db.query(MedicineBatch)
                .filter(MedicineBatch.medicine_id == med_id, MedicineBatch.batch_number == batch_num)
                .first()
            )
            if batch:
                batch.quantity += qty
                self.db.commit()
            else:
                batch = MedicineBatch(
                    medicine_id=med_id,
                    batch_number=batch_num,
                    quantity=qty,
                    cost_price=cost,
                    selling_price=selling,
                    expiry_date=exp_date,
                    supplier_id=po.supplier_id
                )
                self.db.add(batch)
                self.db.commit()
                self.db.refresh(batch)

            # Record TQM Stock Movement
            self.stock_repo.record_movement(
                batch_id=batch.id,
                movement_type="PURCHASE",
                quantity_change=qty,
                balance_after=batch.quantity,
                reason=f"Received against wholesale {po.po_number}",
                performed_by=actor_username,
                pharmacy_id=po.pharmacy_id
            )

        po.status = "Received"
        self.po_repo.update(po)

        self.audit_repo.log_action(
            actor_username,
            "RECEIVE_PO_GOODS",
            "PurchaseOrder",
            str(po.id),
            f"Received stock delivery for {po.po_number}. Inventory replenished."
        )
        return {
            "id": str(po.id),
            "po_number": po.po_number,
            "status": po.status
        }
