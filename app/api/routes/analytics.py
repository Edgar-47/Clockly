"""
app/api/routes/analytics.py

Admin analytics dashboard — workforce intelligence.
All heavy calculations live in AnalyticsService and WorkScheduleService.
"""
from __future__ import annotations

import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse

from app.api.dependencies import require_active_business, require_admin, template_context
from app.core.templates import templates
from app.models.employee import Employee
from app.services.analytics_service import (
    AnalyticsService,
    STANDARD_DAY_SECONDS,
    _fmt_hours,
)
from app.services.employee_service import EmployeeService
from app.services.work_schedule_service import WorkScheduleService

router = APIRouter(tags=["analytics"])


@router.get("/analytics", response_class=HTMLResponse)
async def analytics_dashboard(
    request: Request,
    current_user: Employee = Depends(require_admin),
    business_id: str = Depends(require_active_business),
    period: str = Query("month", pattern="^(today|week|month|custom)$"),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    employee_id: int | None = Query(None),
):
    """
    Admin analytics dashboard.
    Provides: worker rankings, peak staffing heatmap, overtime trends,
    planned vs actual compliance, and monthly overtime breakdown.
    """
    today = date.today()

    # ── Resolve date range ────────────────────────────────────────
    if period == "today":
        start = end = today
    elif period == "week":
        start = today - timedelta(days=today.weekday())
        end = today
    elif period == "custom" and date_from and date_to:
        try:
            start = date.fromisoformat(date_from)
            end = date.fromisoformat(date_to)
            if end < start:
                start, end = end, start
        except ValueError:
            start = today.replace(day=1)
            end = today
        period = "custom"
    else:  # month (default)
        period = "month"
        start = today.replace(day=1)
        end = today

    # ── Employee filter ───────────────────────────────────────────
    employee_service = EmployeeService(business_id=business_id)
    all_employees = employee_service.list_employees()
    active_employees = [e for e in all_employees if e.active and e.role == "employee"]
    filtered_employee = next((e for e in all_employees if e.id == employee_id), None)

    user_ids: list[int] | None = None
    if employee_id and filtered_employee:
        user_ids = [employee_id]
    else:
        user_ids = [e.id for e in active_employees]

    analytics = AnalyticsService(business_id=business_id)
    schedule_service = WorkScheduleService(business_id=business_id)

    # ── Worker rankings ───────────────────────────────────────────
    rankings = analytics.get_worker_rankings(
        start=start,
        end=end,
        user_ids=user_ids,
        limit=15,
    )

    # Serialize for Chart.js
    ranking_json = json.dumps({
        "labels": [r.employee_name.split()[0] if r.employee_name else "—" for r in rankings[:10]],
        "total_hours": [round(r.total_seconds / 3600, 1) for r in rankings[:10]],
        "overtime_hours": [round(r.overtime_seconds / 3600, 1) for r in rankings[:10]],
        "shift_counts": [r.shift_count for r in rankings[:10]],
    }, ensure_ascii=False)

    # ── Peak staffing heatmap ─────────────────────────────────────
    peak_slots = analytics.get_peak_staffing(start=start, end=end, user_ids=user_ids)
    # Build a {dow: {hour: avg_count}} structure for the template
    peak_matrix: dict[int, dict[int, float]] = {dow: {} for dow in range(7)}
    for slot in peak_slots:
        peak_matrix[slot.day_of_week][slot.hour] = slot.avg_count

    max_peak = max((s.avg_count for s in peak_slots), default=0)

    peak_json = json.dumps(
        {
            f"{s.day_of_week}_{s.hour}": round(s.avg_count, 2)
            for s in peak_slots
        },
        ensure_ascii=False,
    )

    # ── Overtime trend (last 12 months) ───────────────────────────
    overtime_trend = analytics.get_overtime_trend(months_back=12, user_ids=user_ids)
    overtime_trend_json = json.dumps({
        "labels": [p.label for p in overtime_trend],
        "regular_hours": [round(p.regular_seconds / 3600, 1) for p in overtime_trend],
        "overtime_hours": [round(p.overtime_seconds / 3600, 1) for p in overtime_trend],
    }, ensure_ascii=False)

    # ── Monthly overtime stats (current year) ─────────────────────
    monthly_stats = analytics.get_monthly_overtime_stats(
        year=today.year,
        user_ids=user_ids,
    )

    # ── Planned vs actual (only if schedules exist) ───────────────
    has_schedules = bool(schedule_service.list_active_schedules())
    planned_vs_actual: list = []

    if has_schedules and user_ids:
        # Build actual_seconds_by_user from rankings
        actual_by_user = {
            r.employee_id: (r.employee_name, r.total_seconds)
            for r in rankings
        }
        planned_vs_actual = schedule_service.build_planned_vs_actual(
            start=start,
            end=end,
            actual_seconds_by_user=actual_by_user,
        )

    # ── Period summary cards ──────────────────────────────────────
    total_hours = sum(r.total_seconds for r in rankings)
    total_overtime = sum(r.overtime_seconds for r in rankings)
    total_shifts = sum(r.shift_count for r in rankings)
    avg_shift = total_hours // len(rankings) if rankings else 0

    # Busiest hour in period
    busiest_slot = max(peak_slots, key=lambda s: s.count, default=None)
    busiest_hour_label = (
        f"{busiest_slot.hour:02d}:00–{busiest_slot.hour + 1:02d}:00"
        if busiest_slot and busiest_slot.count > 0
        else "—"
    )

    # Period label
    period_labels = {
        "today": "Hoy",
        "week": "Esta semana",
        "month": "Este mes",
        "custom": f"{start.strftime('%d/%m/%Y')} – {end.strftime('%d/%m/%Y')}",
    }

    ctx = template_context(request)
    ctx.update({
        # Period / filter state
        "period": period,
        "date_from": start.isoformat(),
        "date_to": end.isoformat(),
        "period_label": period_labels.get(period, "Período personalizado"),
        "employee_id": employee_id,
        "filtered_employee": filtered_employee,
        "all_employees": active_employees,

        # Summary KPIs
        "total_hours_label": _fmt_hours(total_hours),
        "total_overtime_label": _fmt_hours(total_overtime),
        "total_shifts": total_shifts,
        "avg_shift_label": _fmt_hours(avg_shift),
        "busiest_hour_label": busiest_hour_label,
        "max_concurrent": busiest_slot.count if busiest_slot else 0,

        # Rankings
        "rankings": rankings,
        "ranking_json": ranking_json,

        # Heatmap
        "peak_slots": peak_slots,
        "peak_matrix": peak_matrix,
        "max_peak": max_peak,
        "peak_json": peak_json,

        # Overtime trend
        "overtime_trend": overtime_trend,
        "overtime_trend_json": overtime_trend_json,
        "monthly_stats": monthly_stats,

        # Planned vs actual
        "has_schedules": has_schedules,
        "planned_vs_actual": planned_vs_actual,

        # Helpers
        "fmt_hours": _fmt_hours,
        "range_7": range(7),
        "range_24": range(24),
        "hour_labels": [f"{h:02d}h" for h in range(24)],
        "day_labels_short": ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"),
    })

    return templates.TemplateResponse(request, "analytics/dashboard.html", ctx)
