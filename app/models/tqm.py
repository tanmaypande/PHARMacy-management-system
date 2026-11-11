import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class TQMRecord(Base):
    """
    Total Quality Management (TQM) record:
    Tracks Quality Audits, Incidents/Errors, CAPA (Corrective and Preventive Actions),
    and Quality Inspection logs.
    """
    __tablename__ = "tqm_records"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Audit"  # Audit, CAPA, Incident, Inspection, Compliance
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Medium"  # Low, Medium, High, Critical
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Open"  # Open, Under Review, Resolved, Closed
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    action_plan: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    reported_by: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Quality Auditor"
    )
    resolved_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
