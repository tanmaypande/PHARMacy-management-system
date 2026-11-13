import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.pharmacy import SupportTicket


class SupportTicketRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, ticket_id: uuid.UUID) -> Optional[SupportTicket]:
        return self.db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()

    def list_tickets(
        self,
        pharmacy_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[SupportTicket]:
        query = self.db.query(SupportTicket)
        if pharmacy_id:
            query = query.filter(SupportTicket.pharmacy_id == pharmacy_id)
        if status and status != "All":
            query = query.filter(SupportTicket.status == status)
        return query.order_by(desc(SupportTicket.created_at)).limit(limit).all()

    def count_open(self) -> int:
        return self.db.query(SupportTicket).filter(SupportTicket.status == "Open").count()

    def create(self, ticket: SupportTicket) -> SupportTicket:
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def update(self, ticket: SupportTicket) -> SupportTicket:
        self.db.commit()
        self.db.refresh(ticket)
        return ticket
