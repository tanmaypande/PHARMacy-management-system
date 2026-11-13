import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.pharmacy import Pharmacy, Subscription, SupportTicket
from app.models.user import User, AuditLog
from app.repositories.pharmacy_repository import PharmacyRepository
from app.repositories.user_repository import UserRepository
from app.repositories.support_ticket_repository import SupportTicketRepository
from app.repositories.audit_repository import AuditRepository
from app.services.auth_service import hash_password


class SuperAdminService:
    def __init__(self, db: Session):
        self.db = db
        self.pharmacy_repo = PharmacyRepository(db)
        self.user_repo = UserRepository(db)
        self.ticket_repo = SupportTicketRepository(db)
        self.audit_repo = AuditRepository(db)

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        total_pharmacies = self.pharmacy_repo.count_total()
        active_pharmacies = self.pharmacy_repo.count_active()
        suspended_pharmacies = self.pharmacy_repo.count_suspended()
        total_users = self.db.query(User).count()
        total_subscriptions = self.db.query(Subscription).count()
        open_tickets = self.ticket_repo.count_open()

        recent_logs = (
            self.db.query(AuditLog)
            .order_by(AuditLog.timestamp.desc())
            .limit(10)
            .all()
        )

        return {
            "total_registered_pharmacies": total_pharmacies,
            "active_pharmacies": active_pharmacies,
            "suspended_pharmacies": suspended_pharmacies,
            "total_system_users": total_users,
            "total_active_subscriptions": total_subscriptions,
            "pending_support_tickets": open_tickets,
            "recent_audit_trail": [
                {
                    "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "username": l.username,
                    "action": l.action,
                    "entity_type": l.entity_type,
                    "details": l.details
                }
                for l in recent_logs
            ]
        }

    def list_pharmacies(self) -> List[Dict[str, Any]]:
        pharmacies = self.pharmacy_repo.list_all()
        result = []
        for p in pharmacies:
            latest_sub = p.subscriptions[0] if p.subscriptions else None
            result.append({
                "id": str(p.id),
                "name": p.name,
                "license_number": p.license_number,
                "owner_name": p.owner_name,
                "phone": p.phone,
                "email": p.email,
                "address": p.address or "",
                "status": p.status,
                "subscription_plan": p.subscription_plan,
                "subscription_status": latest_sub.status if latest_sub else "N/A",
                "created_at": p.created_at.strftime("%Y-%m-%d")
            })
        return result

    def register_pharmacy(
        self,
        name: str,
        license_number: str,
        owner_name: str,
        phone: str,
        email: str,
        address: str,
        subscription_plan: str,
        owner_username: str,
        owner_password: str,
        actor_username: str = "superadmin"
    ) -> Dict[str, Any]:
        existing_p = self.pharmacy_repo.get_by_license(license_number.strip())
        if existing_p:
            raise ValueError(f"Pharmacy with license '{license_number}' is already registered.")

        existing_user = self.user_repo.get_by_username(owner_username.strip())
        if existing_user:
            raise ValueError(f"Username '{owner_username}' already exists.")

        # 1. Create Pharmacy
        pharmacy = Pharmacy(
            name=name.strip(),
            license_number=license_number.strip(),
            owner_name=owner_name.strip(),
            phone=phone.strip(),
            email=email.strip(),
            address=address.strip(),
            status="active",
            subscription_plan=subscription_plan
        )
        created_pharmacy = self.pharmacy_repo.create(pharmacy)

        # 2. Create Active Subscription
        now = datetime.now(timezone.utc)
        sub = Subscription(
            pharmacy_id=created_pharmacy.id,
            plan_name=subscription_plan,
            status="active",
            price=Decimal("299.00") if subscription_plan == "Enterprise" else Decimal("149.00"),
            billing_cycle="annual",
            start_date=now,
            end_date=now + timedelta(days=365)
        )
        self.pharmacy_repo.create_subscription(sub)

        # 3. Create Pharmacy Owner User Account
        owner_user = User(
            username=owner_username.strip(),
            hashed_password=hash_password(owner_password),
            full_name=owner_name.strip(),
            role="owner",
            pharmacy_id=created_pharmacy.id,
            email=email.strip(),
            phone=phone.strip(),
            is_active=True
        )
        self.user_repo.create(owner_user)

        self.audit_repo.log_action(
            actor_username,
            "REGISTER_PHARMACY",
            "Pharmacy",
            str(created_pharmacy.id),
            f"Onboarded pharmacy '{name}' with owner account '{owner_username}'"
        )

        return {
            "pharmacy_id": str(created_pharmacy.id),
            "name": created_pharmacy.name,
            "license_number": created_pharmacy.license_number,
            "owner_username": owner_user.username,
            "status": created_pharmacy.status
        }

    def toggle_pharmacy_status(self, pharmacy_id: str, actor_username: str = "superadmin") -> Dict[str, Any]:
        p = self.pharmacy_repo.get_by_id(uuid.UUID(pharmacy_id))
        if not p:
            raise ValueError("Pharmacy not found.")

        p.status = "suspended" if p.status == "active" else "active"
        updated = self.pharmacy_repo.update(p)

        # If suspended, deactivate all pharmacy employees
        if updated.status == "suspended":
            self.db.query(User).filter(User.pharmacy_id == p.id).update({"is_active": False})
            self.db.commit()
        else:
            self.db.query(User).filter(User.pharmacy_id == p.id).update({"is_active": True})
            self.db.commit()

        self.audit_repo.log_action(
            actor_username,
            "TOGGLE_PHARMACY_STATUS",
            "Pharmacy",
            str(p.id),
            f"Pharmacy '{p.name}' status changed to {p.status}"
        )
        return {"id": str(p.id), "name": p.name, "status": p.status}

    def list_subscriptions(self) -> List[Dict[str, Any]]:
        subs = self.pharmacy_repo.list_subscriptions()
        return [
            {
                "id": str(s.id),
                "pharmacy_name": s.pharmacy.name if s.pharmacy else "Unknown",
                "plan_name": s.plan_name,
                "status": s.status,
                "price": float(s.price),
                "billing_cycle": s.billing_cycle,
                "start_date": s.start_date.strftime("%Y-%m-%d"),
                "end_date": s.end_date.strftime("%Y-%m-%d")
            }
            for s in subs
        ]

    def list_support_tickets(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        tickets = self.ticket_repo.list_tickets(status=status)
        return [
            {
                "id": str(t.id),
                "ticket_number": t.ticket_number,
                "pharmacy_name": t.pharmacy.name if t.pharmacy else "Customer / General",
                "sender_name": t.sender_name,
                "sender_email": t.sender_email,
                "subject": t.subject,
                "message": t.message,
                "priority": t.priority,
                "status": t.status,
                "response": t.response or "",
                "created_at": t.created_at.strftime("%Y-%m-%d %H:%M")
            }
            for t in tickets
        ]

    def reply_support_ticket(
        self,
        ticket_id: str,
        response: str,
        status: str = "Resolved",
        actor_username: str = "superadmin"
    ) -> Dict[str, Any]:
        ticket = self.ticket_repo.get_by_id(uuid.UUID(ticket_id))
        if not ticket:
            raise ValueError("Ticket not found.")
        ticket.response = response.strip()
        ticket.status = status
        updated = self.ticket_repo.update(ticket)
        self.audit_repo.log_action(
            actor_username,
            "REPLY_TICKET",
            "SupportTicket",
            str(ticket.id),
            f"Responded to ticket {ticket.ticket_number} (status={status})"
        )
        return {"id": str(updated.id), "ticket_number": updated.ticket_number, "status": updated.status}

    def get_system_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        logs = self.db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
        return [
            {
                "id": str(l.id),
                "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "username": l.username,
                "action": l.action,
                "entity_type": l.entity_type,
                "entity_id": l.entity_id or "",
                "details": l.details or ""
            }
            for l in logs
        ]
