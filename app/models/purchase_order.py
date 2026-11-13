import uuid
from datetime import datetime, timezone
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import String, Text, Integer, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PurchaseOrder(Base):
    """
    Purchase Order entity representing wholesale orders created by the Inventory Manager
    and fulfilled/accepted by the Supplier/Distributor.
    """
    __tablename__ = "purchase_orders"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    po_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    pharmacy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("pharmacies.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="Pending",
        nullable=False,
        index=True,
        doc="Pending, Confirmed, Shipped, Received, Rejected, Cancelled"
    )
    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    expected_delivery_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    supplier_quotation_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    created_by: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    items: Mapped[List["PurchaseOrderItem"]] = relationship(
        "PurchaseOrderItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan"
    )


class PurchaseOrderItem(Base):
    """
    Line items within a Purchase Order.
    """
    __tablename__ = "purchase_order_items"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    medicine_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("medicines.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    quantity_ordered: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    quantity_received: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    unit_cost_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="items"
    )
