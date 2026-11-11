import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Numeric, Integer, DateTime, ForeignKey, CheckConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.supplier import Supplier
    from app.models.medicine import Medicine


class Purchase(Base):
    """
    Inbound purchase invoice / consignment received from a pharmaceutical supplier.
    """
    __tablename__ = "purchases"
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_purchase_total_amount_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    purchase_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="RECEIVED"  # RECEIVED, PENDING, CANCELLED
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    supplier: Mapped["Supplier"] = relationship("Supplier", lazy="joined")
    items: Mapped[List["PurchaseItem"]] = relationship(
        "PurchaseItem",
        back_populates="purchase",
        cascade="all, delete-orphan",
        lazy="joined"
    )


class PurchaseItem(Base):
    """
    Line item in an inbound purchase invoice.
    """
    __tablename__ = "purchase_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_purchase_item_quantity_positive"),
        CheckConstraint("unit_cost >= 0", name="ck_purchase_item_unit_cost_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    purchase_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("purchases.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    medicine_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("medicines.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    batch_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    # Relationships
    purchase: Mapped["Purchase"] = relationship("Purchase", back_populates="items")
    medicine: Mapped["Medicine"] = relationship("Medicine", lazy="joined")
