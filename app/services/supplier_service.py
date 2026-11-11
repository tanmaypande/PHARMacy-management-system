from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.supplier import Supplier
from app.repositories.supplier_repository import SupplierRepository
from app.repositories.audit_repository import AuditRepository
import uuid


class SupplierService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SupplierRepository(db)
        self.audit = AuditRepository(db)

    def list_suppliers(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        suppliers = self.repo.list_suppliers(search=search)
        return [
            {
                "id": str(s.id),
                "name": s.name,
                "contact_person": s.contact_person,
                "phone": s.phone,
                "email": s.email,
                "address": s.address,
                "is_active": s.is_active,
                "created_at": s.created_at.isoformat()
            }
            for s in suppliers
        ]

    def create_supplier(self, data: Dict[str, Any], actor: str = "system") -> Dict[str, Any]:
        name = data.get("name", "").strip()
        if not name:
            raise ValueError("Supplier company name is required.")
        if self.repo.get_by_name(name):
            raise ValueError(f"Supplier '{name}' already exists.")

        supplier = Supplier(
            name=name,
            contact_person=data.get("contact_person"),
            phone=data.get("phone"),
            email=data.get("email"),
            address=data.get("address"),
            is_active=data.get("is_active", True)
        )
        created = self.repo.create(supplier)
        self.audit.log_action(actor, "CREATE_SUPPLIER", "Supplier", str(created.id), f"Created supplier {created.name}")
        return {
            "id": str(created.id),
            "name": created.name,
            "contact_person": created.contact_person,
            "phone": created.phone,
            "email": created.email,
            "address": created.address,
            "is_active": created.is_active
        }

    def update_supplier(self, supplier_id: str, data: Dict[str, Any], actor: str = "system") -> Dict[str, Any]:
        s = self.repo.get_by_id(uuid.UUID(supplier_id))
        if not s:
            raise ValueError("Supplier not found.")

        if "name" in data and data["name"].strip():
            new_name = data["name"].strip()
            existing = self.repo.get_by_name(new_name)
            if existing and existing.id != s.id:
                raise ValueError(f"Supplier '{new_name}' already exists.")
            s.name = new_name

        if "contact_person" in data:
            s.contact_person = data["contact_person"]
        if "phone" in data:
            s.phone = data["phone"]
        if "email" in data:
            s.email = data["email"]
        if "address" in data:
            s.address = data["address"]
        if "is_active" in data:
            s.is_active = bool(data["is_active"])

        updated = self.repo.update(s)
        self.audit.log_action(actor, "UPDATE_SUPPLIER", "Supplier", str(updated.id), f"Updated supplier {updated.name}")
        return {
            "id": str(updated.id),
            "name": updated.name,
            "contact_person": updated.contact_person,
            "phone": updated.phone,
            "email": updated.email,
            "address": updated.address,
            "is_active": updated.is_active
        }

    def delete_supplier(self, supplier_id: str, actor: str = "system") -> None:
        s = self.repo.get_by_id(uuid.UUID(supplier_id))
        if not s:
            raise ValueError("Supplier not found.")
        self.repo.delete(s)
        self.audit.log_action(actor, "DELETE_SUPPLIER", "Supplier", str(s.id), f"Deleted supplier {s.name}")
