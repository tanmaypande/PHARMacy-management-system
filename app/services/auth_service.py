import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.audit_repository import AuditRepository
import uuid


def hash_password(password: str) -> str:
    """Secure SHA-256 password hash with project salt."""
    salt = "medicare_pms_salt_tqm_2026"
    return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.audit_repo = AuditRepository(db)

    def seed_default_admin_if_empty(self) -> None:
        """TQM Error Prevention: Guarantees at least one admin account exists on initial boot."""
        users = self.user_repo.list_users(limit=1)
        if not users:
            admin_user = User(
                username="admin",
                hashed_password=hash_password("admin123"),
                full_name="Dr. Pharmacist (Admin)",
                role="admin",
                is_active=True
            )
            self.user_repo.create(admin_user)
            self.audit_repo.log_action("system", "INITIAL_SEED", "User", str(admin_user.id), "Created initial default admin account")

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        user = self.user_repo.get_by_username(username.strip())
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        self.user_repo.update(user)
        self.audit_repo.log_action(user.username, "LOGIN", "User", str(user.id), "Successful login")

        return {
            "id": str(user.id),
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "pharmacy_id": str(user.pharmacy_id) if user.pharmacy_id else None,
            "supplier_id": str(user.supplier_id) if user.supplier_id else None,
            "customer_id": str(user.customer_id) if user.customer_id else None,
            "email": user.email,
            "phone": user.phone,
            "is_active": user.is_active
        }

    def reset_password(self, username: str, new_password: str, actor_username: str = "system") -> Dict[str, Any]:
        user = self.user_repo.get_by_username(username.strip())
        if not user:
            raise ValueError(f"User '{username}' was not found.")
        user.hashed_password = hash_password(new_password)
        self.user_repo.update(user)
        self.audit_repo.log_action(actor_username, "RESET_PASSWORD", "User", str(user.id), f"Password reset for {user.username}")
        return {"id": str(user.id), "username": user.username, "message": "Password updated successfully."}

    def create_user(
        self,
        username: str,
        password: str,
        full_name: str,
        role: str,
        pharmacy_id: Optional[str] = None,
        supplier_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        actor_username: str = "system"
    ) -> Dict[str, Any]:
        existing = self.user_repo.get_by_username(username.strip())
        if existing:
            raise ValueError(f"Username '{username}' already exists.")

        p_id = uuid.UUID(pharmacy_id) if pharmacy_id else None
        s_id = uuid.UUID(supplier_id) if supplier_id else None
        c_id = uuid.UUID(customer_id) if customer_id else None

        user = User(
            username=username.strip(),
            hashed_password=hash_password(password),
            full_name=full_name.strip(),
            role=role.strip().lower(),
            pharmacy_id=p_id,
            supplier_id=s_id,
            customer_id=c_id,
            email=email.strip() if email else None,
            phone=phone.strip() if phone else None,
            is_active=True
        )
        created = self.user_repo.create(user)
        self.audit_repo.log_action(actor_username, "CREATE_USER", "User", str(created.id), f"Created user {created.username} with role {created.role}")
        return {
            "id": str(created.id),
            "username": created.username,
            "full_name": created.full_name,
            "role": created.role,
            "is_active": created.is_active
        }

    def list_users(self) -> List[Dict[str, Any]]:
        users = self.user_repo.list_users()
        return [
            {
                "id": str(u.id),
                "username": u.username,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "last_login": u.last_login.isoformat() if u.last_login else None
            }
            for u in users
        ]

    def toggle_user_active(self, user_id: str, actor_username: str = "system") -> Dict[str, Any]:
        user = self.user_repo.get_by_id(uuid.UUID(user_id))
        if not user:
            raise ValueError("User not found.")
        user.is_active = not user.is_active
        updated = self.user_repo.update(user)
        self.audit_repo.log_action(actor_username, "TOGGLE_USER_ACTIVE", "User", str(updated.id), f"Active state set to {updated.is_active}")
        return {"id": str(updated.id), "username": updated.username, "is_active": updated.is_active}
