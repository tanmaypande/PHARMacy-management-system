import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class User(Base):
    """
    Multi-stakeholder user with Role-Based Access Control (RBAC).
    Supported Roles:
      - 'super_admin': SaaS Platform owner & multi-pharmacy regulator
      - 'owner': Pharmacy Proprietor (full control of single pharmacy)
      - 'pharmacist': Clinical prescription verification & dispensing safety
      - 'cashier': POS billing, counter cashiering & returns
      - 'inventory_manager': Stock batches, purchase orders, goods receiving
      - 'supplier': Wholesale vendor portal (quotations & PO fulfillment)
      - 'customer': Patient portal (catalog, prescription upload, billing history)
      - 'admin': Legacy administrative alias mapped to owner
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
        doc="Bcrypt/SHA256 hashed password"
    )
    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Full display name of employee or stakeholder"
    )
    role: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="cashier",
        index=True,
        doc="RBAC role: super_admin, owner, pharmacist, cashier, inventory_manager, supplier, customer, admin"
    )
    pharmacy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("pharmacies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Tenant link to specific pharmacy"
    )
    supplier_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Linked vendor profile if role is supplier"
    )
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Linked patient profile if role is customer"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Email address for correspondence"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(25),
        nullable=True,
        doc="Phone number"
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
    pharmacy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("pharmacies.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
