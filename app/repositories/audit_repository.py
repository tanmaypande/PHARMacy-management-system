from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import AuditLog
import uuid


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log_action(
        self,
        username: str,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        details: Optional[str] = None
    ) -> AuditLog:
        entry = AuditLog(
            username=username,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            details=details
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_logs(self, limit: int = 100, offset: int = 0) -> List[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())
