"""
app/api/routes/clock.py

Kiosk routes: employee self-service clock in/out.

The kiosk page is designed for a shared tablet at the entrance.
Flow:
  1. Admin opens /clock/kiosk (requires admin session).
  2. Page shows a list of all active employees with their clock status.
  3. Employee taps their name → modal asks for their PIN/password.
  4. POST /clock/punch validates password and toggles clock state.
  5. Page refreshes showing updated status.

This route is intentionally separated from /employees (admin CRUD)
to allow a clean tablet experience.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.api.dependencies import flash, require_admin, template_context
from app.core.flow_debug import flow_log, form_keys
from app.core.templates import templates
from app.models.employee import Employee
from app.services.auth_service import AuthService
from app.services.employee_service import EmployeeService
from app.services.time_clock_service import TimeClockService

router = APIRouter(prefix="/clock", tags=["clock"])


@router.get("/kiosk", response_class=HTMLResponse)
async def kiosk_view(
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    """
    Kiosk display: all active (clockable) employees with their live status.
    """
    clock_service = TimeClockService()
    employee_service = EmployeeService()

    # Only show employees with role="employee" (not admins) in the kiosk
    employees = employee_service.list_clockable_employees()
    statuses = clock_service.get_attendance_statuses(employees)

    ctx = template_context(request)
    ctx["statuses"] = statuses
    return templates.TemplateResponse(request, "clock/kiosk.html", ctx)


@router.post("/punch")
async def clock_punch(
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    """
    Process a clock punch (in or out) for an employee.

    The employee identifies themselves and provides their password.
    The system validates credentials and registers the punch.

    POST body (form):
      employee_id  (int)
      password     (str)
      entry_type   "entrada" | "salida"
      exit_note    (str, optional) — note on exit
      incident_type (str, optional) — incident category on exit
    """
    form_data = await request.form()
    try:
        employee_id = int(str(form_data.get("employee_id", 0)))
        password = str(form_data.get("password", ""))
        entry_type = str(form_data.get("entry_type", "")).strip()
        exit_note = str(form_data.get("exit_note", "")).strip() or None
        incident_type = str(form_data.get("incident_type", "")).strip() or None
    except (ValueError, TypeError):
        flash(request, "Datos de fichaje incorrectos.", "error")
        return RedirectResponse("/clock/kiosk", status_code=303)

    flow_log(
        "frontend.kiosk_punch.form",
        form_keys=form_keys(form_data),
        employee_id=employee_id,
        entry_type=entry_type,
        has_exit_note=bool(exit_note),
        incident_type=incident_type,
    )

    # Validate employee password before registering the punch
    auth_service = AuthService()
    try:
        auth_service.verify_employee_password(employee_id, password)
    except ValueError:
        flash(request, "Contraseña incorrecta.", "error")
        return RedirectResponse("/clock/kiosk", status_code=303)

    # Register the punch
    clock_service = TimeClockService()
    try:
        clock_service.register(
            employee_id=employee_id,
            entry_type=entry_type,
            exit_note=exit_note,
            incident_type=incident_type,
        )
        action = "Entrada" if entry_type == "entrada" else "Salida"
        flash(request, f"{action} registrada correctamente.", "success")
        flow_log(
            "endpoint.kiosk_punch.success",
            employee_id=employee_id,
            entry_type=entry_type,
        )
    except ValueError as exc:
        flash(request, str(exc), "error")
        flow_log(
            "endpoint.kiosk_punch.failure",
            employee_id=employee_id,
            entry_type=entry_type,
            error=str(exc),
        )

    return RedirectResponse("/clock/kiosk", status_code=303)
