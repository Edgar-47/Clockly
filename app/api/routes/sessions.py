"""
app/api/routes/sessions.py

Session management: list, filter, admin-close, export.
All routes require admin role.

Source of truth: attendance_sessions table (not the legacy time_entries).
"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from app.api.dependencies import flash, require_active_business, require_admin, template_context
from app.core.flow_debug import flow_log
from app.core.templates import templates
from app.models.employee import Employee
from app.models.plan_constants import PlanFeature
from app.services.attendance_report_service import AttendanceReportService
from app.services.employee_service import EmployeeService
from app.services.export_service import ExportService
from app.services.subscription_service import FeatureNotAvailableError, SubscriptionService
from app.services.time_clock_service import TimeClockService

router = APIRouter(prefix="/sessions", tags=["sessions"])

# Default date range shown on first load: last 7 days
_DEFAULT_DAYS = 7


def _default_date_from() -> str:
    return (date.today() - timedelta(days=_DEFAULT_DAYS)).isoformat()


def _default_date_to() -> str:
    return date.today().isoformat()


# ---------------------------------------------------------------------------
# Session list
# ---------------------------------------------------------------------------

@router.get("", response_class=HTMLResponse)
async def session_list(
    request: Request,
    current_user: Employee = Depends(require_admin),
    business_id: str = Depends(require_active_business),
    date_from: str | None = None,
    date_to: str | None = None,
    employee_id: str | None = None,
    user_id: str | None = None,
    is_active: str | None = None,
    incident_filter: str | None = None,
):
    """
    Paginated list of attendance sessions with filters:
      - Date range (from / to)
      - Employee filter
      - Status: all | active | closed
      - Incident filter: all | incidents | previous_open | excess_8 | ...
    """
    report_service = AttendanceReportService(business_id=business_id)
    employee_service = EmployeeService(business_id=business_id)

    flow_log("frontend.sessions.query", query=dict(request.query_params))

    parse_errors: list[str] = []
    effective_date_from = _parse_date_filter(
        date_from,
        fallback=_default_date_from(),
        field_label="fecha desde",
        errors=parse_errors,
    )
    effective_date_to = _parse_date_filter(
        date_to,
        fallback=_default_date_to(),
        field_label="fecha hasta",
        errors=parse_errors,
    )
    selected_employee_id = _parse_employee_filter(
        employee_id=employee_id,
        user_id=user_id,
        errors=parse_errors,
    )
    selected_is_active = _parse_status_filter(is_active, errors=parse_errors)
    selected_incident_filter = _parse_incident_filter(
        incident_filter,
        errors=parse_errors,
    )

    if effective_date_from > effective_date_to:
        parse_errors.append("La fecha desde no puede ser mayor que la fecha hasta.")

    for error in parse_errors:
        flash(request, error, "error")

    flow_log(
        "endpoint.sessions.filters",
        date_from=effective_date_from,
        date_to=effective_date_to,
        employee_id=selected_employee_id,
        is_active=selected_is_active,
        incident_filter=selected_incident_filter,
    )
    sessions = []
    if not parse_errors:
        sessions = report_service.list_session_reports(
            date_from=effective_date_from,
            date_to=effective_date_to,
            employee_id=selected_employee_id,
            is_active=selected_is_active,
            incident_filter=selected_incident_filter,
        )
    flow_log("endpoint.sessions.result", count=len(sessions))

    employees = employee_service.list_employees()

    usage = SubscriptionService().get_usage_summary(business_id)

    ctx = template_context(request)
    ctx.update({
        "sessions": sessions,
        "employees": employees,
        "usage": usage,
        "business_id": business_id,
        "filters": {
            "date_from": effective_date_from,
            "date_to": effective_date_to,
            "employee_id": selected_employee_id,
            "is_active": selected_is_active,
            "incident_filter": selected_incident_filter,
        },
    })
    return templates.TemplateResponse(request, "sessions/list.html", ctx)


# ---------------------------------------------------------------------------
# Admin close session
# ---------------------------------------------------------------------------

@router.post("/{session_id}/close")
async def session_admin_close(
    session_id: int,
    request: Request,
    current_user: Employee = Depends(require_admin),
    business_id: str = Depends(require_active_business),
):
    """Close an active session from the admin panel. Requires a reason."""
    form_data = await request.form()
    reason = str(form_data.get("reason", "")).strip()
    try:
        clock_service = TimeClockService(business_id=business_id)
        clock_service.admin_close_session(
            session_id,
            reason=reason,
            admin_user_id=current_user.id,
        )
        flash(request, "Sesión cerrada correctamente.", "success")
    except ValueError as exc:
        flash(request, str(exc), "error")

    # Redirect back with the same filters from the query string.
    params = _build_redirect_params(request)
    return RedirectResponse(f"/sessions{params}", status_code=303)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

@router.get("/export/excel")
async def export_excel(
    request: Request,
    current_user: Employee = Depends(require_admin),
    business_id: str = Depends(require_active_business),
    date_from: str | None = None,
    date_to: str | None = None,
    employee_id: str | None = None,
    user_id: str | None = None,
    is_active: str | None = None,
    incident_filter: str | None = None,
):
    try:
        SubscriptionService().assert_feature(business_id, PlanFeature.EXPORTS_ADVANCED)
    except FeatureNotAvailableError as exc:
        flash(request, str(exc), "error")
        return RedirectResponse("/sessions", status_code=303)

    effective_date_from = date_from or _default_date_from()
    effective_date_to = date_to or _default_date_to()
    errors: list[str] = []
    selected_employee_id = _parse_employee_filter(
        employee_id=employee_id,
        user_id=user_id,
        errors=errors,
    )
    selected_is_active = _parse_status_filter(is_active, errors=errors)
    selected_incident_filter = _parse_incident_filter(
        incident_filter,
        errors=errors,
    )
    if errors:
        for error in errors:
            flash(request, error, "error")
        return RedirectResponse("/sessions", status_code=303)

    try:
        export_service = ExportService(business_id=business_id)
        path = export_service.export_sessions_to_excel(
            date_from=effective_date_from,
            date_to=effective_date_to,
            user_id=selected_employee_id,
            is_active=selected_is_active,
            incident_filter=selected_incident_filter,
        )
        return FileResponse(
            path=str(path),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=path.name,
        )
    except Exception as exc:
        flash(request, f"Error al exportar: {exc}", "error")
        return RedirectResponse("/sessions", status_code=303)


@router.get("/export/pdf")
async def export_pdf(
    request: Request,
    current_user: Employee = Depends(require_admin),
    business_id: str = Depends(require_active_business),
    date_from: str | None = None,
    date_to: str | None = None,
    employee_id: str | None = None,
    user_id: str | None = None,
    is_active: str | None = None,
    incident_filter: str | None = None,
):
    try:
        SubscriptionService().assert_feature(business_id, PlanFeature.EXPORTS_ADVANCED)
    except FeatureNotAvailableError as exc:
        flash(request, str(exc), "error")
        return RedirectResponse("/sessions", status_code=303)
    effective_date_from = date_from or _default_date_from()
    effective_date_to = date_to or _default_date_to()
    errors: list[str] = []
    selected_employee_id = _parse_employee_filter(
        employee_id=employee_id,
        user_id=user_id,
        errors=errors,
    )
    selected_is_active = _parse_status_filter(is_active, errors=errors)
    selected_incident_filter = _parse_incident_filter(
        incident_filter,
        errors=errors,
    )
    if errors:
        for error in errors:
            flash(request, error, "error")
        return RedirectResponse("/sessions", status_code=303)

    try:
        export_service = ExportService(business_id=business_id)
        path = export_service.export_sessions_to_pdf(
            date_from=effective_date_from,
            date_to=effective_date_to,
            user_id=selected_employee_id,
            is_active=selected_is_active,
            incident_filter=selected_incident_filter,
        )
        return FileResponse(
            path=str(path),
            media_type="application/pdf",
            filename=path.name,
        )
    except Exception as exc:
        flash(request, f"Error al exportar: {exc}", "error")
        return RedirectResponse("/sessions", status_code=303)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

_VALID_INCIDENT_FILTERS = {
    AttendanceReportService.INCIDENT_FILTER_ALL,
    AttendanceReportService.INCIDENT_FILTER_ANY,
    AttendanceReportService.INCIDENT_FILTER_PREVIOUS_OPEN,
    AttendanceReportService.INCIDENT_FILTER_EXCESS_8,
    AttendanceReportService.INCIDENT_FILTER_EXCESS_10,
    AttendanceReportService.INCIDENT_FILTER_EXCESS_12,
}


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    clean_value = str(value).strip()
    return clean_value or None


def _parse_date_filter(
    value: str | None,
    *,
    fallback: str,
    field_label: str,
    errors: list[str],
) -> str:
    clean_value = _blank_to_none(value)
    if clean_value is None:
        return fallback
    try:
        date.fromisoformat(clean_value)
    except ValueError:
        errors.append(f"La {field_label} debe tener formato AAAA-MM-DD.")
        return fallback
    return clean_value


def _parse_employee_filter(
    *,
    employee_id: str | None,
    user_id: str | None,
    errors: list[str],
) -> int | None:
    raw_value = _blank_to_none(employee_id)
    if raw_value is None:
        # Backward-compatible alias for links/bookmarks created before the
        # web layer was standardised on employee_id.
        raw_value = _blank_to_none(user_id)
    if raw_value is None:
        return None
    try:
        return int(raw_value)
    except ValueError:
        errors.append("El filtro de empleado no es valido.")
        return None


def _parse_status_filter(value: str | None, *, errors: list[str]) -> int | None:
    clean_value = _blank_to_none(value)
    if clean_value is None:
        return None
    if clean_value not in {"0", "1"}:
        errors.append("El filtro de estado no es valido.")
        return None
    return int(clean_value)


def _parse_incident_filter(value: str | None, *, errors: list[str]) -> str:
    clean_value = _blank_to_none(value) or AttendanceReportService.INCIDENT_FILTER_ALL
    if clean_value not in _VALID_INCIDENT_FILTERS:
        errors.append("El filtro de incidencias no es valido.")
        return AttendanceReportService.INCIDENT_FILTER_ALL
    return clean_value


def _build_redirect_params(request: Request) -> str:
    """Build a query string from the current request's query params."""
    query = request.url.query
    return f"?{query}" if query else ""
