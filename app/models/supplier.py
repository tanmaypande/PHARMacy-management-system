import uuid
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.batch import MedicineBatch


class Supplier(Base):
    """
    Wholesale pharmaceutical distributor or vendor supplying medicines.
    """
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the supplier"
    )
    name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        index=True,
        doc="Company or distributor trade name"
    )
    contact_person: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Representative or point of contact"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Phone number"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Email address for purchase orders"
    )
    address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Physical warehouse or corporate address"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Active status"
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

    # Relationship to batches supplied
    batches: Mapped[List["MedicineBatch"]] = relationship(
        "MedicineBatch",
        back_populates="supplier"
    )

    def __repr__(self) -> str:
        return f"<Supplier(name='{self.name}')>"
