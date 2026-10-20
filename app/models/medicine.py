import uuid
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.batch import MedicineBatch


class Category(Base):
    """
    Therapeutic category or drug classification (e.g., Antibiotics, Analgesics, Antipyretics).
    Groups medicines for inventory classification and reporting.
    """
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the category"
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique name of the category (e.g. Analgesics)"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Optional description of the category's therapeutic use"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp when the category was created"
    )

    # Relationship to medicines belonging to this category
    medicines: Mapped[List["Medicine"]] = relationship(
        "Medicine",
        back_populates="category",
        cascade="all, delete-orphan",
        passive_deletes=False
    )

    def __repr__(self) -> str:
        return f"<Category(name='{self.name}')>"


class Medicine(Base):
    """
    Master product catalog record for a pharmaceutical product.
    
    IMPORTANT TQM DESIGN RULE:
    Product master data is strictly decoupled from inventory batches.
    Single stock counts and expiry dates are NOT stored here, as a single
    medicine may have multiple active batches with distinct expiry dates,
    cost prices, and stock levels.
    """
    __tablename__ = "medicines"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the medicine"
    )
    medicine_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique stock-keeping unit (SKU) or barcode identifier"
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
        doc="Brand or trade name of the medicine (e.g. Paracetamol 500mg)"
    )
    generic_name: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        index=True,
        doc="Active pharmaceutical ingredient / generic compound (e.g. Acetaminophen)"
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Foreign key reference to parent Category"
    )
    manufacturer: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        doc="Pharmaceutical company or manufacturer"
    )
    unit_of_measurement: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Tablets",
        doc="Unit form (e.g., Tablets, Capsules, Syrup, Strip, Bottle, Ampoule)"
    )
    reorder_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
        doc="Threshold below which inventory alerts are triggered for reordering"
    )
    prescription_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Flag indicating whether a valid doctor prescription is legally required to dispense"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Soft-delete flag: inactive medicines cannot be added to new purchase orders"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Creation timestamp"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Last modification timestamp"
    )

    # Relationship back to Category
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="medicines"
    )

    # Relationship to inventory batches
    batches: Mapped[List["MedicineBatch"]] = relationship(
        "MedicineBatch",
        back_populates="medicine",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Medicine(code='{self.medicine_code}', name='{self.name}')>"
