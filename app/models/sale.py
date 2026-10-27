import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.medicine import Medicine
    from app.models.batch import MedicineBatch


class Sale(Base):
    """
    Commercial retail billing and clinical dispensing transaction.
    Represents an immutable financial invoice and clinical checkout.
    """
    __tablename__ = "sales"
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_sale_total_amount_positive"),
        CheckConstraint("subtotal >= 0", name="ck_sale_subtotal_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique transaction identifier"
    )
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Human-readable sequential invoice number (e.g. INV-20261027-0001)"
    )
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Optional reference to registered patient/customer"
    )
    customer_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default="Walk-in Customer",
        doc="Snapshot customer name printed on the receipt"
    )
    customer_phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Customer phone number"
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Sum of line item totals before discount and tax"
    )
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Discount percentage applied"
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Total discount amount deducted"
    )
    tax_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Tax/GST rate applied"
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Calculated tax amount added"
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Grand total payable by customer"
    )
    payment_method: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Cash",
        doc="Tender type: Cash, Credit Card, Debit Card, UPI, Digital Wallet, Insurance"
    )
    payment_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Paid",
        doc="Payment state: Paid, Pending, Refunded"
    )
    cashier_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Pharmacist",
        doc="Name of pharmacist or staff member processing dispensation"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Prescription notes or doctor instructions"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        doc="Billing timestamp"
    )

    # Relationships
    customer: Mapped[Optional["Customer"]] = relationship(
        "Customer",
        back_populates="sales"
    )
    items: Mapped[List["SaleItem"]] = relationship(
        "SaleItem",
        back_populates="sale",
        cascade="all, delete-orphan",
        order_by="SaleItem.created_at"
    )

    def __repr__(self) -> str:
        return f"<Sale(invoice='{self.invoice_number}', total={self.total_amount})>"


class SaleItem(Base):
    """
    Itemized prescription dispensation line attached to a Sale.
    Captures exact product, batch lot, and pricing snapshots at the time of transaction.
    """
    __tablename__ = "sale_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_sale_item_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_sale_item_unit_price_positive"),
        CheckConstraint("subtotal >= 0", name="ck_sale_item_subtotal_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique line item identifier"
    )
    sale_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent sale bill"
    )
    medicine_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("medicines.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Catalog medicine item"
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("medicine_batches.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Specific physical inventory batch lot dispensed"
    )
    medicine_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        doc="Medicine brand name snapshot"
    )
    medicine_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Medicine SKU/barcode snapshot"
    )
    batch_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Manufacturer lot number snapshot"
    )
    expiry_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Batch expiry date snapshot"
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        doc="Selling price per unit at sale time"
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Number of units dispensed"
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        doc="Line subtotal (unit_price * quantity)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    sale: Mapped["Sale"] = relationship("Sale", back_populates="items")
    medicine: Mapped["Medicine"] = relationship("Medicine")
    batch: Mapped["MedicineBatch"] = relationship("MedicineBatch")

    def __repr__(self) -> str:
        return f"<SaleItem(med='{self.medicine_name}', qty={self.quantity}, subtotal={self.subtotal})>"
