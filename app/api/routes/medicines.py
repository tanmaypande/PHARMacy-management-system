import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.medicine_service import MedicineService
from app.api.schemas.medicine import MedicineCreate, MedicineUpdate, MedicineResponse

router = APIRouter(prefix="/api/v1/medicines", tags=["Medicines"])


@router.post("", response_model=MedicineResponse, status_code=status.HTTP_201_CREATED)
def create_medicine(payload: MedicineCreate, db: Session = Depends(get_db)):
    service = MedicineService(db)
    return service.create_medicine(payload)


@router.get("", response_model=List[MedicineResponse])
def list_medicines(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None, description="Search by name, code, or generic name"),
    category_id: Optional[uuid.UUID] = Query(None, description="Filter by Category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    service = MedicineService(db)
    medicines, _ = service.list_medicines(
        skip=skip,
        limit=limit,
        search=search,
        category_id=category_id,
        is_active=is_active
    )
    return medicines


@router.get("/{medicine_id}", response_model=MedicineResponse)
def get_medicine(medicine_id: uuid.UUID, db: Session = Depends(get_db)):
    service = MedicineService(db)
    return service.get_medicine(medicine_id)


@router.put("/{medicine_id}", response_model=MedicineResponse)
def update_medicine(medicine_id: uuid.UUID, payload: MedicineUpdate, db: Session = Depends(get_db)):
    service = MedicineService(db)
    return service.update_medicine(medicine_id, payload)


@router.delete("/{medicine_id}", response_model=MedicineResponse)
def deactivate_medicine(medicine_id: uuid.UUID, db: Session = Depends(get_db)):
    service = MedicineService(db)
    return service.deactivate_medicine(medicine_id)
