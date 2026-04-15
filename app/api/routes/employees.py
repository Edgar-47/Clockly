"""
app/api/routes/employees.py

Employee CRUD routes: list, create, edit, toggle active, reset password.
All routes require admin role.

Session 2 additions:
- HR profile (hire_date, department, job_title, contract_type, …) on create + edit.
- Schedule assignment (schedule_id, effective_from) on create + edit.
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.api.dependencies import flash, require_admin, template_context
from app.core.templates import templates
from app.database.employee_profile_repository import EmployeeProfileRepository
from app.models.employee import Employee
from app.models.employee_profile import CONTRACT_TYPE_CHOICES
from app.services.employee_service import EmployeeService
from app.services.work_schedule_service import WorkScheduleService

router = APIRouter(prefix="/employees", tags=["employees"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_schedule_context() -> dict:
    """Returns active schedules for the schedule-assignment dropdown."""
    svc = WorkScheduleService()
    return {
        "active_schedules": svc.list_active_schedules(),
        "contract_type_choices": CONTRACT_TYPE_CHOICES,
    }


def _parse_profile_fields(form_data) -> dict:
    return {
        "hire_date": str(form_data.get("hire_date", "")).strip() or None,
        "contract_type": str(form_data.get("contract_type", "")).strip() or None,
        "department": str(form_data.get("department", "")).strip() or None,
        "job_title": str(form_data.get("job_title", "")).strip() or None,
        "phone": str(form_data.get("phone", "")).strip() or None,
        "personal_email": str(form_data.get("personal_email", "")).strip() or None,
        "emergency_contact_name": str(form_data.get("emergency_contact_name", "")).strip() or None,
        "emergency_contact_phone": str(form_data.get("emergency_contact_phone", "")).strip() or None,
        "social_security_number": str(form_data.get("social_security_number", "")).strip() or None,
        "notes": str(form_data.get("notes", "")).strip() or None,
    }


def _save_profile(user_id: int, fields: dict) -> None:
    EmployeeProfileRepository().upsert(user_id, **fields)


def _maybe_assign_schedule(
    user_id: int,
    form_data,
) -> None:
    """If a schedule_id is provided in form_data, create an assignment."""
    raw = str(form_data.get("schedule_id", "")).strip()
    if not raw or not raw.isdigit():
        return
    schedule_id = int(raw)
    effective_from_raw = str(form_data.get("schedule_effective_from", "")).strip()
    try:
        effective_from = date.fromisoformat(effective_from_raw)
    except (ValueError, TypeError):
        effective_from = date.today()

    svc = WorkScheduleService()
    svc.assign_schedule(
        user_id=user_id,
        schedule_id=schedule_id,
        effective_from=effective_from,
    )


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@router.get("", response_class=HTMLResponse)
async def employee_list(
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    emp_service = EmployeeService()
    sched_service = WorkScheduleService()
    employees = emp_service.list_employees()

    # Build a quick map user_id → current schedule assignment (name + type)
    schedule_by_employee: dict[int, dict] = {}
    for emp in employees:
        assignment = sched_service.get_assignment_record(emp.id)
        if assignment:
            sched = sched_service.get_schedule(assignment.schedule_id)
            if sched:
                schedule_by_employee[emp.id] = {
                    "name": sched.schedule.name,
                    "type": sched.schedule.schedule_type,
                    "type_label": sched.schedule.schedule_type_label,
                    "is_strict": sched.schedule.is_strict,
                }

    ctx = template_context(request)
    ctx["employees"] = employees
    ctx["schedule_by_employee"] = schedule_by_employee
    return templates.TemplateResponse(request, "employees/list.html", ctx)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@router.get("/new", response_class=HTMLResponse)
async def employee_new_form(
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    ctx = template_context(request)
    ctx["form"] = {}
    ctx.update(_load_schedule_context())
    return templates.TemplateResponse(request, "employees/create.html", ctx)


@router.post("/new")
async def employee_create(
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    form_data = await request.form()
    data = {
        "first_name": str(form_data.get("first_name", "")),
        "last_name": str(form_data.get("last_name", "")),
        "dni": str(form_data.get("dni", "")),
        "password": str(form_data.get("password", "")),
        "role": str(form_data.get("role", "employee")),
    }
    profile_fields = _parse_profile_fields(form_data)

    try:
        emp_service = EmployeeService()
        user_id = emp_service.create_employee(**data)

        # Save HR profile (non-blocking — silently skip on error)
        try:
            _save_profile(user_id, profile_fields)
        except Exception:
            pass

        # Assign schedule if provided
        try:
            _maybe_assign_schedule(user_id, form_data)
        except ValueError:
            pass

        flash(request, "Empleado creado correctamente.", "success")
        return RedirectResponse("/employees", status_code=303)
    except ValueError as exc:
        ctx = template_context(request)
        ctx["error"] = str(exc)
        ctx["form"] = {**data, **profile_fields}
        ctx.update(_load_schedule_context())
        return templates.TemplateResponse(request, "employees/create.html", ctx, status_code=400)


# ---------------------------------------------------------------------------
# Edit
# ---------------------------------------------------------------------------

@router.get("/{employee_id}/edit", response_class=HTMLResponse)
async def employee_edit_form(
    employee_id: int,
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    emp_service = EmployeeService()
    sched_service = WorkScheduleService()
    profile_repo = EmployeeProfileRepository()

    employee = emp_service.employee_repository.get_by_id(employee_id)
    if not employee:
        flash(request, "Empleado no encontrado.", "error")
        return RedirectResponse("/employees", status_code=302)

    profile = profile_repo.get_by_user_id(employee_id)
    current_assignment = sched_service.get_assignment_record(employee_id)
    current_schedule = (
        sched_service.get_schedule(current_assignment.schedule_id)
        if current_assignment else None
    )
    assignment_history = sched_service.list_assignments_for_user(employee_id)

    ctx = template_context(request)
    ctx["employee"] = employee
    ctx["profile"] = profile
    ctx["current_assignment"] = current_assignment
    ctx["current_schedule"] = current_schedule
    ctx["assignment_history"] = assignment_history
    ctx.update(_load_schedule_context())
    return templates.TemplateResponse(request, "employees/edit.html", ctx)


@router.post("/{employee_id}/edit")
async def employee_update(
    employee_id: int,
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    form_data = await request.form()
    data = {
        "first_name": str(form_data.get("first_name", "")),
        "last_name": str(form_data.get("last_name", "")),
        "dni": str(form_data.get("dni", "")),
        "role": str(form_data.get("role", "employee")),
        "active": form_data.get("active") is not None,
    }
    profile_fields = _parse_profile_fields(form_data)

    try:
        emp_service = EmployeeService()
        emp_service.update_employee(employee_id, **data)

        try:
            _save_profile(employee_id, profile_fields)
        except Exception:
            pass

        try:
            _maybe_assign_schedule(employee_id, form_data)
        except ValueError as schedule_exc:
            flash(request, f"Datos de empleado guardados, pero horario: {schedule_exc}", "warning")
            return RedirectResponse(f"/employees/{employee_id}/edit", status_code=303)

        flash(request, "Empleado actualizado.", "success")
        return RedirectResponse("/employees", status_code=303)
    except ValueError as exc:
        emp_service = EmployeeService()
        sched_service = WorkScheduleService()
        profile_repo = EmployeeProfileRepository()

        employee = emp_service.employee_repository.get_by_id(employee_id)
        profile = profile_repo.get_by_user_id(employee_id)
        current_assignment = sched_service.get_assignment_record(employee_id)
        current_schedule = (
            sched_service.get_schedule(current_assignment.schedule_id)
            if current_assignment else None
        )
        assignment_history = sched_service.list_assignments_for_user(employee_id)

        ctx = template_context(request)
        ctx["error"] = str(exc)
        ctx["employee"] = employee
        ctx["profile"] = profile
        ctx["current_assignment"] = current_assignment
        ctx["current_schedule"] = current_schedule
        ctx["assignment_history"] = assignment_history
        ctx["form"] = {**data, **profile_fields}
        ctx.update(_load_schedule_context())
        return templates.TemplateResponse(request, "employees/edit.html", ctx, status_code=400)


# ---------------------------------------------------------------------------
# Toggle active / inactive
# ---------------------------------------------------------------------------

@router.post("/{employee_id}/toggle")
async def employee_toggle(
    employee_id: int,
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    try:
        service = EmployeeService()
        new_state = service.toggle_active(employee_id)
        label = "activado" if new_state else "desactivado"
        flash(request, f"Empleado {label}.", "success")
    except ValueError as exc:
        flash(request, str(exc), "error")
    return RedirectResponse("/employees", status_code=303)


# ---------------------------------------------------------------------------
# Password reset (generates a temporary password)
# ---------------------------------------------------------------------------

@router.post("/{employee_id}/reset-password")
async def employee_reset_password(
    employee_id: int,
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    try:
        service = EmployeeService()
        temp_password = service.reset_password(employee_id)
        flash(
            request,
            f"Contraseña temporal generada: {temp_password} — comunícasela al empleado.",
            "success",
        )
    except ValueError as exc:
        flash(request, str(exc), "error")
    return RedirectResponse("/employees", status_code=303)


# ---------------------------------------------------------------------------
# Set password manually
# ---------------------------------------------------------------------------

@router.post("/{employee_id}/set-password")
async def employee_set_password(
    employee_id: int,
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    form_data = await request.form()
    new_password = str(form_data.get("new_password", ""))
    try:
        service = EmployeeService()
        service.set_password(employee_id, new_password)
        flash(request, "Contraseña actualizada.", "success")
    except ValueError as exc:
        flash(request, str(exc), "error")
    return RedirectResponse(f"/employees/{employee_id}/edit", status_code=303)


# ---------------------------------------------------------------------------
# Remove schedule assignment
# ---------------------------------------------------------------------------

@router.post("/{employee_id}/remove-schedule/{assignment_id}")
async def employee_remove_schedule(
    employee_id: int,
    assignment_id: int,
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    try:
        svc = WorkScheduleService()
        svc.deactivate_assignment(assignment_id)
        flash(request, "Asignación de horario eliminada.", "success")
    except Exception as exc:
        flash(request, str(exc), "error")
    return RedirectResponse(f"/employees/{employee_id}/edit", status_code=303)
