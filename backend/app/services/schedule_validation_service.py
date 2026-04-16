"""
app/services/schedule_validation_service.py

Validates whether an employee is allowed to clock in at a given moment.

Rules:
- Employees with NO schedule assigned → always allowed.
- Employees with a FLEXIBLE schedule → always allowed (informational only).
- Employees with a STRICT schedule → allowed only if today's weekday is defined
  in the schedule AND the current time falls within
  [start_time - late_tolerance, end_time + early_leave_tolerance].

Callers receive a ClockInPermission with `allowed` bool and a human-readable
`reason` for UI error messages.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time

from app.database.work_schedule_repository import WorkScheduleRepository
from app.models.schedule_day import ScheduleDay
from app.models.work_schedule import WorkSchedule


@dataclass(frozen=True)
class ClockInPermission:
    allowed: bool
    reason: str  # empty when allowed, user-facing Spanish message when blocked


class ScheduleValidationService:

    def __init__(
        self,
        work_schedule_repository: WorkScheduleRepository | None = None,
        *,
        business_id: str | None = None,
    ) -> None:
        self._repo = work_schedule_repository or WorkScheduleRepository(
            business_id=business_id
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_clock_in(
        self,
        user_id: int,
        now: datetime | None = None,
    ) -> ClockInPermission:
        """
        Return ClockInPermission for *user_id* at the given moment (default: now).
        """
        now = now or datetime.now()
        ref_date = now.date()

        assignment = self._repo.get_active_assignment(user_id, ref_date)
        if assignment is None:
            # No schedule assigned — unrestricted
            return ClockInPermission(allowed=True, reason="")

        schedule = self._repo.get_by_id(assignment.schedule_id)
        if schedule is None or not schedule.is_strict:
            # Flexible schedule — always allowed
            return ClockInPermission(allowed=True, reason="")

        # Strict schedule — check the day definition
        days = self._repo.get_days(assignment.schedule_id)
        today_dow = now.weekday()  # 0 = Monday
        day_def = next((d for d in days if d.day_of_week == today_dow), None)

        if day_def is None:
            return ClockInPermission(
                allowed=False,
                reason=(
                    f"Tu horario ({schedule.name}) no contempla trabajo hoy "
                    f"({_dow_name(today_dow)}). El fichaje está bloqueado."
                ),
            )

        # Parse window boundaries
        window_open = _subtract_minutes(day_def.start_time, day_def.late_tolerance_minutes)
        window_close = _add_minutes(day_def.end_time, day_def.early_leave_tolerance_minutes)
        current_time = now.time().replace(second=0, microsecond=0)

        if current_time < window_open:
            return ClockInPermission(
                allowed=False,
                reason=(
                    f"Tu horario comienza a las {day_def.start_time_display}. "
                    f"El fichaje estará disponible a partir de las "
                    f"{_fmt_time(window_open)}."
                ),
            )

        if current_time > window_close:
            return ClockInPermission(
                allowed=False,
                reason=(
                    f"El horario de hoy finalizó a las {day_def.end_time_display}. "
                    f"El fichaje ya no está disponible."
                ),
            )

        return ClockInPermission(allowed=True, reason="")


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

_DOW_NAMES = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")


def _dow_name(dow: int) -> str:
    return _DOW_NAMES[dow] if 0 <= dow <= 6 else str(dow)


def _parse_time(value: str) -> time:
    """Parse HH:MM[:SS] → time, returning midnight on failure."""
    try:
        parts = str(value).split(":")
        return time(int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        return time(0, 0)


def _subtract_minutes(time_str: str, minutes: int) -> time:
    from datetime import date, timedelta
    t = _parse_time(time_str)
    dt = datetime.combine(date.today(), t) - timedelta(minutes=max(0, minutes))
    return dt.time().replace(second=0, microsecond=0)


def _add_minutes(time_str: str, minutes: int) -> time:
    from datetime import date, timedelta
    t = _parse_time(time_str)
    dt = datetime.combine(date.today(), t) + timedelta(minutes=max(0, minutes))
    return dt.time().replace(second=0, microsecond=0)


def _fmt_time(t: time) -> str:
    return t.strftime("%H:%M")
