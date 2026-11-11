from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.core.database import get_db
from app.services.prescription_service import PrescriptionService
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/prescriptions", tags=["Prescriptions"])


class PrescriptionCreateRequest(BaseModel):
    customer_id: str
    doctor_name: str
    doctor_license: Optional[str] = None
    prescription_date: Optional[str] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None


@router.get("")
def list_prescriptions(customer_id: Optional[str] = None, db: Session = Depends(get_db)):
    svc = PrescriptionService(db)
    return svc.list_prescriptions(customer_id=customer_id)


@router.post("")
def create_prescription(req: PrescriptionCreateRequest, db: Session = Depends(get_db)):
    svc = PrescriptionService(db)
    try:
        return svc.create_prescription(req.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{prescription_id}")
def delete_prescription(prescription_id: str, db: Session = Depends(get_db)):
    svc = PrescriptionService(db)
    try:
        svc.delete_prescription(prescription_id)
        return {"status": "success", "message": "Prescription deleted"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
