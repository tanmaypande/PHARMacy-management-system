from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.supplier_portal_service import SupplierPortalService
from app.services.purchase_order_service import PurchaseOrderService

router = APIRouter(prefix="/api/v1/supplier-portal", tags=["Supplier Portal"])


class RespondPORequest(BaseModel):
    status: str
    quotation_notes: str = ""


@router.get("/dashboard")
def get_dashboard(supplier_id: Optional[str] = None, db: Session = Depends(get_db)):
    svc = SupplierPortalService(db)
    return svc.get_dashboard_metrics(supplier_id)


@router.get("/orders")
def list_orders(supplier_id: Optional[str] = None, db: Session = Depends(get_db)):
    svc = SupplierPortalService(db)
    return svc.list_orders(supplier_id)


@router.post("/orders/{po_id}/respond")
def respond_to_order(po_id: str, req: RespondPORequest, db: Session = Depends(get_db)):
    svc = PurchaseOrderService(db)
    try:
        return svc.supplier_respond_order(po_id, req.status, req.quotation_notes)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/catalog")
def get_supplied_catalog(supplier_id: Optional[str] = None, db: Session = Depends(get_db)):
    svc = SupplierPortalService(db)
    return svc.get_supplied_catalog(supplier_id)


@router.get("/payments")
def get_payment_ledger(supplier_id: Optional[str] = None, db: Session = Depends(get_db)):
    svc = SupplierPortalService(db)
    return svc.get_payment_ledger(supplier_id)
