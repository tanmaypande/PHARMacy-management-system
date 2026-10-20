from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.inventory_service import InventoryService
from app.api.schemas.dashboard import DashboardMetrics

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get("/metrics", response_model=DashboardMetrics)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    service = InventoryService(db)
    return service.get_dashboard_metrics()
