"""
Kiosk mode routes for employee self-service time clocking.

Flow:
  1. /kiosk/enter  → enter business access code
  2. /kiosk        → view all employees (no employee logged in yet)
  3. /kiosk/login  → employee enters their credentials
  4. /kiosk/me     → employee personal view (status, punch buttons, colleague list)
  5. /kiosk/punch  → register clock in/out
  6. /kiosk/logout → clear employee session (keep kiosk business active)

All kiosk routes require kiosk_business_id in session.
/kiosk/me and /kiosk/punch also require an employee to be logged in (user_id in session).
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.api.dependencies import (
    flash,
    require_kiosk_active,
    require_kiosk_employee,
    template_context,
    RequiresKioskException,
)
from app.core.flow_debug import flow_log, form_keys
from app.core.security import (
    build_kiosk_session_payload,
    build_kiosk_employee_payload,
)
from app.core.templates import templates
from app.database.business_repository import BusinessRepository
from app.models.employee import Employee
from app.services.auth_service import AuthService
from app.services.employee_service import EmployeeService
from app.services.time_clock_service import TimeClockService


router = APIRouter(prefix="/kiosk", tags=["kiosk"])


# ---------------------------------------------------------------------------
# 1. Business Code Entry
# ---------------------------------------------------------------------------

@router.get("/enter", response_class=HTMLResponse)
async def kiosk_enter_form(request: Request):
    """Display the business code entry form."""
    # If already in kiosk mode with a business, redirect to main view
    if request.session.get("kiosk_business_id"):
        return RedirectResponse("/kiosk", status_code=302)

    ctx = template_context(request)
    return templates.TemplateResponse(request, "kiosk/enter.html", ctx)


@router.post("/enter")
async def kiosk_enter_submit(request: Request):
    """Validate business code and start kiosk mode."""
    form_data = await request.form()
    login_code = str(form_data.get("login_code", "")).strip()

    flow_log("kiosk.enter.form", form_keys=form_keys(form_data))

    if not login_code:
        ctx = template_context(request)
        ctx["error"] = "Por favor ingrese un código de negocio."
        return templates.TemplateResponse(request, "kiosk/enter.html", ctx, status_code=400)

    # Validate business code — active businesses only
    business_repo = BusinessRepository()
    business = business_repo.get_by_login_code(login_code)

    if not business:
        flow_log("kiosk.enter.invalid_code", code=login_code)
        # Distinguish "inactive business" from "code never existed" for a
        # more actionable error message.
        any_business = business_repo.get_by_login_code_any_status(login_code)
        if any_business and not any_business.is_active:
            error = "Este negocio está inactivo. Contacta con tu administrador."
        else:
            error = "Código de negocio no encontrado. Verifica el código e inténtalo de nuevo."
        ctx = template_context(request)
        ctx["error"] = error
        ctx["login_code"] = login_code
        return templates.TemplateResponse(request, "kiosk/enter.html", ctx, status_code=400)

    # Start kiosk mode: save business_id in session
    request.session.update(build_kiosk_session_payload(business.id))
    flow_log("kiosk.enter.success", business_id=business.id, business_name=business.business_name)

    return RedirectResponse("/kiosk", status_code=303)


# ---------------------------------------------------------------------------
# 2. Kiosk Main View (no employee logged in)
# ---------------------------------------------------------------------------

@router.get("", response_class=HTMLResponse)
async def kiosk_main(
    request: Request,
    business_id: str = Depends(require_kiosk_active),
):
    """Display kiosk main view: business name, clock, employee list with status."""
    business_repo = BusinessRepository()
    business = business_repo.get_by_id(business_id)

    if not business:
        # Business was deleted or invalid
        flow_log("kiosk.main.business_not_found", business_id=business_id)
        request.session.clear()
        flash(request, "El código de negocio ya no es válido.", "error")
        return RedirectResponse("/kiosk/enter", status_code=302)

    # Load all clockable employees for this business
    employee_service = EmployeeService(business_id=business_id)
    employees = employee_service.list_clockable_employees()

    # Get their current statuses
    clock_service = TimeClockService(business_id=business_id)
    statuses = clock_service.get_attendance_statuses(employees)

    flow_log(
        "kiosk.main.view",
        business_id=business_id,
        employee_count=len(employees),
        clocked_in_count=sum(1 for s in statuses if s.is_clocked_in),
    )

    ctx = template_context(request)
    ctx.update({
        "business": business,
        "statuses": statuses,
    })
    return templates.TemplateResponse(request, "kiosk/main.html", ctx)


# ---------------------------------------------------------------------------
# 3. Employee Login (in Kiosk)
# ---------------------------------------------------------------------------

@router.get("/login", response_class=HTMLResponse)
async def kiosk_login_form(
    request: Request,
    business_id: str = Depends(require_kiosk_active),
):
    """Display employee login form."""
    business_repo = BusinessRepository()
    business = business_repo.get_by_id(business_id)

    ctx = template_context(request)
    if business:
        ctx["business"] = business
    return templates.TemplateResponse(request, "kiosk/login.html", ctx)


@router.post("/login")
async def kiosk_login_submit(
    request: Request,
    business_id: str = Depends(require_kiosk_active),
):
    """Validate employee credentials and log them in to kiosk."""
    form_data = await request.form()
    identifier = str(form_data.get("identifier", "")).strip()
    password = str(form_data.get("password", ""))

    flow_log("kiosk.login.form", form_keys=form_keys(form_data), business_id=business_id)

    # Authenticate employee
    auth_service = AuthService()
    try:
        employee = auth_service.login(identifier, password)
    except ValueError as exc:
        flow_log("kiosk.login.auth_failed", identifier=identifier, business_id=business_id)
        ctx = template_context(request)
        ctx["error"] = "Usuario o contraseña inválidos."
        ctx["identifier"] = identifier

        business_repo = BusinessRepository()
        business = business_repo.get_by_id(business_id)
        if business:
            ctx["business"] = business

        return templates.TemplateResponse(request, "kiosk/login.html", ctx, status_code=400)

    # Verify employee belongs to this business
    business_repo = BusinessRepository()
    if employee.role != "employee":
        flow_log(
            "kiosk.login.admin_rejected",
            user_id=employee.id,
            business_id=business_id,
        )
        ctx = template_context(request)
        ctx["error"] = "El kiosk es solo para empleados."
        ctx["identifier"] = identifier

        business = business_repo.get_by_id(business_id)
        if business:
            ctx["business"] = business

        return templates.TemplateResponse(request, "kiosk/login.html", ctx, status_code=403)

    if not business_repo.user_has_access(business_id=business_id, user_id=employee.id):
        flow_log(
            "kiosk.login.not_in_business",
            user_id=employee.id,
            business_id=business_id,
        )
        ctx = template_context(request)
        ctx["error"] = "Este empleado no pertenece a este negocio."
        ctx["identifier"] = identifier

        business = business_repo.get_by_id(business_id)
        if business:
            ctx["business"] = business

        return templates.TemplateResponse(request, "kiosk/login.html", ctx, status_code=400)

    # Log employee in: add to session
    request.session.update(build_kiosk_employee_payload(employee))
    flow_log(
        "kiosk.login.success",
        user_id=employee.id,
        business_id=business_id,
    )

    return RedirectResponse("/kiosk/me", status_code=303)


# ---------------------------------------------------------------------------
# 4. Employee Personal View
# ---------------------------------------------------------------------------

@router.get("/me", response_class=HTMLResponse)
async def kiosk_employee_view(
    request: Request,
    auth: tuple[Employee, str] = Depends(require_kiosk_employee),
):
    """Display employee personal kiosk view: status, punch button, colleague list."""
    employee, business_id = auth

    business_repo = BusinessRepository()
    business = business_repo.get_by_id(business_id)

    # Load employee's current status
    clock_service = TimeClockService(business_id=business_id)
    status = clock_service.get_attendance_status(employee)

    # Load all colleagues for the colleague list
    employee_service = EmployeeService(business_id=business_id)
    colleagues = employee_service.list_clockable_employees()
    colleague_statuses = clock_service.get_attendance_statuses(colleagues)

    flow_log(
        "kiosk.me.view",
        user_id=employee.id,
        business_id=business_id,
        is_clocked_in=status.is_clocked_in,
    )

    ctx = template_context(request)
    ctx.update({
        "business": business,
        "employee": employee,
        "status": status,
        "colleague_statuses": colleague_statuses,
    })
    return templates.TemplateResponse(request, "kiosk/me.html", ctx)


# ---------------------------------------------------------------------------
# 5. Clock In/Out
# ---------------------------------------------------------------------------

@router.post("/punch")
async def kiosk_punch(
    request: Request,
    auth: tuple[Employee, str] = Depends(require_kiosk_employee),
):
    """Register clock in or clock out for the logged-in employee."""
    employee, business_id = auth

    form_data = await request.form()
    entry_type = str(form_data.get("entry_type", "")).strip()
    exit_note = str(form_data.get("exit_note", "")).strip() or None
    incident_type = str(form_data.get("incident_type", "")).strip() or None

    flow_log(
        "kiosk.punch.form",
        user_id=employee.id,
        form_keys=form_keys(form_data),
        entry_type=entry_type,
    )

    clock_service = TimeClockService(business_id=business_id)
    try:
        clock_service.register(
            employee_id=employee.id,
            entry_type=entry_type,
            exit_note=exit_note,
            incident_type=incident_type,
        )
        action = "Entrada" if entry_type == "entrada" else "Salida"
        flash(request, f"{action} registrada correctamente.", "success")
        flow_log("kiosk.punch.success", user_id=employee.id, entry_type=entry_type)
    except ValueError as exc:
        flash(request, str(exc), "error")
        flow_log("kiosk.punch.failure", user_id=employee.id, error=str(exc))

    return RedirectResponse("/kiosk/me", status_code=303)


# ---------------------------------------------------------------------------
# 6. Employee Logout (Kiosk Only)
# ---------------------------------------------------------------------------

@router.post("/logout")
async def kiosk_logout(
    request: Request,
    auth: tuple[Employee, str] = Depends(require_kiosk_employee),
):
    """Log out the employee but keep the kiosk business active."""
    employee, business_id = auth

    # Clear only employee session keys; keep kiosk_business_id
    request.session.pop("user_id", None)
    request.session.pop("user_name", None)
    request.session.pop("user_role", None)

    flow_log("kiosk.logout", user_id=employee.id, business_id=business_id)
    flash(request, f"Sesión de {employee.full_name} cerrada.", "info")

    return RedirectResponse("/kiosk/login", status_code=302)
