import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Numeric, Boolean, Date, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.medicine import Medicine
    from app.models.supplier import Supplier


class MedicineBatch(Base):
    """
    Physical inventory batch received for a specific medicine.
    
    TQM Error Prevention Controls:
    1. CheckConstraint ensures quantity can never be negative (prevents overselling at DB level).
    2. CheckConstraint ensures pricing cannot be negative.
    3. UniqueConstraint on (medicine_id, batch_number) prevents duplicate batch records.
    4. Explicit expiry_date enables query-level blocking of expired medications.
    """
    __tablename__ = "medicine_batches"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_batch_quantity_positive"),
        CheckConstraint("cost_price >= 0", name="ck_batch_cost_price_positive"),
        CheckConstraint("selling_price >= 0", name="ck_batch_selling_price_positive"),
        UniqueConstraint("medicine_id", "batch_number", name="uq_medicine_batch_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the batch record"
    )
    medicine_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("medicines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to the parent medicine catalog item"
    )
    supplier_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Optional supplier from whom this batch was procured"
    )
    batch_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Manufacturer batch or lot number"
    )
    expiry_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="Expiration date stamped on packaging"
    )
    cost_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Procurement cost price per unit"
    )
    selling_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Retail selling price per unit"
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Current physical units available in stock"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Batch availability flag"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Receipt timestamp"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Last modification timestamp"
    )

    # Relationships
    medicine: Mapped["Medicine"] = relationship(
        "Medicine",
        back_populates="batches"
    )
    supplier: Mapped[Optional["Supplier"]] = relationship(
        "Supplier",
        back_populates="batches"
    )

    def is_expired(self) -> bool:
        """Returns True if the batch has passed its expiration date."""
        return self.expiry_date < date.today()

    def __repr__(self) -> str:
        return f"<MedicineBatch(batch='{self.batch_number}', qty={self.quantity}, exp={self.expiry_date})>"
