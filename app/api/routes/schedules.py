"""
app/api/routes/schedules.py

Admin management of work schedule templates and employee assignments.
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.api.dependencies import flash, require_admin, template_context
from app.core.templates import templates
from app.models.employee import Employee
from app.services.employee_service import EmployeeService
from app.services.work_schedule_service import WorkScheduleService
from app.database.work_schedule_repository import WorkScheduleRepository

router = APIRouter(prefix="/schedules", tags=["schedules"])

_DOW_NAMES = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@router.get("", response_class=HTMLResponse)
async def list_schedules(
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    service = WorkScheduleService()
    schedules_with_days = service.list_schedules()
    repo = WorkScheduleRepository()
    # Attach assigned employee count per schedule
    assignment_counts = {
        swd.schedule.id: len(repo.list_assignments_for_schedule(swd.schedule.id))
        for swd in schedules_with_days
    }
    ctx = template_context(request)
    ctx.update({
        "schedules": schedules_with_days,
        "assignment_counts": assignment_counts,
        "dow_names": _DOW_NAMES,
    })
    return templates.TemplateResponse(request, "schedules/list.html", ctx)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@router.get("/new", response_class=HTMLResponse)
async def new_schedule_form(
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    ctx = template_context(request)
    ctx["dow_names"] = _DOW_NAMES
    ctx["schedule"] = None
    ctx["days"] = []
    return templates.TemplateResponse(request, "schedules/create.html", ctx)


@router.post("/new")
async def create_schedule(
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    form = await request.form()
    name = str(form.get("name", "")).strip()
    description = str(form.get("description", "")).strip() or None
    weekly_target_raw = str(form.get("weekly_hours_target", "")).strip()
    weekly_target = float(weekly_target_raw) if weekly_target_raw else None
    schedule_type = str(form.get("schedule_type", "flexible")).strip()

    days = _parse_days_from_form(form)

    service = WorkScheduleService()
    try:
        schedule_id = service.create_schedule(
            name=name,
            description=description,
            weekly_hours_target=weekly_target,
            schedule_type=schedule_type,
            days=days,
        )
    except ValueError as exc:
        flash(request, str(exc), "error")
        ctx = template_context(request)
        ctx.update({
            "dow_names": _DOW_NAMES,
            "schedule": None,
            "days": [],
            "form_name": name,
            "form_description": description or "",
        })
        return templates.TemplateResponse(request, "schedules/create.html", ctx)

    flash(request, f"Horario «{name}» creado correctamente.", "success")
    return RedirectResponse(f"/schedules/{schedule_id}", status_code=303)


# ---------------------------------------------------------------------------
# Detail
# ---------------------------------------------------------------------------

@router.get("/{schedule_id}", response_class=HTMLResponse)
async def schedule_detail(
    request: Request,
    schedule_id: int,
    current_user: Employee = Depends(require_admin),
):
    service = WorkScheduleService()
    swd = service.get_schedule(schedule_id)
    if not swd:
        flash(request, "Horario no encontrado.", "error")
        return RedirectResponse("/schedules", status_code=303)

    repo = WorkScheduleRepository()
    assignments = repo.list_assignments_for_schedule(schedule_id)
    all_employees = EmployeeService().list_employees()
    clockable = [e for e in all_employees if e.active and e.role == "employee"]

    ctx = template_context(request)
    ctx.update({
        "swd": swd,
        "assignments": assignments,
        "clockable_employees": clockable,
        "dow_names": _DOW_NAMES,
        "today": date.today().isoformat(),
    })
    return templates.TemplateResponse(request, "schedules/detail.html", ctx)


# ---------------------------------------------------------------------------
# Edit
# ---------------------------------------------------------------------------

@router.get("/{schedule_id}/edit", response_class=HTMLResponse)
async def edit_schedule_form(
    request: Request,
    schedule_id: int,
    current_user: Employee = Depends(require_admin),
):
    service = WorkScheduleService()
    swd = service.get_schedule(schedule_id)
    if not swd:
        flash(request, "Horario no encontrado.", "error")
        return RedirectResponse("/schedules", status_code=303)

    ctx = template_context(request)
    ctx.update({
        "swd": swd,
        "dow_names": _DOW_NAMES,
    })
    return templates.TemplateResponse(request, "schedules/edit.html", ctx)


@router.post("/{schedule_id}/edit")
async def update_schedule(
    request: Request,
    schedule_id: int,
    current_user: Employee = Depends(require_admin),
):
    form = await request.form()
    name = str(form.get("name", "")).strip()
    description = str(form.get("description", "")).strip() or None
    weekly_target_raw = str(form.get("weekly_hours_target", "")).strip()
    weekly_target = float(weekly_target_raw) if weekly_target_raw else None
    schedule_type = str(form.get("schedule_type", "flexible")).strip()
    is_active = form.get("is_active") == "1"
    days = _parse_days_from_form(form)

    service = WorkScheduleService()
    try:
        service.update_schedule(
            schedule_id,
            name=name,
            description=description,
            weekly_hours_target=weekly_target,
            schedule_type=schedule_type,
            is_active=is_active,
            days=days,
        )
    except ValueError as exc:
        flash(request, str(exc), "error")
        swd = service.get_schedule(schedule_id)
        ctx = template_context(request)
        ctx.update({
            "swd": swd,
            "dow_names": _DOW_NAMES,
        })
        return templates.TemplateResponse(request, "schedules/edit.html", ctx)

    flash(request, f"Horario «{name}» actualizado.", "success")
    return RedirectResponse(f"/schedules/{schedule_id}", status_code=303)


# ---------------------------------------------------------------------------
# Delete (soft)
# ---------------------------------------------------------------------------

@router.post("/{schedule_id}/delete")
async def delete_schedule(
    request: Request,
    schedule_id: int,
    current_user: Employee = Depends(require_admin),
):
    service = WorkScheduleService()
    swd = service.get_schedule(schedule_id)
    if swd:
        service.delete_schedule(schedule_id)
        flash(request, f"Horario «{swd.schedule.name}» desactivado.", "info")
    return RedirectResponse("/schedules", status_code=303)


# ---------------------------------------------------------------------------
# Assign employee to schedule
# ---------------------------------------------------------------------------

@router.post("/{schedule_id}/assign")
async def assign_schedule(
    request: Request,
    schedule_id: int,
    current_user: Employee = Depends(require_admin),
):
    form = await request.form()
    user_id_raw = str(form.get("user_id", "")).strip()
    effective_from_raw = str(form.get("effective_from", "")).strip()
    effective_to_raw = str(form.get("effective_to", "")).strip()

    if not user_id_raw or not effective_from_raw:
        flash(request, "Empleado y fecha de inicio son obligatorios.", "error")
        return RedirectResponse(f"/schedules/{schedule_id}", status_code=303)

    try:
        user_id = int(user_id_raw)
        eff_from = date.fromisoformat(effective_from_raw)
        eff_to = date.fromisoformat(effective_to_raw) if effective_to_raw else None
    except (ValueError, TypeError):
        flash(request, "Datos inválidos en el formulario.", "error")
        return RedirectResponse(f"/schedules/{schedule_id}", status_code=303)

    service = WorkScheduleService()
    try:
        service.assign_schedule(
            user_id=user_id,
            schedule_id=schedule_id,
            effective_from=eff_from,
            effective_to=eff_to,
        )
        flash(request, "Horario asignado correctamente.", "success")
    except ValueError as exc:
        flash(request, str(exc), "error")

    return RedirectResponse(f"/schedules/{schedule_id}", status_code=303)


@router.post("/assignments/{assignment_id}/remove")
async def remove_assignment(
    request: Request,
    assignment_id: int,
    current_user: Employee = Depends(require_admin),
):
    form = await request.form()
    schedule_id_raw = str(form.get("schedule_id", "")).strip()
    service = WorkScheduleService()
    service.deactivate_assignment(assignment_id)
    flash(request, "Asignación eliminada.", "info")
    redirect_to = f"/schedules/{schedule_id_raw}" if schedule_id_raw else "/schedules"
    return RedirectResponse(redirect_to, status_code=303)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_days_from_form(form) -> list[dict]:
    """
    Extract day definitions from a multi-row schedule form.
    Expects form fields: day_dow[], day_start[], day_end[],
    day_break[], day_late_tol[], day_early_tol[]
    """
    dows = form.getlist("day_dow")
    starts = form.getlist("day_start")
    ends = form.getlist("day_end")
    breaks = form.getlist("day_break")
    late_tols = form.getlist("day_late_tol")
    early_tols = form.getlist("day_early_tol")

    days = []
    for i, dow in enumerate(dows):
        try:
            days.append({
                "day_of_week": int(dow),
                "start_time": starts[i] if i < len(starts) else "09:00",
                "end_time": ends[i] if i < len(ends) else "17:00",
                "break_minutes": int(breaks[i]) if i < len(breaks) and breaks[i] else 0,
                "late_tolerance_minutes": int(late_tols[i]) if i < len(late_tols) and late_tols[i] else 0,
                "early_leave_tolerance_minutes": int(early_tols[i]) if i < len(early_tols) and early_tols[i] else 0,
            })
        except (ValueError, TypeError):
            continue
    return days
