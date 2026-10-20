import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.inventory_service import InventoryService
from app.api.schemas.batch import BatchCreate, BatchResponse

router = APIRouter(prefix="/api/v1/batches", tags=["Inventory Batches"])


@router.post("", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
def create_batch(payload: BatchCreate, db: Session = Depends(get_db)):
    service = InventoryService(db)
    return service.create_batch(payload)


@router.get("", response_model=List[BatchResponse])
def list_batches(
    medicine_id: Optional[uuid.UUID] = Query(None, description="Filter by Medicine"),
    active_only: bool = Query(True, description="Only active batches"),
    db: Session = Depends(get_db)
):
    service = InventoryService(db)
    return service.list_batches(medicine_id=medicine_id, active_only=active_only)


@router.get("/expiring-soon", response_model=List[BatchResponse])
def list_expiring_soon(
    days: int = Query(30, ge=1, le=365, description="Alert window in days"),
    db: Session = Depends(get_db)
):
    service = InventoryService(db)
    return service.list_expiring_soon(days=days)


@router.get("/expired", response_model=List[BatchResponse])
def list_expired(db: Session = Depends(get_db)):
    service = InventoryService(db)
    return service.list_expired()
