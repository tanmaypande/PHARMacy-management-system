import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.super_admin_service import SuperAdminService

router = APIRouter(prefix="/api/v1/super-admin", tags=["Super Admin Panel"])


class RegisterPharmacyRequest(BaseModel):
    name: str
    license_number: str
    owner_name: str
    phone: str
    email: str
    address: str
    subscription_plan: str = "Enterprise"
    owner_username: str
    owner_password: str


class ReplyTicketRequest(BaseModel):
    response: str
    status: str = "Resolved"


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    svc = SuperAdminService(db)
    return svc.get_dashboard_metrics()


@router.get("/pharmacies")
def list_pharmacies(db: Session = Depends(get_db)):
    svc = SuperAdminService(db)
    return svc.list_pharmacies()


@router.post("/pharmacies", status_code=status.HTTP_201_CREATED)
def register_pharmacy(req: RegisterPharmacyRequest, db: Session = Depends(get_db)):
    svc = SuperAdminService(db)
    try:
        return svc.register_pharmacy(
            name=req.name,
            license_number=req.license_number,
            owner_name=req.owner_name,
            phone=req.phone,
            email=req.email,
            address=req.address,
            subscription_plan=req.subscription_plan,
            owner_username=req.owner_username,
            owner_password=req.owner_password
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/pharmacies/{pharmacy_id}/toggle-status")
def toggle_pharmacy_status(pharmacy_id: str, db: Session = Depends(get_db)):
    svc = SuperAdminService(db)
    try:
        return svc.toggle_pharmacy_status(pharmacy_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/subscriptions")
def list_subscriptions(db: Session = Depends(get_db)):
    svc = SuperAdminService(db)
    return svc.list_subscriptions()


@router.get("/support-tickets")
def list_support_tickets(status: Optional[str] = None, db: Session = Depends(get_db)):
    svc = SuperAdminService(db)
    return svc.list_support_tickets(status=status)


@router.put("/support-tickets/{ticket_id}/reply")
def reply_support_ticket(ticket_id: str, req: ReplyTicketRequest, db: Session = Depends(get_db)):
    svc = SuperAdminService(db)
    try:
        return svc.reply_support_ticket(ticket_id, req.response, req.status)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/audit-logs")
def get_audit_logs(limit: int = 100, db: Session = Depends(get_db)):
    svc = SuperAdminService(db)
    return svc.get_system_audit_logs(limit=limit)
