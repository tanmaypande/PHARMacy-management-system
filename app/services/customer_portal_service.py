import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.models.user import User
from app.models.prescription import Prescription
from app.models.sale import Sale, SaleItem
from app.models.medicine import Medicine
from app.models.pharmacy import SupportTicket, Pharmacy
from app.services.auth_service import hash_password
from app.repositories.audit_repository import AuditRepository


class CustomerPortalService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_repo = AuditRepository(db)

    def register_patient(
        self,
        name: str,
        phone: str,
        email: str,
        address: str,
        password: str
    ) -> Dict[str, Any]:
        existing_user = self.db.query(User).filter(User.username == email.strip().lower()).first()
        if existing_user:
            raise ValueError(f"An account with email '{email}' already exists.")

        default_p = self.db.query(Pharmacy).first()
        p_id = default_p.id if default_p else None

        # 1. Create Patient record
        customer = Customer(
            name=name.strip(),
            phone=phone.strip(),
            email=email.strip().lower(),
            address=address.strip(),
            pharmacy_id=p_id
        )
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)

        # 2. Create User Login
        user = User(
            username=email.strip().lower(),
            hashed_password=hash_password(password),
            full_name=name.strip(),
            role="customer",
            pharmacy_id=p_id,
            customer_id=customer.id,
            email=email.strip().lower(),
            phone=phone.strip(),
            is_active=True
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        self.audit_repo.log_action(
            user.username,
            "PATIENT_REGISTRATION",
            "Customer",
            str(customer.id),
            f"New patient self-registered: {name}"
        )
        return {
            "customer_id": str(customer.id),
            "username": user.username,
            "name": customer.name,
            "email": customer.email
        }

    def get_dashboard_metrics(self, customer_id: Optional[str] = None) -> Dict[str, Any]:
        c_id = uuid.UUID(customer_id) if customer_id else None
        if not c_id:
            first_c = self.db.query(Customer).first()
            c_id = first_c.id if first_c else None

        if not c_id:
            return {"active_prescriptions": 0, "completed_orders": 0, "total_spent": 0.0}

        rx_count = self.db.query(Prescription).filter(Prescription.customer_id == c_id).count()
        orders_count = self.db.query(Sale).filter(Sale.customer_id == c_id).count()
        total_spent = 0.0
        sales = self.db.query(Sale).filter(Sale.customer_id == c_id).all()
        for s in sales:
            total_spent += float(s.total_amount)

        return {
            "active_prescriptions": rx_count,
            "completed_orders": orders_count,
            "total_spent": round(total_spent, 2)
        }

    def get_available_catalog(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        query = self.db.query(Medicine).filter(Medicine.is_active == True)
        if search:
            s = f"%{search.strip()}%"
            query = query.filter((Medicine.name.ilike(s)) | (Medicine.generic_name.ilike(s)))

        meds = query.limit(50).all()
        result = []
        for m in meds:
            # Check availability
            avail_stock = sum(b.current_stock for b in m.batches if b.current_stock > 0)
            in_stock = avail_stock > 0
            price = float(m.batches[0].selling_price) if m.batches else 0.0

            result.append({
                "id": str(m.id),
                "name": m.name,
                "generic_name": m.generic_name or "N/A",
                "category": m.category.name if m.category else "General",
                "unit": m.unit or "Unit",
                "prescription_required": m.prescription_required,
                "in_stock": in_stock,
                "available_stock": avail_stock,
                "price": price
            })
        return result

    def upload_prescription(
        self,
        customer_id: Optional[str],
        doctor_name: str,
        doctor_registration: Optional[str],
        notes: str,
        actor_username: str = "customer"
    ) -> Dict[str, Any]:
        c_id = uuid.UUID(customer_id) if customer_id else None
        if not c_id:
            first_c = self.db.query(Customer).first()
            c_id = first_c.id if first_c else None

        if not c_id:
            raise ValueError("Patient profile is required to upload a prescription.")

        default_p = self.db.query(Pharmacy).first()
        p_id = default_p.id if default_p else None

        seq = self.db.query(Prescription).count() + 1
        rx_number = f"RX-WEB-{datetime.now(timezone.utc).year}-{seq:04d}"

        rx = Prescription(
            prescription_number=rx_number,
            customer_id=c_id,
            pharmacy_id=p_id,
            doctor_name=doctor_name.strip(),
            doctor_registration=doctor_registration.strip() if doctor_registration else None,
            prescription_date=datetime.now(timezone.utc).date(),
            notes=notes.strip(),
            status="Pending"
        )
        self.db.add(rx)
        self.db.commit()
        self.db.refresh(rx)

        self.audit_repo.log_action(
            actor_username,
            "UPLOAD_PRESCRIPTION",
            "Prescription",
            str(rx.id),
            f"Patient uploaded prescription {rx.prescription_number} for clinical review"
        )
        return {
            "id": str(rx.id),
            "rx_number": rx.prescription_number,
            "status": rx.status,
            "doctor_name": rx.doctor_name
        }

    def list_my_prescriptions(self, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        c_id = uuid.UUID(customer_id) if customer_id else None
        if not c_id:
            first_c = self.db.query(Customer).first()
            c_id = first_c.id if first_c else None

        if not c_id:
            return []

        rxs = (
            self.db.query(Prescription)
            .filter(Prescription.customer_id == c_id)
            .order_by(Prescription.created_at.desc())
            .all()
        )
        return [
            {
                "id": str(r.id),
                "rx_number": r.prescription_number,
                "doctor_name": r.doctor_name,
                "status": r.status or "Pending",
                "notes": r.notes or "",
                "dispensing_notes": getattr(r, "dispensing_notes", "") or "",
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")
            }
            for r in rxs
        ]

    def list_my_orders(self, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        c_id = uuid.UUID(customer_id) if customer_id else None
        if not c_id:
            first_c = self.db.query(Customer).first()
            c_id = first_c.id if first_c else None

        if not c_id:
            return []

        sales = (
            self.db.query(Sale)
            .filter(Sale.customer_id == c_id)
            .order_by(Sale.created_at.desc())
            .all()
        )
        return [
            {
                "id": str(s.id),
                "invoice_number": s.invoice_number,
                "sale_date": s.created_at.strftime("%Y-%m-%d %H:%M"),
                "total_amount": float(s.total_amount),
                "payment_status": s.payment_status,
                "payment_method": s.payment_method,
                "items_count": len(s.items)
            }
            for s in sales
        ]

    def submit_support_ticket(
        self,
        sender_name: str,
        sender_email: str,
        subject: str,
        message: str,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        c_id = uuid.UUID(customer_id) if customer_id else None
        default_p = self.db.query(Pharmacy).first()
        p_id = default_p.id if default_p else None

        seq = self.db.query(SupportTicket).count() + 1
        tck_num = f"TCK-PAT-{seq:04d}"

        ticket = SupportTicket(
            ticket_number=tck_num,
            pharmacy_id=p_id,
            sender_name=sender_name.strip(),
            sender_email=sender_email.strip(),
            subject=subject.strip(),
            message=message.strip(),
            priority="Low",
            status="Open"
        )
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return {"id": str(ticket.id), "ticket_number": ticket.ticket_number, "status": ticket.status}
