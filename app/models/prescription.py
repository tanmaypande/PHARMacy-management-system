import uuid
from datetime import datetime, timezone, date
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.customer import Customer


class Prescription(Base):
    """
    Patient prescription record associated with customer profile.
    """
    __tablename__ = "prescriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    pharmacy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("pharmacies.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    prescription_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )
    doctor_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    doctor_license: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    @property
    def doctor_registration(self) -> Optional[str]:
        return self.doctor_license

    @doctor_registration.setter
    def doctor_registration(self, val: Optional[str]):
        self.doctor_license = val
    prescription_date: Mapped[date] = mapped_column(
        Date,
        default=lambda: datetime.now(timezone.utc).date(),
        nullable=False
    )
    diagnosis: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="Pending",
        nullable=False,
        index=True,
        doc="Pending, Verified, Dispensed, Rejected"
    )
    verified_by: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    dispensing_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
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
    customer: Mapped["Customer"] = relationship("Customer", lazy="joined")
