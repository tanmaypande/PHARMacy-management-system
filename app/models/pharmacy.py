import uuid
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import String, Text, Boolean, Integer, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Pharmacy(Base):
    """
    Tenant entity representing an independent pharmacy registered in the system.
    Enforces multi-stakeholder pharmacy-level tenant isolation.
    """
    __tablename__ = "pharmacies"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique pharmacy tenant ID"
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
        doc="Commercial trade name of the pharmacy"
    )
    license_number: Mapped[str] = mapped_column(
        String(80),
        unique=True,
        nullable=False,
        index=True,
        doc="Official Drug Controller Pharmacy License Number"
    )
    owner_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Primary legal owner / proprietor name"
    )
    phone: Mapped[str] = mapped_column(
        String(25),
        nullable=False,
        doc="Registered pharmacy contact phone"
    )
    email: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Official pharmacy correspondence email"
    )
    address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Physical dispensary address"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
        doc="Account status: active, suspended, pending"
    )
    subscription_plan: Mapped[str] = mapped_column(
        String(50),
        default="Enterprise",
        nullable=False,
        doc="Current software subscription tier"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription",
        back_populates="pharmacy",
        cascade="all, delete-orphan"
    )
    expenses: Mapped[List["Expense"]] = relationship(
        "Expense",
        back_populates="pharmacy",
        cascade="all, delete-orphan"
    )
    support_tickets: Mapped[List["SupportTicket"]] = relationship(
        "SupportTicket",
        back_populates="pharmacy",
        cascade="all, delete-orphan"
    )


class Subscription(Base):
    """
    Subscription plan and license validity for a registered pharmacy.
    """
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    pharmacy_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pharmacies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    plan_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Enterprise"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active"
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("199.00")
    )
    billing_cycle: Mapped[str] = mapped_column(
        String(20),
        default="monthly",
        nullable=False
    )
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    pharmacy: Mapped["Pharmacy"] = relationship(
        "Pharmacy",
        back_populates="subscriptions"
    )


class Expense(Base):
    """
    Operating expenses recorded by the Pharmacy Owner for profit & loss reporting.
    """
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    pharmacy_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pharmacies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Expense category: Rent, Utilities, Salaries, Supplies, Maintenance, Other"
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    expense_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    recorded_by: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    pharmacy: Mapped["Pharmacy"] = relationship(
        "Pharmacy",
        back_populates="expenses"
    )


class StockMovement(Base):
    """
    TQM stock ledger tracking physical movement: Purchase, Sale, Return, Adjustment, Disposal.
    Prevents negative stock and ensures total auditability.
    """
    __tablename__ = "stock_movements"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    pharmacy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("pharmacies.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("medicine_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    movement_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
        doc="PURCHASE, SALE, RETURN, ADJUSTMENT, DISPOSAL"
    )
    quantity_change: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Positive for inbound, negative for outbound"
    )
    balance_after: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Resulting stock level after movement"
    )
    reason: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    performed_by: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class SupportTicket(Base):
    """
    Support inquiries submitted by pharmacies or customers to Super Admin / Support.
    """
    __tablename__ = "support_tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    ticket_number: Mapped[str] = mapped_column(
        String(40),
        unique=True,
        nullable=False,
        index=True
    )
    pharmacy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("pharmacies.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    sender_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    sender_email: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    subject: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        default="Medium",
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="Open",
        nullable=False,
        index=True
    )
    response: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    pharmacy: Mapped[Optional["Pharmacy"]] = relationship(
        "Pharmacy",
        back_populates="support_tickets"
    )


class Notification(Base):
    """
    Cross-stakeholder in-app notifications and alerts.
    """
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    pharmacy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("pharmacies.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    recipient_role: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    recipient_username: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
