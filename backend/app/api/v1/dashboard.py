from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import ApiContext, require_api_permission
from app.api.v1.serializers import (
    attendance_status_to_dict,
    business_to_dict,
    dashboard_summary_to_dict,
    session_report_to_dict,
)
from app.database.business_repository import BusinessRepository
from app.services.analytics_service import AnalyticsService
from app.services.attendance_report_service import AttendanceReportService
from app.services.employee_service import EmployeeService
from app.services.subscription_service import SubscriptionService
from app.services.time_clock_service import TimeClockService


router = APIRouter(prefix="/dashboard", tags=["api-dashboard"])


@router.get("/summary")
async def dashboard_summary(
    ctx: ApiContext = Depends(require_api_permission("reports:view")),
) -> dict:
    business_id = ctx.active_business_id or ""
    business = BusinessRepository().get_by_id(business_id)
    usage = SubscriptionService().get_usage_summary(business_id)
    clock_service = TimeClockService(business_id=business_id)
    employee_service = EmployeeService(business_id=business_id)
    report_service = AttendanceReportService(business_id=business_id)

    statuses = clock_service.list_current_statuses(active_only=True)
    clocked_in = [status for status in statuses if status.is_clocked_in]
    clocked_out = [status for status in statuses if not status.is_clocked_in]
    recent_sessions = report_service.list_session_reports(is_active=0)[:20]

    active_employees = [
        employee
        for employee in employee_service.list_employees()
        if employee.active and employee.role == "employee"
    ]
    kpis = None
    if active_employees:
        kpis = AnalyticsService(business_id=business_id).get_dashboard_kpis(
            user_ids=[employee.id for employee in active_employees],
            today=date.today(),
        )

    return {
        "business": business_to_dict(
            business,
            active=True,
            role=ctx.active_business_role,
        )
        if business
        else None,
        "usage": {
            "plan": {
                "code": usage.plan.code,
                "name": usage.plan.name,
                "max_employees": usage.plan.max_employees,
                "max_admins": usage.plan.max_admins,
            },
            "employee_count": usage.employee_count,
            "admin_count": usage.admin_count,
        },
        "total_employees": len(statuses),
        "total_clocked_in": len(clocked_in),
        "total_clocked_out": len(clocked_out),
        "clocked_in_statuses": [
            attendance_status_to_dict(status) for status in clocked_in
        ],
        "recent_sessions": [
            session_report_to_dict(session) for session in recent_sessions
        ],
        "kpis": dashboard_summary_to_dict(kpis),
    }
