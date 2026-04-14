"""
Employee self-service routes.

This keeps the employee flow independent from the admin dashboard.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.api.dependencies import flash, require_user, template_context
from app.core.flow_debug import flow_log, form_keys
from app.core.templates import templates
from app.models.employee import Employee
from app.services.attendance_report_service import AttendanceReportService
from app.services.time_clock_service import TimeClockService


router = APIRouter(prefix="/me", tags=["employee"])


@router.get("", response_class=HTMLResponse)
async def employee_portal(
    request: Request,
    current_user: Employee = Depends(require_user),
):
    if current_user.role == "admin":
        return RedirectResponse("/dashboard", status_code=302)

    clock_service = TimeClockService()
    report_service = AttendanceReportService()

    status = clock_service.get_attendance_statuses([current_user])[0]
    recent_sessions = report_service.list_session_reports(user_id=current_user.id)[:10]

    flow_log(
        "endpoint.employee_portal.view",
        employee_id=current_user.id,
        is_clocked_in=status.is_clocked_in,
        recent_count=len(recent_sessions),
    )

    ctx = template_context(request)
    ctx.update(
        {
            "employee": current_user,
            "status": status,
            "recent_sessions": recent_sessions,
        }
    )
    return templates.TemplateResponse(request, "employee/portal.html", ctx)


@router.post("/punch")
async def employee_punch(
    request: Request,
    current_user: Employee = Depends(require_user),
):
    if current_user.role != "employee":
        flash(request, "Solo los empleados pueden registrar asistencia.", "error")
        return RedirectResponse("/dashboard", status_code=303)

    form_data = await request.form()
    clock_service = TimeClockService()
    active_session = clock_service.get_active_session(current_user.id)
    entry_type = TimeClockService.EXIT if active_session else TimeClockService.ENTRY

    exit_note = None
    incident_type = None
    if entry_type == TimeClockService.EXIT:
        exit_note = str(form_data.get("exit_note", "")).strip() or None
        incident_type = str(form_data.get("incident_type", "")).strip() or None

    flow_log(
        "frontend.employee_punch.form",
        employee_id=current_user.id,
        form_keys=form_keys(form_data),
        derived_entry_type=entry_type,
        has_exit_note=bool(exit_note),
        incident_type=incident_type,
    )

    try:
        clock_service.register(
            employee_id=current_user.id,
            entry_type=entry_type,
            exit_note=exit_note,
            incident_type=incident_type,
        )
        action = "Entrada" if entry_type == TimeClockService.ENTRY else "Salida"
        flash(request, f"{action} registrada correctamente.", "success")
        flow_log(
            "endpoint.employee_punch.success",
            employee_id=current_user.id,
            entry_type=entry_type,
        )
    except ValueError as exc:
        flash(request, str(exc), "error")
        flow_log(
            "endpoint.employee_punch.failure",
            employee_id=current_user.id,
            entry_type=entry_type,
            error=str(exc),
        )

    return RedirectResponse("/me", status_code=303)
