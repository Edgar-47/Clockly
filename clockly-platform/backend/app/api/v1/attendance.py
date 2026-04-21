from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import ApiContext, require_api_business
from app.api.v1.errors import forbidden, validation_error
from app.api.v1.serializers import attendance_status_to_dict, session_report_to_dict
from app.database.employee_repository import EmployeeRepository
from app.schemas.api_v1 import ClockRequest
from app.services.attendance_report_service import AttendanceReportService
from app.services.time_clock_service import TimeClockService


router = APIRouter(prefix="/attendance", tags=["api-attendance"])


@router.get("")
async def current_attendance(ctx: ApiContext = Depends(require_api_business)) -> dict:
    clock_service = TimeClockService(business_id=ctx.active_business_id)
    if ctx.active_business_role == "employee":
        employee = EmployeeRepository(business_id=ctx.active_business_id).get_by_id(
            ctx.user.id
        )
        if employee is None:
            raise validation_error("Empleado no encontrado en el negocio activo.")
        return {"items": [attendance_status_to_dict(clock_service.get_attendance_status(employee))]}

    if "attendance:manage" not in ctx.permissions:
        raise forbidden()
    statuses = clock_service.list_current_statuses(active_only=True)
    return {"items": [attendance_status_to_dict(status) for status in statuses]}


@router.post("/clock-in")
async def clock_in(
    payload: ClockRequest | None = None,
    ctx: ApiContext = Depends(require_api_business),
) -> dict:
    employee_id = _resolve_clock_employee_id(ctx, payload.employee_id if payload else None)
    try:
        session = TimeClockService(
            business_id=ctx.active_business_id,
        ).start_session_for_employee(employee_id)
    except ValueError as exc:
        raise validation_error(str(exc)) from exc
    return {"session": session_report_or_session(session)}


@router.post("/clock-out")
async def clock_out(
    payload: ClockRequest | None = None,
    ctx: ApiContext = Depends(require_api_business),
) -> dict:
    payload = payload or ClockRequest()
    employee_id = _resolve_clock_employee_id(ctx, payload.employee_id)
    try:
        session = TimeClockService(
            business_id=ctx.active_business_id,
        ).clock_out_employee(
            employee_id,
            exit_note=payload.exit_note,
            incident_type=payload.incident_type,
        )
    except ValueError as exc:
        raise validation_error(str(exc)) from exc
    return {"session": session_report_or_session(session)}


@router.get("/history")
async def attendance_history(
    date_from: str | None = None,
    date_to: str | None = None,
    employee_id: int | None = None,
    is_active: int | None = None,
    incident_filter: str | None = None,
    ctx: ApiContext = Depends(require_api_business),
) -> dict:
    if ctx.active_business_role == "employee":
        employee_id = ctx.user.id
    elif "reports:view" not in ctx.permissions and "attendance:manage" not in ctx.permissions:
        raise forbidden()

    reports = AttendanceReportService(
        business_id=ctx.active_business_id,
    ).list_session_reports(
        date_from=date_from,
        date_to=date_to,
        employee_id=employee_id,
        is_active=is_active,
        incident_filter=incident_filter,
    )
    return {"items": [session_report_to_dict(report) for report in reports]}


def _resolve_clock_employee_id(ctx: ApiContext, requested_employee_id: int | None) -> int:
    if ctx.active_business_role == "employee":
        if requested_employee_id and requested_employee_id != ctx.user.id:
            raise forbidden("Solo puedes fichar con tu propio usuario.")
        return ctx.user.id
    if "attendance:manage" not in ctx.permissions:
        raise forbidden()
    if requested_employee_id is None:
        raise validation_error("employee_id es obligatorio para fichaje administrado.")
    return requested_employee_id


def session_report_or_session(session) -> dict:
    return {
        "id": session.id,
        "business_id": session.business_id,
        "user_id": session.user_id,
        "clock_in_time": session.clock_in_time,
        "clock_out_time": session.clock_out_time,
        "is_active": session.is_active,
        "total_seconds": session.total_seconds,
        "exit_note": session.exit_note,
        "incident_type": session.incident_type,
    }
