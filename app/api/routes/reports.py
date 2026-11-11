from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.core.database import get_db
from app.services.report_service import ReportService
from app.utils.backup import backup_database
from app.repositories.store_setting_repository import StoreSettingRepository
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/reports", tags=["Reports & Analytics"])


@router.get("/sales-summary")
def get_sales_summary(days: int = 30, db: Session = Depends(get_db)):
    svc = ReportService(db)
    return svc.get_sales_summary(days=days)


@router.get("/inventory-valuation")
def get_inventory_valuation(db: Session = Depends(get_db)):
    svc = ReportService(db)
    return svc.get_inventory_valuation()


@router.post("/export-sales-csv")
def export_sales_csv(days: int = 30, db: Session = Depends(get_db)):
    svc = ReportService(db)
    path = f"exports/sales_report_{days}days.csv"
    exported_file = svc.export_sales_csv(path, days=days)
    return {"status": "success", "file_path": exported_file}


@router.post("/backup")
def create_backup():
    res = backup_database()
    return res


@router.get("/settings")
def get_store_settings(db: Session = Depends(get_db)):
    repo = StoreSettingRepository(db)
    return repo.get_all()


class SettingUpdate(BaseModel):
    settings: Dict[str, str]


@router.post("/settings")
def update_store_settings(req: SettingUpdate, db: Session = Depends(get_db)):
    repo = StoreSettingRepository(db)
    for k, v in req.settings.items():
        repo.set_value(k, str(v))
    return {"status": "success", "settings": repo.get_all()}
