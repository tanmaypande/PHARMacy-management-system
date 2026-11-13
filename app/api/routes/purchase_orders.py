from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.purchase_order_service import PurchaseOrderService
from app.services.inventory_service import InventoryService
import uuid

router = APIRouter(prefix="/api/v1/purchase-orders", tags=["Purchase Orders & Wholesale"])


class POItemInput(BaseModel):
    medicine_id: str
    quantity: int
    unit_cost_price: float


class CreatePORequest(BaseModel):
    supplier_id: str
    items: List[POItemInput]
    notes: Optional[str] = None
    pharmacy_id: Optional[str] = None


class ReceivePOItemInput(BaseModel):
    medicine_id: str
    quantity: int
    cost_price: float
    selling_price: float
    batch_number: Optional[str] = None
    expiry_date: Optional[str] = "2027-12-31"


class ReceivePORequest(BaseModel):
    batches: List[ReceivePOItemInput]


class StockAdjustmentRequest(BaseModel):
    batch_id: str
    new_quantity: int
    reason: str
    pharmacy_id: Optional[str] = None


@router.get("")
def list_purchase_orders(
    pharmacy_id: Optional[str] = None,
    supplier_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    svc = PurchaseOrderService(db)
    return svc.list_orders(pharmacy_id=pharmacy_id, supplier_id=supplier_id, status=status)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_purchase_order(req: CreatePORequest, db: Session = Depends(get_db)):
    svc = PurchaseOrderService(db)
    try:
        return svc.create_purchase_order(
            supplier_id=req.supplier_id,
            items=[i.model_dump() for i in req.items],
            notes=req.notes,
            pharmacy_id=req.pharmacy_id
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{po_id}")
def get_order_details(po_id: str, db: Session = Depends(get_db)):
    svc = PurchaseOrderService(db)
    try:
        return svc.get_order_details(po_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{po_id}/receive")
def receive_order_goods(po_id: str, req: ReceivePORequest, db: Session = Depends(get_db)):
    svc = PurchaseOrderService(db)
    try:
        return svc.receive_order_goods(po_id, [b.model_dump() for b in req.batches])
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/inventory/adjust")
def adjust_inventory_stock(req: StockAdjustmentRequest, db: Session = Depends(get_db)):
    svc = InventoryService(db)
    p_id = uuid.UUID(req.pharmacy_id) if req.pharmacy_id else None
    return svc.adjust_stock(
        batch_id=uuid.UUID(req.batch_id),
        new_quantity=req.new_quantity,
        reason=req.reason,
        pharmacy_id=p_id
    )


@router.get("/inventory/movements")
def list_stock_movements(pharmacy_id: Optional[str] = None, batch_id: Optional[str] = None, db: Session = Depends(get_db)):
    svc = InventoryService(db)
    p_id = uuid.UUID(pharmacy_id) if pharmacy_id else None
    b_id = uuid.UUID(batch_id) if batch_id else None
    return svc.list_movements(pharmacy_id=p_id, batch_id=b_id)
