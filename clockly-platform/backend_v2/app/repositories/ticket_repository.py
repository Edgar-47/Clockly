from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket


class TicketRepository:
    def __init__(self, db: Session, *, company_id: UUID) -> None:
        self.db = db
        self.company_id = company_id

    def list(
        self,
        *,
        employee_id: UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Ticket]:
        statement = select(Ticket).where(Ticket.company_id == self.company_id)
        if employee_id:
            statement = statement.where(Ticket.employee_id == employee_id)
        if date_from:
            statement = statement.where(Ticket.occurred_on >= date_from)
        if date_to:
            statement = statement.where(Ticket.occurred_on <= date_to)
        statement = statement.order_by(Ticket.created_at.desc())
        return list(self.db.scalars(statement))

    def add(self, ticket: Ticket) -> Ticket:
        self.db.add(ticket)
        self.db.flush()
        return ticket

