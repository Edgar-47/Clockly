"""
app/services/analytics_service.py

Workforce intelligence analytics — all calculations live here.
Reads only from attendance_sessions (single source of truth).
Never reads from legacy time_entries.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from app.database.attendance_session_repository import AttendanceSessionRepository
from app.models.attendance_session import AttendanceSession


_MONTH_NAMES_ES = (
    "", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
)

# Standard overtime threshold (seconds)
STANDARD_DAY_SECONDS = 8 * 3600   # 8 h
STANDARD_WEEK_SECONDS = 40 * 3600  # 40 h


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WorkerRanking:
    employee_id: int
    employee_name: str
    dni: str
    total_seconds: int
    overtime_seconds: int        # above STANDARD_DAY_SECONDS threshold per shift
    shift_count: int
    average_seconds: int         # avg shift duration

    @property
    def total_hours_label(self) -> str:
        return _fmt_hours(self.total_seconds)

    @property
    def overtime_hours_label(self) -> str:
        return _fmt_hours(self.overtime_seconds)

    @property
    def avg_shift_label(self) -> str:
        return _fmt_hours(self.average_seconds)

    @property
    def overtime_pct(self) -> float:
        if not self.total_seconds:
            return 0.0
        return round(self.overtime_seconds / self.total_seconds * 100, 1)


@dataclass(frozen=True)
class HourlySlot:
    """One cell of the peak-staffing heatmap (day_of_week × hour)."""
    day_of_week: int    # 0 = Monday
    hour: int           # 0–23
    count: int          # number of presence instances summed across all days
    avg_count: float    # count / number_of_that_weekday_in_period
    is_peak: bool = False


@dataclass(frozen=True)
class MonthlyOvertimeStat:
    year: int
    month: int
    label: str                   # "Ene 2024"
    total_overtime_seconds: int
    sessions_with_overtime: int
    affected_users: int

    @property
    def total_overtime_hours_label(self) -> str:
        return _fmt_hours(self.total_overtime_seconds)


@dataclass(frozen=True)
class OvertimeTrendPoint:
    label: str   # "Ene 24"
    regular_seconds: int
    overtime_seconds: int
    month: int
    year: int


@dataclass(frozen=True)
class ComplianceSummary:
    total_assessed: int
    on_time: int
    late_arrivals: int
    early_leaves: int
    overtime_sessions: int
    missed_shifts: int           # scheduled days with no clock-in


@dataclass(frozen=True)
class ComplianceDetail:
    employee_id: int
    employee_name: str
    session_date: str
    clock_in_time: str
    clock_out_time: str | None
    scheduled_start: str         # "HH:MM"
    scheduled_end: str           # "HH:MM"
    late_minutes: int            # 0 if on time / negative if early
    early_leave_minutes: int     # 0 if on time / negative if late
    overtime_seconds: int
    status: str                  # "ok" | "late" | "early_leave" | "overtime"


@dataclass(frozen=True)
class DashboardSummary:
    """High-level KPIs for the main dashboard."""
    total_hours_today: int
    total_hours_week: int
    total_hours_month: int
    busiest_hour_today: int | None
    busiest_concurrent_today: int
    month_overtime_seconds: int
    top_worker_this_week: str | None


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class AnalyticsService:

    def __init__(
        self,
        attendance_session_repository: AttendanceSessionRepository | None = None,
    ) -> None:
        self.repo = attendance_session_repository or AttendanceSessionRepository()

    # ------------------------------------------------------------------
    # Worker rankings
    # ------------------------------------------------------------------

    def get_worker_rankings(
        self,
        *,
        start: date,
        end: date,
        user_ids: list[int] | None = None,
        overtime_threshold_seconds: int = STANDARD_DAY_SECONDS,
        limit: int = 20,
    ) -> list[WorkerRanking]:
        """
        Return employees ranked by total worked hours in [start, end].
        `end` is inclusive: sessions starting on end-date are included.
        """
        start_str = _date_to_str(start)
        end_str = _date_to_str(end + timedelta(days=1))  # exclusive upper bound

        rows = self.repo.aggregate_worked_seconds_by_user(
            start_str, end_str, user_ids=user_ids
        )

        # Calculate overtime per employee by iterating individual sessions
        sessions = self.repo.list_closed_overlapping(
            start=start_str,
            end=end_str,
            user_ids=user_ids,
        )
        overtime_by_user: dict[int, int] = {}
        for s in sessions:
            sec = s.total_seconds or 0
            overtime = max(sec - overtime_threshold_seconds, 0)
            overtime_by_user[s.user_id] = overtime_by_user.get(s.user_id, 0) + overtime

        rankings = []
        for row in rows[:limit]:
            uid = int(row["user_id"])
            total_s = int(row["total_seconds"] or 0)
            shift_count = int(row["shift_count"] or 0)
            avg_s = int(row["avg_seconds"] or 0) if shift_count else 0
            rankings.append(
                WorkerRanking(
                    employee_id=uid,
                    employee_name=str(row.get("employee_name") or ""),
                    dni=str(row.get("dni") or ""),
                    total_seconds=total_s,
                    overtime_seconds=overtime_by_user.get(uid, 0),
                    shift_count=shift_count,
                    average_seconds=avg_s,
                )
            )
        return rankings

    # ------------------------------------------------------------------
    # Peak staffing heatmap
    # ------------------------------------------------------------------

    def get_peak_staffing(
        self,
        *,
        start: date,
        end: date,
        user_ids: list[int] | None = None,
    ) -> list[HourlySlot]:
        """
        Build a 7×24 (day_of_week × hour) heatmap of average concurrent workers.
        Returns list of HourlySlot, sorted by (day_of_week, hour).
        """
        start_dt = datetime.combine(start, time.min)
        end_dt = datetime.combine(end + timedelta(days=1), time.min)

        sessions = self.repo.list_all_overlapping(
            start=_dt_to_str(start_dt),
            end=_dt_to_str(end_dt),
            user_ids=user_ids,
        )

        # Count occurrences: {(dow, hour): total_presence}
        presence: dict[tuple[int, int], int] = {}
        # Count how many times each (dow, hour) slot actually existed in period
        day_counts: dict[int, int] = _weekday_counts(start, end)

        now = datetime.now()

        for session in sessions:
            s_in = _parse_dt(session.clock_in_time)
            if session.clock_out_time:
                s_out = _parse_dt(session.clock_out_time)
            elif session.is_active:
                s_out = min(now, end_dt)
            else:
                continue
            if not s_in or not s_out or s_out <= s_in:
                continue

            # Clamp to analysis window
            s_in = max(s_in, start_dt)
            s_out = min(s_out, end_dt)

            # Walk through each full hour slot the session touches
            cursor = s_in.replace(minute=0, second=0, microsecond=0)
            if cursor < s_in:
                cursor += timedelta(hours=1)

            while cursor < s_out:
                slot_start = cursor
                slot_end = cursor + timedelta(hours=1)
                # Session overlaps this slot
                overlap_start = max(s_in, slot_start)
                overlap_end = min(s_out, slot_end)
                if overlap_end > overlap_start:
                    dow = slot_start.weekday()
                    hour = slot_start.hour
                    presence[(dow, hour)] = presence.get((dow, hour), 0) + 1
                cursor += timedelta(hours=1)

        # Build heatmap slots
        max_count = max(presence.values(), default=0)
        slots: list[HourlySlot] = []
        for dow in range(7):
            n_days = day_counts.get(dow, 1)
            for hour in range(24):
                count = presence.get((dow, hour), 0)
                avg = count / n_days if n_days else 0
                slots.append(
                    HourlySlot(
                        day_of_week=dow,
                        hour=hour,
                        count=count,
                        avg_count=round(avg, 2),
                        is_peak=(count == max_count and count > 0),
                    )
                )
        return slots

    # ------------------------------------------------------------------
    # Monthly overtime trend
    # ------------------------------------------------------------------

    def get_overtime_trend(
        self,
        *,
        year: int | None = None,
        months_back: int = 12,
        user_ids: list[int] | None = None,
        overtime_threshold_seconds: int = STANDARD_DAY_SECONDS,
    ) -> list[OvertimeTrendPoint]:
        """
        Return month-by-month overtime vs regular hours for last `months_back` months.
        """
        today = date.today()
        if year is not None:
            months = [(year, m) for m in range(1, 13)]
        else:
            months = []
            cursor = today.replace(day=1)
            for _ in range(months_back):
                months.append((cursor.year, cursor.month))
                # Go to previous month
                if cursor.month == 1:
                    cursor = cursor.replace(year=cursor.year - 1, month=12)
                else:
                    cursor = cursor.replace(month=cursor.month - 1)
            months.reverse()

        points: list[OvertimeTrendPoint] = []
        for yr, mo in months:
            month_start = date(yr, mo, 1)
            last_day = calendar.monthrange(yr, mo)[1]
            month_end = date(yr, mo, last_day)

            start_str = _date_to_str(month_start)
            end_str = _date_to_str(month_end + timedelta(days=1))

            sessions = self.repo.list_closed_overlapping(
                start=start_str,
                end=end_str,
                user_ids=user_ids,
            )

            regular_s = 0
            overtime_s = 0
            for s in sessions:
                sec = s.total_seconds or 0
                ot = max(sec - overtime_threshold_seconds, 0)
                reg = sec - ot
                regular_s += reg
                overtime_s += ot

            label = f"{_MONTH_NAMES_ES[mo]} {str(yr)[2:]}"
            points.append(OvertimeTrendPoint(
                label=label,
                regular_seconds=regular_s,
                overtime_seconds=overtime_s,
                month=mo,
                year=yr,
            ))
        return points

    def get_monthly_overtime_stats(
        self,
        *,
        year: int,
        user_ids: list[int] | None = None,
        overtime_threshold_seconds: int = STANDARD_DAY_SECONDS,
    ) -> list[MonthlyOvertimeStat]:
        rows = self.repo.aggregate_overtime_by_month(
            year=year,
            overtime_threshold_seconds=overtime_threshold_seconds,
            user_ids=user_ids,
        )
        by_month = {int(r["month"]): r for r in rows}
        stats: list[MonthlyOvertimeStat] = []
        for mo in range(1, 13):
            row = by_month.get(mo)
            stats.append(MonthlyOvertimeStat(
                year=year,
                month=mo,
                label=f"{_MONTH_NAMES_ES[mo]} {year}",
                total_overtime_seconds=int(row["total_overtime_seconds"] or 0) if row else 0,
                sessions_with_overtime=int(row["sessions_with_overtime"] or 0) if row else 0,
                affected_users=int(row["affected_users"] or 0) if row else 0,
            ))
        return stats

    # ------------------------------------------------------------------
    # Compliance: planned vs actual
    # ------------------------------------------------------------------

    def get_compliance_overview(
        self,
        *,
        start: date,
        end: date,
        assignments: list,  # list[EmployeeSchedule] with days pre-loaded
        schedule_days_by_schedule: dict[int, list],  # dict[schedule_id → list[ScheduleDay]]
        overtime_threshold_seconds: int = STANDARD_DAY_SECONDS,
    ) -> ComplianceSummary:
        """
        Compare scheduled hours vs actual attendance for assigned employees.
        `assignments` and `schedule_days_by_schedule` come from WorkScheduleService.
        """
        if not assignments:
            return ComplianceSummary(0, 0, 0, 0, 0, 0)

        user_ids = list({a.user_id for a in assignments})
        start_str = _date_to_str(start)
        end_str = _date_to_str(end + timedelta(days=1))

        sessions = self.repo.list_closed_overlapping(
            start=start_str,
            end=end_str,
            user_ids=user_ids,
        )

        # Group sessions by (user_id, date)
        sessions_by_user_day: dict[tuple[int, date], list[AttendanceSession]] = {}
        for s in sessions:
            s_dt = _parse_dt(s.clock_in_time)
            if not s_dt:
                continue
            key = (s.user_id, s_dt.date())
            sessions_by_user_day.setdefault(key, []).append(s)

        total_assessed = 0
        on_time = 0
        late = 0
        early = 0
        overtime_count = 0
        missed = 0

        current = start
        while current <= end:
            dow = current.weekday()
            for assignment in assignments:
                if not assignment.is_current(current):
                    continue
                days_map = schedule_days_by_schedule.get(assignment.schedule_id, [])
                sched_day = next((d for d in days_map if d.day_of_week == dow), None)
                if not sched_day:
                    continue

                total_assessed += 1
                day_sessions = sessions_by_user_day.get((assignment.user_id, current), [])

                if not day_sessions:
                    missed += 1
                    continue

                # Use earliest clock-in and latest clock-out
                earliest_in = min(
                    (_parse_dt(s.clock_in_time) for s in day_sessions if s.clock_in_time),
                    default=None,
                )
                latest_out = max(
                    (
                        _parse_dt(s.clock_out_time)
                        for s in day_sessions
                        if s.clock_out_time
                    ),
                    default=None,
                )

                scheduled_in = datetime.combine(current, _parse_time(sched_day.start_time))
                scheduled_out = datetime.combine(current, _parse_time(sched_day.end_time))
                tolerance_in = timedelta(minutes=sched_day.late_tolerance_minutes)
                tolerance_out = timedelta(minutes=sched_day.early_leave_tolerance_minutes)

                is_late = earliest_in and earliest_in > scheduled_in + tolerance_in
                is_early = latest_out and latest_out < scheduled_out - tolerance_out

                total_session_s = sum(s.total_seconds or 0 for s in day_sessions)
                is_overtime = total_session_s > overtime_threshold_seconds

                if is_late:
                    late += 1
                elif is_early:
                    early += 1
                elif is_overtime:
                    overtime_count += 1
                else:
                    on_time += 1

            current += timedelta(days=1)

        return ComplianceSummary(
            total_assessed=total_assessed,
            on_time=on_time,
            late_arrivals=late,
            early_leaves=early,
            overtime_sessions=overtime_count,
            missed_shifts=missed,
        )

    # ------------------------------------------------------------------
    # Dashboard-level KPIs
    # ------------------------------------------------------------------

    def get_dashboard_kpis(
        self,
        *,
        user_ids: list[int],
        today: date | None = None,
    ) -> DashboardSummary:
        ref = today or date.today()
        week_start = ref - timedelta(days=ref.weekday())
        month_start = ref.replace(day=1)

        today_str = _date_to_str(ref)
        today_end = _date_to_str(ref + timedelta(days=1))
        week_str = _date_to_str(week_start)
        month_str = _date_to_str(month_start)
        end_str = _date_to_str(ref + timedelta(days=1))

        # Aggregate totals
        today_rows = self.repo.aggregate_worked_seconds_by_user(
            today_str, today_end, user_ids=user_ids
        )
        week_rows = self.repo.aggregate_worked_seconds_by_user(
            week_str, end_str, user_ids=user_ids
        )
        month_rows = self.repo.aggregate_worked_seconds_by_user(
            month_str, end_str, user_ids=user_ids
        )

        total_today = sum(int(r.get("total_seconds") or 0) for r in today_rows)
        total_week = sum(int(r.get("total_seconds") or 0) for r in week_rows)
        total_month = sum(int(r.get("total_seconds") or 0) for r in month_rows)

        # Top worker this week (by hours)
        top_worker = max(week_rows, key=lambda r: r.get("total_seconds") or 0, default=None)
        top_name = str(top_worker["employee_name"]) if top_worker else None

        # Month overtime (simple: sum of overtime-seconds from month sessions)
        month_sessions = self.repo.list_closed_overlapping(
            start=month_str,
            end=end_str,
            user_ids=user_ids,
        )
        month_overtime = sum(
            max((s.total_seconds or 0) - STANDARD_DAY_SECONDS, 0)
            for s in month_sessions
        )

        # Busiest hour today
        today_peak = self.get_peak_staffing(start=ref, end=ref, user_ids=user_ids)
        busiest = max(today_peak, key=lambda s: s.count, default=None)
        busiest_hour = busiest.hour if busiest and busiest.count > 0 else None
        busiest_count = busiest.count if busiest else 0

        return DashboardSummary(
            total_hours_today=total_today,
            total_hours_week=total_week,
            total_hours_month=total_month,
            busiest_hour_today=busiest_hour,
            busiest_concurrent_today=busiest_count,
            month_overtime_seconds=month_overtime,
            top_worker_this_week=top_name,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_hours(seconds: int) -> str:
    if not seconds:
        return "0h"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    if m:
        return f"{h}h {m}m"
    return f"{h}h"


def _date_to_str(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def _dt_to_str(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat(sep=" ")


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except (ValueError, TypeError):
        return None


def _parse_time(value: str) -> time:
    try:
        parts = str(value).split(":")
        h, m = int(parts[0]), int(parts[1])
        return time(h, m)
    except (ValueError, IndexError, TypeError):
        return time(0, 0)


def _weekday_counts(start: date, end: date) -> dict[int, int]:
    """Return how many times each weekday (0–6) occurs in [start, end]."""
    counts: dict[int, int] = {i: 0 for i in range(7)}
    cursor = start
    while cursor <= end:
        counts[cursor.weekday()] += 1
        cursor += timedelta(days=1)
    return counts
