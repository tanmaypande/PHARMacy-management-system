import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Role(Base):
    """
    Role definition in the Role-Based Access Control (RBAC) engine.
    """
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="super_admin, owner, pharmacist, cashier, inventory_manager, supplier, customer"
    )
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan"
    )


class Permission(Base):
    """
    Granular action permission (e.g. 'medicines:read', 'sales:create', 'pharmacies:manage').
    """
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    module: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    role_permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="permission",
        cascade="all, delete-orphan"
    )


class RolePermission(Base):
    """
    Many-to-many link binding Permissions to Roles.
    """
    __tablename__ = "role_permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="permissions"
    )
    permission: Mapped["Permission"] = relationship(
        "Permission",
        back_populates="role_permissions"
    )
