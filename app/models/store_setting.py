from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class StoreSetting(Base):
    """
    Pharmacy store profile, invoice branding, and configuration preferences.
    """
    __tablename__ = "store_settings"

    key: Mapped[str] = mapped_column(
        String(50),
        primary_key=True
    )
    value: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
