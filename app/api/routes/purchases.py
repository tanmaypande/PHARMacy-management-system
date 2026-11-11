from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.core.database import get_db
from app.services.purchase_service import PurchaseService
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/purchases", tags=["Purchases & Inbound Invoices"])


class PurchaseItemPayload(BaseModel):
    medicine_id: str
    batch_number: str
    quantity: int
    unit_cost: float
    selling_price: Optional[float] = None
    expiry_date: Optional[str] = None


class PurchaseCreatePayload(BaseModel):
    supplier_id: str
    invoice_number: Optional[str] = None
    notes: Optional[str] = None
    items: List[PurchaseItemPayload]


@router.get("")
def list_purchases(db: Session = Depends(get_db)):
    svc = PurchaseService(db)
    return svc.list_purchases()


@router.post("")
def create_purchase(req: PurchaseCreatePayload, db: Session = Depends(get_db)):
    svc = PurchaseService(db)
    try:
        return svc.create_purchase(req.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
