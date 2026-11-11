from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.core.database import get_db
from app.services.tqm_service import TQMService
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/tqm", tags=["Total Quality Management (TQM)"])


class TQMRecordCreate(BaseModel):
    title: str
    category: str = "Audit"
    severity: str = "Medium"
    status: str = "Open"
    description: str
    action_plan: Optional[str] = None
    reported_by: Optional[str] = None


@router.get("/records")
def list_records(category: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    svc = TQMService(db)
    return svc.list_records(category=category, status=status)


@router.post("/records")
def create_record(req: TQMRecordCreate, db: Session = Depends(get_db)):
    svc = TQMService(db)
    try:
        return svc.create_record(req.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/records/{record_id}")
def update_record(record_id: str, req: TQMRecordCreate, db: Session = Depends(get_db)):
    svc = TQMService(db)
    try:
        return svc.update_record(record_id, req.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/records/{record_id}")
def delete_record(record_id: str, db: Session = Depends(get_db)):
    svc = TQMService(db)
    try:
        svc.delete_record(record_id)
        return {"status": "success", "message": "Record deleted"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/kpis")
def get_kpis(db: Session = Depends(get_db)):
    svc = TQMService(db)
    return svc.get_quality_dashboard_kpis()
