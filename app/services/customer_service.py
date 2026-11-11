from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.repositories.customer_repository import CustomerRepository
from app.repositories.audit_repository import AuditRepository
import uuid


class CustomerService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CustomerRepository(db)
        self.audit = AuditRepository(db)

    def list_customers(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        customers = self.repo.list_customers(search=search)
        return [
            {
                "id": str(c.id),
                "name": c.name,
                "phone": c.phone,
                "email": c.email,
                "address": c.address,
                "created_at": c.created_at.isoformat()
            }
            for c in customers
        ]

    def create_customer(self, data: Dict[str, Any], actor: str = "system") -> Dict[str, Any]:
        name = data.get("name", "").strip()
        if not name:
            raise ValueError("Customer / Patient name is required.")

        customer = Customer(
            name=name,
            phone=data.get("phone"),
            email=data.get("email"),
            address=data.get("address")
        )
        created = self.repo.create(customer)
        self.audit.log_action(actor, "CREATE_CUSTOMER", "Customer", str(created.id), f"Enrolled patient {created.name}")
        return {
            "id": str(created.id),
            "name": created.name,
            "phone": created.phone,
            "email": created.email,
            "address": created.address
        }

    def update_customer(self, customer_id: str, data: Dict[str, Any], actor: str = "system") -> Dict[str, Any]:
        c = self.repo.get_by_id(uuid.UUID(customer_id))
        if not c:
            raise ValueError("Customer not found.")

        if "name" in data and data["name"].strip():
            c.name = data["name"].strip()
        if "phone" in data:
            c.phone = data["phone"]
        if "email" in data:
            c.email = data["email"]
        if "address" in data:
            c.address = data["address"]

        updated = self.repo.update(c)
        self.audit.log_action(actor, "UPDATE_CUSTOMER", "Customer", str(updated.id), f"Updated patient {updated.name}")
        return {
            "id": str(updated.id),
            "name": updated.name,
            "phone": updated.phone,
            "email": updated.email,
            "address": updated.address
        }

    def delete_customer(self, customer_id: str, actor: str = "system") -> None:
        c = self.repo.get_by_id(uuid.UUID(customer_id))
        if not c:
            raise ValueError("Customer not found.")
        self.repo.delete(c)
        self.audit.log_action(actor, "DELETE_CUSTOMER", "Customer", str(c.id), f"Deleted patient {c.name}")
