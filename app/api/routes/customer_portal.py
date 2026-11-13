from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.customer_portal_service import CustomerPortalService

router = APIRouter(prefix="/api/v1/customer-portal", tags=["Customer Portal"])


class PatientRegisterRequest(BaseModel):
    name: str
    phone: str
    email: str
    address: str
    password: str


class UploadRxRequest(BaseModel):
    doctor_name: str
    doctor_registration: Optional[str] = None
    notes: str = ""
    customer_id: Optional[str] = None


class CustomerTicketRequest(BaseModel):
    sender_name: str
    sender_email: str
    subject: str
    message: str
    customer_id: Optional[str] = None


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_patient(req: PatientRegisterRequest, db: Session = Depends(get_db)):
    svc = CustomerPortalService(db)
    try:
        return svc.register_patient(
            name=req.name,
            phone=req.phone,
            email=req.email,
            address=req.address,
            password=req.password
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/dashboard")
def get_dashboard(customer_id: Optional[str] = None, db: Session = Depends(get_db)):
    svc = CustomerPortalService(db)
    return svc.get_dashboard_metrics(customer_id)


@router.get("/catalog")
def get_catalog(search: Optional[str] = None, db: Session = Depends(get_db)):
    svc = CustomerPortalService(db)
    return svc.get_available_catalog(search)


@router.post("/prescriptions", status_code=status.HTTP_201_CREATED)
def upload_prescription(req: UploadRxRequest, db: Session = Depends(get_db)):
    svc = CustomerPortalService(db)
    try:
        return svc.upload_prescription(
            customer_id=req.customer_id,
            doctor_name=req.doctor_name,
            doctor_registration=req.doctor_registration,
            notes=req.notes
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/prescriptions")
def list_my_prescriptions(customer_id: Optional[str] = None, db: Session = Depends(get_db)):
    svc = CustomerPortalService(db)
    return svc.list_my_prescriptions(customer_id)


@router.get("/orders")
def list_my_orders(customer_id: Optional[str] = None, db: Session = Depends(get_db)):
    svc = CustomerPortalService(db)
    return svc.list_my_orders(customer_id)


@router.post("/support", status_code=status.HTTP_201_CREATED)
def submit_support_ticket(req: CustomerTicketRequest, db: Session = Depends(get_db)):
    svc = CustomerPortalService(db)
    return svc.submit_support_ticket(
        sender_name=req.sender_name,
        sender_email=req.sender_email,
        subject=req.subject,
        message=req.message,
        customer_id=req.customer_id
    )
