import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Policy(Base):
    """
    Standard Operating Procedures (SOP) & Pharmacy Governance Policies.
    Categories:
      - Store Governance
      - Medicine Handling & Cold Chain Storage
      - Prescription Verification & Dispensing Compliance
      - Inventory & Stock Management
      - Expiry & Hazardous Disposal Protocols
      - Patient Privacy & Data Security (HIPAA / GDPR equivalent)
    """
    __tablename__ = "policies"

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
        String(60),
        nullable=False,
        default="Store Governance"
    )
    version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="1.0"
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    responsible_role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="All Staff"  # Administrator, Pharmacist, Cashier, Inventory Manager, All Staff
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )
    review_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
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
