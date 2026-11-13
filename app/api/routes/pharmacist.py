from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.pharmacist_service import PharmacistService

router = APIRouter(prefix="/api/v1/pharmacist", tags=["Pharmacist Panel"])


class VerifyRxRequest(BaseModel):
    dispensing_notes: str = "Verified for clinical accuracy and safe dosage."


class RejectRxRequest(BaseModel):
    reason: str


@router.get("/dashboard")
def get_dashboard(pharmacy_id: Optional[str] = None, db: Session = Depends(get_db)):
    svc = PharmacistService(db)
    return svc.get_dashboard_metrics(pharmacy_id)


@router.get("/prescriptions")
def list_prescriptions(pharmacy_id: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    svc = PharmacistService(db)
    return svc.list_prescriptions(pharmacy_id=pharmacy_id, status=status)


@router.post("/prescriptions/{prescription_id}/verify")
def verify_prescription(prescription_id: str, req: VerifyRxRequest, db: Session = Depends(get_db)):
    svc = PharmacistService(db)
    try:
        return svc.verify_prescription(prescription_id, req.dispensing_notes)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/prescriptions/{prescription_id}/reject")
def reject_prescription(prescription_id: str, req: RejectRxRequest, db: Session = Depends(get_db)):
    svc = PharmacistService(db)
    try:
        return svc.reject_prescription(prescription_id, req.reason)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/prescriptions/{prescription_id}/dispense")
def dispense_prescription(prescription_id: str, db: Session = Depends(get_db)):
    svc = PharmacistService(db)
    try:
        return svc.dispense_prescription(prescription_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/patient-history/{customer_id}")
def get_patient_history(customer_id: str, db: Session = Depends(get_db)):
    svc = PharmacistService(db)
    return svc.get_patient_medication_history(customer_id)
