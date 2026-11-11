from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.core.database import get_db
from app.services.supplier_service import SupplierService
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/suppliers", tags=["Suppliers"])


class SupplierCreateRequest(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True


@router.get("")
def list_suppliers(search: Optional[str] = None, db: Session = Depends(get_db)):
    svc = SupplierService(db)
    return svc.list_suppliers(search=search)


@router.post("")
def create_supplier(req: SupplierCreateRequest, db: Session = Depends(get_db)):
    svc = SupplierService(db)
    try:
        return svc.create_supplier(req.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{supplier_id}")
def update_supplier(supplier_id: str, req: SupplierCreateRequest, db: Session = Depends(get_db)):
    svc = SupplierService(db)
    try:
        return svc.update_supplier(supplier_id, req.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: str, db: Session = Depends(get_db)):
    svc = SupplierService(db)
    try:
        svc.delete_supplier(supplier_id)
        return {"status": "success", "message": "Supplier deleted"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
