from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from app.models.tqm import TQMRecord
from app.models.batch import MedicineBatch
from app.models.sale import Sale
from app.models.medicine import Medicine
from app.models.prescription import Prescription
from datetime import date, timedelta
import uuid


class TQMRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, record_id: uuid.UUID) -> Optional[TQMRecord]:
        return self.db.get(TQMRecord, record_id)

    def list_records(self, category: Optional[str] = None, status: Optional[str] = None, skip: int = 0, limit: int = 200) -> List[TQMRecord]:
        stmt = select(TQMRecord)
        if category:
            stmt = stmt.where(TQMRecord.category == category)
        if status:
            stmt = stmt.where(TQMRecord.status == status)
        stmt = stmt.order_by(TQMRecord.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create(self, record: TQMRecord) -> TQMRecord:
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def update(self, record: TQMRecord) -> TQMRecord:
        self.db.commit()
        self.db.refresh(record)
        return record

    def delete(self, record: TQMRecord) -> None:
        self.db.delete(record)
        self.db.commit()

    def calculate_actual_kpis(self) -> Dict[str, Any]:
        """Calculates authentic, un-fabricated clinical quality metrics from live DB rows."""
        today = date.today()
        soon_thresh = today + timedelta(days=30)

        # Batch counts
        all_batches = list(self.db.scalars(select(MedicineBatch).where(MedicineBatch.is_active.is_(True))).all())
        total_batches = len(all_batches)
        expired_count = sum(1 for b in all_batches if b.expiry_date < today)
        near_expiry_count = sum(1 for b in all_batches if today <= b.expiry_date <= soon_thresh)
        depleted_count = sum(1 for b in all_batches if b.quantity == 0)

        # Total medicines and low stock count (<10 units across all lots)
        meds = list(self.db.scalars(select(Medicine).where(Medicine.is_active.is_(True))).all())
        total_meds = len(meds)

        # Sales & Returns metrics
        all_sales = list(self.db.scalars(select(Sale)).all())
        total_sales = len(all_sales)
        refunded_sales = sum(1 for s in all_sales if s.payment_status.lower() == "refunded")
        billing_accuracy_pct = round(((total_sales - refunded_sales) / max(1, total_sales)) * 100, 1)

        # TQM incident resolutions
        tqm_records = list(self.db.scalars(select(TQMRecord)).all())
        total_incidents = len(tqm_records)
        closed_incidents = sum(1 for r in tqm_records if r.status in ("Resolved", "Closed"))
        incident_res_rate = round((closed_incidents / max(1, total_incidents)) * 100, 1) if total_incidents > 0 else 100.0

        expired_pct = round((expired_count / max(1, total_batches)) * 100, 1) if total_batches > 0 else 0.0

        return {
            "total_batches_audited": total_batches,
            "expired_batches": expired_count,
            "expired_stock_percentage": expired_pct,
            "near_expiry_batches": near_expiry_count,
            "depleted_lots": depleted_count,
            "total_medicines_active": total_meds,
            "total_transactions": total_sales,
            "refunded_transactions": refunded_sales,
            "billing_accuracy_percentage": billing_accuracy_pct,
            "total_quality_records": total_incidents,
            "resolved_quality_records": closed_incidents,
            "resolution_rate_percentage": incident_res_rate
        }
