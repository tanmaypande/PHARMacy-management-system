from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.core.database import get_db
from app.services.customer_service import CustomerService
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/customers", tags=["Customers & Patients"])


class CustomerCreateRequest(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


@router.get("")
def list_customers(search: Optional[str] = None, db: Session = Depends(get_db)):
    svc = CustomerService(db)
    return svc.list_customers(search=search)


@router.post("")
def create_customer(req: CustomerCreateRequest, db: Session = Depends(get_db)):
    svc = CustomerService(db)
    try:
        return svc.create_customer(req.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{customer_id}")
def update_customer(customer_id: str, req: CustomerCreateRequest, db: Session = Depends(get_db)):
    svc = CustomerService(db)
    try:
        return svc.update_customer(customer_id, req.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{customer_id}")
def delete_customer(customer_id: str, db: Session = Depends(get_db)):
    svc = CustomerService(db)
    try:
        svc.delete_customer(customer_id)
        return {"status": "success", "message": "Customer deleted"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
