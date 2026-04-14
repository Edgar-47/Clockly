"""
app/api/routes/dashboard.py

Main dashboard: shows live attendance summary and recent activity.
Admin-only view.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.api.dependencies import require_admin, template_context
from app.core.templates import templates
from app.models.employee import Employee
from app.services.time_clock_service import TimeClockService
from app.services.attendance_report_service import AttendanceReportService
from app.services.employee_service import EmployeeService

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    """
    Main dashboard.
    Displays:
    - Summary counters (total employees, clocked in, clocked out)
    - Table of currently clocked-in employees with elapsed time
    - Last 20 closed sessions
    """
    clock_service = TimeClockService()
    employee_service = EmployeeService()
    report_service = AttendanceReportService()

    # Attendance statuses for all active employees
    all_statuses = clock_service.list_current_statuses(active_only=True)
    clocked_in = [s for s in all_statuses if s.is_clocked_in]
    clocked_out = [s for s in all_statuses if not s.is_clocked_in]

    # Recent closed sessions (last 20)
    recent_sessions = report_service.list_session_reports(is_active=0)[:20]

    ctx = template_context(request)
    ctx.update({
        "total_employees": len(all_statuses),
        "total_clocked_in": len(clocked_in),
        "total_clocked_out": len(clocked_out),
        "clocked_in_statuses": clocked_in,
        "recent_sessions": recent_sessions,
    })
    return templates.TemplateResponse(request, "dashboard.html", ctx)
