"""
app/api/routes/expenses.py

Routes for the Employee Expenses module.

Route order matters — literal segments must be registered before dynamic ones:

  GET  /expenses                      → employee: my expenses list
  GET  /expenses/new                  → create form
  POST /expenses                      → submit new expense
  GET  /expenses/admin                → admin: list all expenses with filters
  GET  /expenses/admin/{id}           → admin: expense detail + management form
  POST /expenses/admin/{id}/review    → admin: update status + notes
  GET  /expenses/attachment/{eid}/{aid} → serve ticket image file
  GET  /expenses/{id}                 → employee: expense detail (own only)
  POST /expenses/{id}/delete          → employee: delete pending expense
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from app.api.dependencies import (
    flash,
    require_active_business,
    require_admin,
    require_user,
    template_context,
)
from app.core.templates import templates
from app.database.employee_repository import EmployeeRepository
from app.models.expense import (
    EXPENSE_CATEGORIES,
    EXPENSE_CATEGORY_LABELS,
    EXPENSE_STATUSES,
    EXPENSE_STATUS_LABELS,
)
from app.services.expense_service import (
    ExpensePermissionError,
    ExpenseService,
    ExpenseValidationError,
)

router = APIRouter(prefix="/expenses", tags=["expenses"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _expense_service(business_id: str | None = None) -> ExpenseService:
    return ExpenseService(business_id=business_id)


def _category_choices() -> list[tuple[str, str]]:
    return [(k, EXPENSE_CATEGORY_LABELS[k]) for k in EXPENSE_CATEGORIES]


def _status_choices() -> list[tuple[str, str]]:
    return [(k, EXPENSE_STATUS_LABELS[k]) for k in EXPENSE_STATUSES]


# ===========================================================================
# EMPLOYEE routes (literal paths first, then dynamic)
# ===========================================================================

@router.get("", response_class=HTMLResponse)
async def expenses_list(
    request: Request,
    status: str = "",
    current_user=Depends(require_user),
):
    """Employee: list my own expenses."""
    business_id = request.session.get("active_business_id")
    svc = _expense_service(business_id)

    expenses = svc.list_my_expenses(current_user.id, status=status or None)
    total = svc.get_my_total(current_user.id)

    ctx = template_context(request)
    ctx.update({
        "expenses": expenses,
        "total": total,
        "filter_status": status,
        "status_choices": _status_choices(),
    })
    return templates.TemplateResponse(request, "expenses/list.html", ctx)


@router.get("/new", response_class=HTMLResponse)
async def expenses_new(
    request: Request,
    current_user=Depends(require_user),
):
    """Employee: show create-expense form."""
    from datetime import date
    ctx = template_context(request)
    ctx.update({
        "category_choices": _category_choices(),
        "today": date.today().isoformat(),
    })
    return templates.TemplateResponse(request, "expenses/create.html", ctx)


@router.post("", response_class=HTMLResponse)
async def expenses_create(
    request: Request,
    title: str = Form(""),
    amount: str = Form(""),
    expense_date: str = Form(""),
    description: str = Form(""),
    category: str = Form("otros"),
    reference_number: str = Form(""),
    currency: str = Form("EUR"),
    files: list[UploadFile] = File(default=[]),
    current_user=Depends(require_user),
):
    """Employee: submit a new expense."""
    business_id = request.session.get("active_business_id")
    svc = _expense_service(business_id)

    valid_files = [f for f in files if f.filename and f.filename.strip()]

    try:
        expense_id = svc.create_expense(
            user_id=current_user.id,
            title=title,
            amount_raw=amount,
            expense_date_raw=expense_date,
            description=description or None,
            category=category,
            currency=currency,
            reference_number=reference_number or None,
        )
    except ExpenseValidationError as exc:
        flash(request, str(exc), "error")
        from datetime import date
        ctx = template_context(request)
        ctx.update({
            "category_choices": _category_choices(),
            "today": date.today().isoformat(),
            "form": {
                "title": title,
                "amount": amount,
                "expense_date": expense_date,
                "description": description,
                "category": category,
                "reference_number": reference_number,
            },
        })
        return templates.TemplateResponse(request, "expenses/create.html", ctx)

    upload_errors: list[str] = []
    for upload in valid_files:
        try:
            file_bytes = await upload.read()
            svc.save_attachment(
                expense_id,
                file_bytes=file_bytes,
                original_filename=upload.filename or "ticket",
                content_type=upload.content_type,
            )
        except ExpenseValidationError as exc:
            upload_errors.append(f"{upload.filename}: {exc}")
        except Exception:
            upload_errors.append(f"{upload.filename}: error al guardar el archivo.")

    if upload_errors:
        flash(
            request,
            "Gasto guardado, pero algunos archivos no se pudieron subir: " + " | ".join(upload_errors),
            "warning",
        )
    else:
        flash(request, "Gasto registrado correctamente.", "success")

    return RedirectResponse(f"/expenses/{expense_id}", status_code=303)


# ===========================================================================
# ADMIN routes — registered before /{expense_id} to avoid path conflicts
# ===========================================================================

@router.get("/admin", response_class=HTMLResponse)
async def expenses_admin_list(
    request: Request,
    status: str = "",
    employee_id: str = "",
    search: str = "",
    date_from: str = "",
    date_to: str = "",
    amount_min: str = "",
    amount_max: str = "",
    business_id: str = Depends(require_active_business),
):
    """Admin: list all expenses with filters and summary counters."""
    svc = _expense_service(business_id)
    repo_employees = EmployeeRepository(business_id=business_id)

    def _parse_float(raw: str) -> float | None:
        try:
            return float(raw.replace(",", ".").strip()) if raw.strip() else None
        except ValueError:
            return None

    def _parse_int(raw: str) -> int | None:
        try:
            return int(raw.strip()) if raw.strip() else None
        except ValueError:
            return None

    expenses = svc.list_all_expenses(
        status=status or None,
        user_id=_parse_int(employee_id),
        search=search or None,
        date_from=date_from or None,
        date_to=date_to or None,
        amount_min=_parse_float(amount_min),
        amount_max=_parse_float(amount_max),
    )
    summary = svc.get_summary()
    employees = repo_employees.list_all()

    ctx = template_context(request)
    ctx.update({
        "expenses": expenses,
        "summary": summary,
        "employees": employees,
        "status_choices": _status_choices(),
        "filter_status": status,
        "filter_employee_id": employee_id,
        "filter_search": search,
        "filter_date_from": date_from,
        "filter_date_to": date_to,
        "filter_amount_min": amount_min,
        "filter_amount_max": amount_max,
    })
    return templates.TemplateResponse(request, "expenses/admin_list.html", ctx)


@router.get("/admin/{expense_id}", response_class=HTMLResponse)
async def expenses_admin_detail(
    request: Request,
    expense_id: int,
    business_id: str = Depends(require_active_business),
):
    """Admin: view and manage a specific expense."""
    svc = _expense_service(business_id)
    try:
        expense = svc.get_expense_for_admin(expense_id)
    except ExpensePermissionError as exc:
        flash(request, str(exc), "error")
        return RedirectResponse("/expenses/admin", status_code=302)

    attachments = svc.get_attachments(expense_id)
    ctx = template_context(request)
    ctx.update({
        "expense": expense,
        "attachments": attachments,
        "status_choices": _status_choices(),
    })
    return templates.TemplateResponse(request, "expenses/admin_detail.html", ctx)


@router.post("/admin/{expense_id}/review", response_class=HTMLResponse)
async def expenses_admin_review(
    request: Request,
    expense_id: int,
    new_status: str = Form(""),
    admin_notes: str = Form(""),
    business_id: str = Depends(require_active_business),
    current_user=Depends(require_admin),
):
    """Admin: change expense status and/or update admin notes."""
    svc = _expense_service(business_id)
    try:
        svc.review_expense(
            expense_id,
            new_status=new_status,
            reviewer_id=current_user.id,
            admin_notes=admin_notes or None,
        )
        flash(request, "Estado del gasto actualizado correctamente.", "success")
    except (ExpensePermissionError, ExpenseValidationError) as exc:
        flash(request, str(exc), "error")

    return RedirectResponse(f"/expenses/admin/{expense_id}", status_code=303)


# ===========================================================================
# FILE SERVING — before /{expense_id} to avoid path conflicts
# ===========================================================================

@router.get("/attachment/{expense_id}/{attachment_id}")
async def expenses_attachment(
    request: Request,
    expense_id: int,
    attachment_id: int,
    current_user=Depends(require_user),
):
    """Serve a ticket attachment image (access-controlled)."""
    business_id = request.session.get("active_business_id")
    svc = _expense_service(business_id)
    is_admin = current_user.role == "admin"

    try:
        if is_admin:
            svc.get_expense_for_admin(expense_id)
        else:
            svc.get_my_expense(expense_id, current_user.id)
    except ExpensePermissionError:
        return RedirectResponse("/expenses", status_code=302)

    attachments = svc.get_attachments(expense_id)
    attachment = next((a for a in attachments if a.id == attachment_id), None)
    if attachment is None:
        return RedirectResponse("/expenses", status_code=302)

    file_path = Path(attachment.file_path)
    if not file_path.exists():
        flash(request, "El archivo no está disponible.", "error")
        return RedirectResponse(f"/expenses/{expense_id}", status_code=302)

    return FileResponse(
        path=str(file_path),
        media_type=attachment.mime_type or "image/jpeg",
        filename=attachment.file_name,
    )


# ===========================================================================
# DYNAMIC routes — after all literal paths
# ===========================================================================

@router.get("/{expense_id}", response_class=HTMLResponse)
async def expenses_detail(
    request: Request,
    expense_id: int,
    current_user=Depends(require_user),
):
    """Employee: view own expense detail."""
    business_id = request.session.get("active_business_id")
    svc = _expense_service(business_id)
    is_admin = current_user.role == "admin"

    try:
        expense = (
            svc.get_expense_for_admin(expense_id)
            if is_admin
            else svc.get_my_expense(expense_id, current_user.id)
        )
    except ExpensePermissionError as exc:
        flash(request, str(exc), "error")
        return RedirectResponse("/expenses", status_code=302)

    attachments = svc.get_attachments(expense_id)
    ctx = template_context(request)
    ctx.update({
        "expense": expense,
        "attachments": attachments,
        "is_admin": is_admin,
    })
    return templates.TemplateResponse(request, "expenses/detail.html", ctx)


@router.post("/{expense_id}/delete", response_class=HTMLResponse)
async def expenses_delete(
    request: Request,
    expense_id: int,
    current_user=Depends(require_user),
):
    """Delete a pending expense (own or admin)."""
    business_id = request.session.get("active_business_id")
    svc = _expense_service(business_id)
    is_admin = current_user.role == "admin"

    try:
        svc.delete_expense(expense_id, user_id=current_user.id, is_admin=is_admin)
        flash(request, "Gasto eliminado.", "success")
    except (ExpensePermissionError, ExpenseValidationError) as exc:
        flash(request, str(exc), "error")

    redirect_to = "/expenses/admin" if is_admin else "/expenses"
    return RedirectResponse(redirect_to, status_code=303)
