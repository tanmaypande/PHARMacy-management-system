import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class User(Base):
    """
    System user with Role-Based Access Control (RBAC).
    Roles:
      - 'admin': Full administrative and system control
      - 'pharmacist': Formulary, batches, purchases, dispensing
      - 'cashier': POS Billing, sales inquiry only
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the user"
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique username for authentication"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Bcrypt hashed password"
    )
    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Full display name of employee"
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="cashier",
        doc="RBAC role: admin, pharmacist, or cashier"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether this user account is active"
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of most recent login"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Account creation timestamp"
    )


class AuditLog(Base):
    """
    Immutable audit trail for TQM process control and regulatory compliance.
    """
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    entity_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
