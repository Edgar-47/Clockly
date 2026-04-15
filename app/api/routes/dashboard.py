"""
app/api/routes/dashboard.py

Main dashboard: live attendance + high-level workforce KPIs.
All data is scoped to the admin's active business.
"""
from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.api.dependencies import (
    require_active_business,
    require_admin,
    template_context,
)
from app.core.templates import templates
from app.database.business_repository import BusinessRepository
from app.models.employee import Employee
from app.services.analytics_service import AnalyticsService, _fmt_hours
from app.services.attendance_report_service import AttendanceReportService
from app.services.employee_service import EmployeeService
from app.services.time_clock_service import TimeClockService

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: Employee = Depends(require_admin),
    business_id: str = Depends(require_active_business),
):
    """
    Main dashboard — scoped to the active business.
    Displays:
    - Business context header
    - Summary counters (total employees, clocked in, clocked out)
    - Workforce KPI cards (hours today/week/month; overtime; top worker)
    - Table of currently clocked-in employees with elapsed time
    - Last 20 closed sessions
    """
    # Load business for display
    business_repo = BusinessRepository()
    business = business_repo.get_by_id(business_id)

    clock_service = TimeClockService(business_id=business_id)
    employee_service = EmployeeService(business_id=business_id)
    report_service = AttendanceReportService(business_id=business_id)

    # Attendance statuses for all active employees in this business
    all_statuses = clock_service.list_current_statuses(active_only=True)
    clocked_in = [s for s in all_statuses if s.is_clocked_in]
    clocked_out = [s for s in all_statuses if not s.is_clocked_in]

    # Recent closed sessions (last 20)
    recent_sessions = report_service.list_session_reports(is_active=0)[:20]

    # Workforce KPIs
    active_employees = [
        e for e in employee_service.list_employees()
        if e.active and e.role == "employee"
    ]
    user_ids = [e.id for e in active_employees]

    kpis = None
    if user_ids:
        try:
            analytics = AnalyticsService(business_id=business_id)
            kpis = analytics.get_dashboard_kpis(user_ids=user_ids, today=date.today())
        except Exception:
            kpis = None

    ctx = template_context(request)
    ctx.update({
        "business": business,
        "total_employees": len(all_statuses),
        "total_clocked_in": len(clocked_in),
        "total_clocked_out": len(clocked_out),
        "clocked_in_statuses": clocked_in,
        "recent_sessions": recent_sessions,
        "kpis": kpis,
        "fmt_hours": _fmt_hours,
    })
    return templates.TemplateResponse(request, "dashboard.html", ctx)
