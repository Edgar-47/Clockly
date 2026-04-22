from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import TenantContext, require_permission
from app.models.ticket import Ticket
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import TicketCreate, TicketRead


router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=list[TicketRead])
def list_tickets(
    employee_id: UUID | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    ctx: TenantContext = Depends(require_permission("tickets:read")),
    db: Session = Depends(get_db),
) -> list[TicketRead]:
    return TicketRepository(db, company_id=ctx.company_id).list(
        employee_id=employee_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    ctx: TenantContext = Depends(require_permission("tickets:write")),
    db: Session = Depends(get_db),
) -> TicketRead:
    ticket = Ticket(
        company_id=ctx.company_id,
        employee_id=payload.employee_id,
        user_id=ctx.user.id,
        title=payload.title,
        description=payload.description,
        occurred_on=payload.occurred_on,
        attachment_key=payload.attachment_key,
    )
    TicketRepository(db, company_id=ctx.company_id).add(ticket)
    db.commit()
    return ticket

