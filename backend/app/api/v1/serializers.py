from __future__ import annotations

from app.models.attendance_session import AttendanceSession
from app.models.attendance_status import AttendanceStatus
from app.models.business import Business
from app.models.employee import Employee
from app.services.analytics_service import DashboardSummary
from app.services.attendance_report_service import SessionReport
from app.services.authorization_service import ROLE_PERMISSIONS


def user_to_dict(user: Employee, *, business_role: str | None = None) -> dict:
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.full_name,
        "dni": user.dni,
        "role": business_role or user.role,
        "global_role": user.role,
        "active": user.active,
        "created_at": user.created_at,
        "last_business_id": user.last_business_id,
    }


def business_to_dict(business: Business, *, active: bool = False, role: str | None = None) -> dict:
    return {
        "id": business.id,
        "business_name": business.business_name,
        "business_type": business.business_type,
        "timezone": business.timezone,
        "country": business.country,
        "login_code": business.login_code,
        "slug": business.slug,
        "business_key": business.business_key,
        "is_active": business.is_active,
        "created_at": business.created_at,
        "updated_at": business.updated_at,
        "active": active,
        "role": role,
    }


def session_to_dict(session: AttendanceSession | None) -> dict | None:
    if session is None:
        return None
    return {
        "id": session.id,
        "business_id": session.business_id,
        "user_id": session.user_id,
        "clock_in_time": session.clock_in_time,
        "clock_out_time": session.clock_out_time,
        "is_active": session.is_active,
        "total_seconds": session.total_seconds,
        "notes": session.notes,
        "exit_note": session.exit_note,
        "incident_type": session.incident_type,
        "closed_by_admin": session.closed_by_admin,
        "manual_close_reason": session.manual_close_reason,
        "closed_by_user_id": session.closed_by_user_id,
    }


def attendance_status_to_dict(status: AttendanceStatus) -> dict:
    return {
        "employee": user_to_dict(status.employee),
        "is_clocked_in": status.is_clocked_in,
        "status_label": status.status_label,
        "last_action_label": status.last_action_label,
        "last_timestamp": status.last_timestamp,
        "active_session": session_to_dict(status.active_session),
        "latest_session": session_to_dict(status.latest_session),
    }


def session_report_to_dict(report: SessionReport) -> dict:
    return {
        "id": report.id,
        "business_id": None,
        "user_id": report.user_id,
        "employee_name": report.employee_name,
        "dni": report.dni,
        "clock_in_time": report.clock_in_time,
        "clock_out_time": report.clock_out_time,
        "is_active": report.is_active,
        "total_seconds": report.total_seconds,
        "display_duration_seconds": report.display_duration_seconds,
        "counted_duration_seconds": report.counted_duration_seconds,
        "exit_note": report.exit_note,
        "incident_type": report.incident_type,
        "closed_by_admin": report.closed_by_admin,
        "manual_close_reason": report.manual_close_reason,
        "incident_label": report.incident_label,
        "severity": report.severity,
        "status_label": report.status_label,
    }


def dashboard_summary_to_dict(summary: DashboardSummary | None) -> dict | None:
    if summary is None:
        return None
    return {
        "total_hours_today": summary.total_hours_today,
        "total_hours_week": summary.total_hours_week,
        "total_hours_month": summary.total_hours_month,
        "busiest_hour_today": summary.busiest_hour_today,
        "busiest_concurrent_today": summary.busiest_concurrent_today,
        "month_overtime_seconds": summary.month_overtime_seconds,
        "top_worker_this_week": summary.top_worker_this_week,
    }


def permissions_for_role(role: str | None) -> list[str]:
    return sorted(ROLE_PERMISSIONS.get(role or "", set()))
