import uuid
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.sale import Sale


class Customer(Base):
    """
    Patient or retail customer receiving pharmacy dispensations.
    """
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the customer"
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
        doc="Full customer or patient name"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="Contact phone number"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Email address for e-receipts"
    )
    address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Physical or residential address"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Enrollment timestamp"
    )

    # Relationships
    sales: Mapped[List["Sale"]] = relationship(
        "Sale",
        back_populates="customer"
    )

    def __repr__(self) -> str:
        return f"<Customer(name='{self.name}', phone='{self.phone}')>"
