from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.owner_service import OwnerService

router = APIRouter(prefix="/api/v1/owner", tags=["Pharmacy Owner Panel"])


class AddExpenseRequest(BaseModel):
    category: str
    amount: float
    description: str
    pharmacy_id: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    name: str
    phone: str
    email: str
    address: str
    pharmacy_id: Optional[str] = None


@router.get("/dashboard")
def get_dashboard(pharmacy_id: Optional[str] = None, db: Session = Depends(get_db)):
    svc = OwnerService(db)
    return svc.get_business_dashboard(pharmacy_id)


@router.get("/expenses")
def list_expenses(pharmacy_id: Optional[str] = None, category: Optional[str] = None, db: Session = Depends(get_db)):
    svc = OwnerService(db)
    return svc.list_expenses(pharmacy_id, category)


@router.post("/expenses", status_code=status.HTTP_201_CREATED)
def add_expense(req: AddExpenseRequest, db: Session = Depends(get_db)):
    svc = OwnerService(db)
    try:
        return svc.add_expense(
            pharmacy_id=req.pharmacy_id,
            category=req.category,
            amount=req.amount,
            description=req.description
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/expenses/{expense_id}")
def delete_expense(expense_id: str, db: Session = Depends(get_db)):
    svc = OwnerService(db)
    if not svc.delete_expense(expense_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")
    return {"success": True}


@router.get("/profit-loss")
def get_profit_and_loss(pharmacy_id: Optional[str] = None, db: Session = Depends(get_db)):
    svc = OwnerService(db)
    return svc.get_profit_and_loss(pharmacy_id)


@router.get("/profile")
def get_profile(pharmacy_id: Optional[str] = None, db: Session = Depends(get_db)):
    svc = OwnerService(db)
    return svc.get_pharmacy_profile(pharmacy_id)


@router.put("/profile")
def update_profile(req: UpdateProfileRequest, db: Session = Depends(get_db)):
    svc = OwnerService(db)
    return svc.update_pharmacy_profile(
        pharmacy_id=req.pharmacy_id,
        name=req.name,
        phone=req.phone,
        email=req.email,
        address=req.address
    )
