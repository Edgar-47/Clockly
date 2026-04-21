from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import ApiContext, require_api_business, require_api_permission
from app.api.v1.errors import forbidden, not_found, validation_error
from app.database.expense_repository import ExpenseRepository
from app.schemas.api_v1 import TicketCreateRequest, TicketReviewRequest


router = APIRouter(prefix="/tickets", tags=["api-tickets"])

# Status translation: English API <-> Spanish DB
_STATUS_TO_DB: dict[str, str] = {
    "pending": "pendiente",
    "approved": "aprobado",
    "reimbursed": "reembolsado",
    "rejected": "rechazado",
}
_STATUS_FROM_DB: dict[str, str] = {v: k for k, v in _STATUS_TO_DB.items()}

# Category translation: English API <-> Spanish DB
_CATEGORY_TO_DB: dict[str, str] = {
    "expense": "material",
    "purchase": "suministros",
    "travel": "transporte",
    "food": "comida",
    "other": "otros",
}
_CATEGORY_FROM_DB: dict[str, str] = {v: k for k, v in _CATEGORY_TO_DB.items()}


def _ticket_to_dict(expense) -> dict:
    return {
        "id": expense.id,
        "business_id": expense.business_id,
        "user_id": expense.user_id,
        "title": expense.title,
        "amount": expense.amount,
        "category": _CATEGORY_FROM_DB.get(expense.category, expense.category),
        "status": _STATUS_FROM_DB.get(expense.status, expense.status),
        "date": expense.expense_date,
        "created_at": expense.created_at,
        "description": expense.description,
        "media_url": None,
        "reviewed_by_admin_id": expense.reviewed_by,
        "reviewed_at": expense.reviewed_at,
        "review_note": expense.admin_notes,
        "employee_name": expense.employee_name,
    }


@router.get("")
async def list_tickets(
    status: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    ctx: ApiContext = Depends(require_api_business),
) -> dict:
    repo = ExpenseRepository(business_id=ctx.active_business_id)
    db_status = _STATUS_TO_DB.get(status or "", status) if status else None

    if ctx.active_business_role == "employee":
        expenses = repo.list_by_user(
            ctx.user.id,
            status=db_status,
        )
    elif "reports:view" in ctx.permissions or "employees:manage" in ctx.permissions:
        expenses = repo.list_all(
            status=db_status,
            date_from=from_date,
            date_to=to_date,
        )
    else:
        raise forbidden()

    return {"items": [_ticket_to_dict(e) for e in expenses]}


@router.get("/{ticket_id}")
async def get_ticket(
    ticket_id: int,
    ctx: ApiContext = Depends(require_api_business),
) -> dict:
    repo = ExpenseRepository(business_id=ctx.active_business_id)
    expense = repo.get_by_id(ticket_id)
    if expense is None:
        raise not_found("Ticket no encontrado.")
    if ctx.active_business_role == "employee" and expense.user_id != ctx.user.id:
        raise forbidden()
    return {"ticket": _ticket_to_dict(expense)}


@router.post("")
async def create_ticket(
    payload: TicketCreateRequest,
    ctx: ApiContext = Depends(require_api_business),
) -> dict:
    repo = ExpenseRepository(business_id=ctx.active_business_id)
    db_category = _CATEGORY_TO_DB.get(payload.category, "otros")
    try:
        expense_id = repo.create(
            user_id=ctx.user.id,
            title=payload.title,
            amount=payload.amount,
            expense_date=payload.date,
            description=payload.description,
            category=db_category,
        )
    except Exception as exc:
        raise validation_error(str(exc)) from exc
    expense = repo.get_by_id(expense_id)
    return {"ticket": _ticket_to_dict(expense)}


@router.patch("/{ticket_id}")
async def review_ticket(
    ticket_id: int,
    payload: TicketReviewRequest,
    ctx: ApiContext = Depends(require_api_business),
) -> dict:
    if "employees:manage" not in ctx.permissions and "reports:view" not in ctx.permissions:
        raise forbidden()
    repo = ExpenseRepository(business_id=ctx.active_business_id)
    expense = repo.get_by_id(ticket_id)
    if expense is None:
        raise not_found("Ticket no encontrado.")
    db_status = _STATUS_TO_DB.get(payload.status, payload.status)
    updated = repo.update_status(
        ticket_id,
        status=db_status,
        reviewed_by=ctx.user.id,
        admin_notes=payload.review_note,
    )
    if not updated:
        raise validation_error("No se pudo actualizar el ticket.")
    expense = repo.get_by_id(ticket_id)
    return {"ticket": _ticket_to_dict(expense)}
