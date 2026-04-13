from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from app.database.attendance_session_repository import AttendanceSessionRepository
from app.models.attendance_session import AttendanceSession
from app.services.attendance_policy import (
    exceeded_shift_threshold_hours,
    incident_type_label,
)


@dataclass(frozen=True)
class WorkSummary:
    employee_id: int
    period_start: datetime
    period_end: datetime
    total_seconds: int = 0
    shift_count: int = 0
    average_seconds: int = 0


@dataclass(frozen=True)
class EmployeePeriodSummary:
    employee_id: int
    today: WorkSummary
    week: WorkSummary
    month: WorkSummary


@dataclass(frozen=True)
class SessionReport:
    id: int
    user_id: int
    employee_name: str
    dni: str
    clock_in_time: str
    clock_out_time: str | None
    is_active: bool
    total_seconds: int | None
    notes: str | None
    exit_note: str | None
    incident_type: str | None
    closed_by_admin: bool
    manual_close_reason: str | None
    closed_by_user_id: int | None
    display_duration_seconds: int | None
    counted_duration_seconds: int | None
    excess_threshold_hours: int | None
    is_open_from_previous_day: bool
    incident_labels: tuple[str, ...]
    severity: str

    @property
    def has_incident(self) -> bool:
        return bool(self.incident_labels)

    @property
    def incident_label(self) -> str:
        return " | ".join(self.incident_labels) if self.incident_labels else "OK"

    @property
    def status_label(self) -> str:
        if self.closed_by_admin:
            return "Cierre admin"
        if self.is_active:
            return "Activo"
        return "Cerrado"

    @property
    def notes_label(self) -> str:
        parts = []
        if self.notes:
            parts.append(self.notes)
        if self.exit_note:
            parts.append(f"Salida: {self.exit_note}")
        if self.manual_close_reason and self.manual_close_reason != self.exit_note:
            parts.append(f"Cierre: {self.manual_close_reason}")
        return " | ".join(parts)


class AttendanceReportService:
    INCIDENT_FILTER_ALL = "all"
    INCIDENT_FILTER_ANY = "incidents"
    INCIDENT_FILTER_PREVIOUS_OPEN = "previous_open"
    INCIDENT_FILTER_EXCESS_8 = "excess_8"
    INCIDENT_FILTER_EXCESS_10 = "excess_10"
    INCIDENT_FILTER_EXCESS_12 = "excess_12"

    def __init__(
        self,
        attendance_session_repository: AttendanceSessionRepository | None = None,
    ) -> None:
        self.attendance_session_repository = (
            attendance_session_repository or AttendanceSessionRepository()
        )

    def get_current_period_summaries(
        self,
        employee_ids: list[int],
        *,
        today: date | None = None,
    ) -> dict[int, EmployeePeriodSummary]:
        if not employee_ids:
            return {}

        reference_day = today or date.today()
        day_start, day_end = self._day_bounds(reference_day)
        week_start, week_end = self._week_bounds(reference_day)
        month_start, month_end = self._month_bounds(reference_day)

        today_summaries = self.summarize_period(
            employee_ids,
            start=day_start,
            end=day_end,
        )
        week_summaries = self.summarize_period(
            employee_ids,
            start=week_start,
            end=week_end,
        )
        month_summaries = self.summarize_period(
            employee_ids,
            start=month_start,
            end=month_end,
        )

        return {
            employee_id: EmployeePeriodSummary(
                employee_id=employee_id,
                today=today_summaries[employee_id],
                week=week_summaries[employee_id],
                month=month_summaries[employee_id],
            )
            for employee_id in employee_ids
        }

    def get_employee_summary(
        self,
        employee_id: int,
        *,
        date_from: date,
        date_to: date,
    ) -> WorkSummary:
        start = datetime.combine(date_from, time.min)
        end = datetime.combine(date_to + timedelta(days=1), time.min)
        return self.summarize_period([employee_id], start=start, end=end)[employee_id]

    def summarize_period(
        self,
        employee_ids: list[int],
        *,
        start: datetime,
        end: datetime,
    ) -> dict[int, WorkSummary]:
        summaries = {
            employee_id: _MutableWorkSummary(employee_id=employee_id)
            for employee_id in employee_ids
        }
        if not employee_ids:
            return {}

        sessions = self.attendance_session_repository.list_closed_overlapping(
            start=self._format_datetime(start),
            end=self._format_datetime(end),
            user_ids=employee_ids,
        )

        for session in sessions:
            started = self._parse_datetime(session.clock_in_time)
            ended = self._parse_datetime(session.clock_out_time)
            if not started or not ended or ended <= started:
                continue

            summary = summaries.get(session.user_id)
            if summary is None:
                continue

            overlap_seconds = self._overlap_seconds(started, ended, start, end)
            if overlap_seconds > 0:
                summary.total_seconds += overlap_seconds

            if start <= started < end:
                summary.shift_count += 1
                session_seconds = session.total_seconds
                if session_seconds is None:
                    session_seconds = max(int((ended - started).total_seconds()), 0)
                summary.shift_seconds_total += max(int(session_seconds), 0)

        return {
            employee_id: summary.to_work_summary(start=start, end=end)
            for employee_id, summary in summaries.items()
        }

    def list_session_reports(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        user_id: int | None = None,
        is_active: int | None = None,
        incident_filter: str | None = None,
        now: datetime | None = None,
    ) -> list[SessionReport]:
        rows = self.attendance_session_repository.list_with_user_names(
            date_from=date_from,
            date_to=date_to,
            user_id=user_id,
            is_active=is_active,
        )
        reference_now = now or datetime.now().replace(microsecond=0)
        reports = [self._build_session_report(row, now=reference_now) for row in rows]
        clean_filter = incident_filter or self.INCIDENT_FILTER_ALL
        return [
            report
            for report in reports
            if self._matches_incident_filter(report, clean_filter)
        ]

    def _build_session_report(self, row: dict, *, now: datetime) -> SessionReport:
        is_active = bool(row["is_active"])
        started = self._parse_datetime(row.get("clock_in_time"))
        ended = self._parse_datetime(row.get("clock_out_time"))

        counted_duration_seconds: int | None = None
        display_duration_seconds: int | None = None

        if is_active:
            if started:
                display_duration_seconds = max(int((now - started).total_seconds()), 0)
        else:
            counted_duration_seconds = self._closed_duration_seconds(row, started, ended)
            display_duration_seconds = counted_duration_seconds

        excess = exceeded_shift_threshold_hours(display_duration_seconds)
        previous_open = bool(is_active and started and started.date() < now.date())

        labels: list[str] = []
        if previous_open:
            labels.append("Abierta de dia anterior")
        if excess:
            labels.append(f"Turno >{excess}h")
        if row.get("closed_by_admin"):
            labels.append("Cierre admin")

        incident_label = incident_type_label(row.get("incident_type"))
        if incident_label:
            labels.append(incident_label)

        severity = "none"
        if previous_open or (excess is not None and excess >= 12):
            severity = "critical"
        elif labels:
            severity = "warning"

        return SessionReport(
            id=int(row["id"]),
            user_id=int(row["user_id"]),
            employee_name=row.get("employee_name") or "",
            dni=row.get("dni") or "",
            clock_in_time=row.get("clock_in_time") or "",
            clock_out_time=row.get("clock_out_time"),
            is_active=is_active,
            total_seconds=row.get("total_seconds"),
            notes=row.get("notes"),
            exit_note=row.get("exit_note"),
            incident_type=row.get("incident_type"),
            closed_by_admin=bool(row.get("closed_by_admin")),
            manual_close_reason=row.get("manual_close_reason"),
            closed_by_user_id=row.get("closed_by_user_id"),
            display_duration_seconds=display_duration_seconds,
            counted_duration_seconds=counted_duration_seconds,
            excess_threshold_hours=excess,
            is_open_from_previous_day=previous_open,
            incident_labels=tuple(labels),
            severity=severity,
        )

    def _matches_incident_filter(
        self,
        report: SessionReport,
        incident_filter: str,
    ) -> bool:
        if incident_filter == self.INCIDENT_FILTER_ANY:
            return report.has_incident
        if incident_filter == self.INCIDENT_FILTER_PREVIOUS_OPEN:
            return report.is_open_from_previous_day
        if incident_filter == self.INCIDENT_FILTER_EXCESS_8:
            return bool(report.excess_threshold_hours and report.excess_threshold_hours >= 8)
        if incident_filter == self.INCIDENT_FILTER_EXCESS_10:
            return bool(report.excess_threshold_hours and report.excess_threshold_hours >= 10)
        if incident_filter == self.INCIDENT_FILTER_EXCESS_12:
            return bool(report.excess_threshold_hours and report.excess_threshold_hours >= 12)
        return True

    def _closed_duration_seconds(
        self,
        row: dict,
        started: datetime | None,
        ended: datetime | None,
    ) -> int:
        total_seconds = row.get("total_seconds")
        if total_seconds is not None:
            return max(int(total_seconds), 0)
        if not started or not ended:
            return 0
        return max(int((ended - started).total_seconds()), 0)

    def _day_bounds(self, target: date) -> tuple[datetime, datetime]:
        start = datetime.combine(target, time.min)
        return start, start + timedelta(days=1)

    def _week_bounds(self, target: date) -> tuple[datetime, datetime]:
        day_start = datetime.combine(target, time.min)
        start = day_start - timedelta(days=target.weekday())
        return start, start + timedelta(days=7)

    def _month_bounds(self, target: date) -> tuple[datetime, datetime]:
        start = datetime.combine(target.replace(day=1), time.min)
        if target.month == 12:
            next_month = date(target.year + 1, 1, 1)
        else:
            next_month = date(target.year, target.month + 1, 1)
        return start, datetime.combine(next_month, time.min)

    def _overlap_seconds(
        self,
        start_a: datetime,
        end_a: datetime,
        start_b: datetime,
        end_b: datetime,
    ) -> int:
        overlap_start = max(start_a, start_b)
        overlap_end = min(end_a, end_b)
        if overlap_end <= overlap_start:
            return 0
        return int((overlap_end - overlap_start).total_seconds())

    def _parse_datetime(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return None

    def _format_datetime(self, value: datetime) -> str:
        return value.replace(microsecond=0).isoformat(sep=" ")


@dataclass
class _MutableWorkSummary:
    employee_id: int
    total_seconds: int = 0
    shift_count: int = 0
    shift_seconds_total: int = 0

    def to_work_summary(self, *, start: datetime, end: datetime) -> WorkSummary:
        average_seconds = 0
        if self.shift_count:
            average_seconds = int(self.shift_seconds_total / self.shift_count)
        return WorkSummary(
            employee_id=self.employee_id,
            period_start=start,
            period_end=end,
            total_seconds=self.total_seconds,
            shift_count=self.shift_count,
            average_seconds=average_seconds,
        )
