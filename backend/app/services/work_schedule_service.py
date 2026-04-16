"""
app/services/work_schedule_service.py

Schedule template management, employee assignment, and planned-hours calculation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.database.employee_repository import EmployeeRepository
from app.database.work_schedule_repository import WorkScheduleRepository
from app.models.employee_schedule import EmployeeSchedule
from app.models.schedule_day import ScheduleDay
from app.models.work_schedule import WorkSchedule


@dataclass(frozen=True)
class ScheduleWithDays:
    schedule: WorkSchedule
    days: list[ScheduleDay]

    @property
    def weekly_planned_minutes(self) -> int:
        return sum(d.net_minutes for d in self.days)

    @property
    def weekly_planned_hours_label(self) -> str:
        total = self.weekly_planned_minutes
        h, m = divmod(total, 60)
        if m:
            return f"{h}h {m}m/semana"
        return f"{h}h/semana"


@dataclass(frozen=True)
class PlannedVsActual:
    employee_id: int
    employee_name: str
    period_start: date
    period_end: date
    planned_seconds: int
    actual_seconds: int
    variance_seconds: int   # actual - planned (positive = overtime, negative = under)

    @property
    def variance_label(self) -> str:
        from app.services.analytics_service import _fmt_hours
        sign = "+" if self.variance_seconds >= 0 else "–"
        return f"{sign}{_fmt_hours(abs(self.variance_seconds))}"

    @property
    def variance_pct(self) -> float:
        if not self.planned_seconds:
            return 0.0
        return round(self.variance_seconds / self.planned_seconds * 100, 1)

    @property
    def status(self) -> str:
        if self.variance_seconds > 3600:
            return "overtime"
        if self.variance_seconds < -3600:
            return "under"
        return "ok"


class WorkScheduleService:

    def __init__(
        self,
        work_schedule_repository: WorkScheduleRepository | None = None,
        *,
        business_id: str | None = None,
    ) -> None:
        self.business_id = business_id
        self.repo = (
            work_schedule_repository or WorkScheduleRepository(business_id=business_id)
        )

    # ------------------------------------------------------------------
    # Schedule templates
    # ------------------------------------------------------------------

    def list_schedules(self) -> list[ScheduleWithDays]:
        schedules = self.repo.list_all()
        return [
            ScheduleWithDays(s, self.repo.get_days(s.id))
            for s in schedules
        ]

    def list_active_schedules(self) -> list[ScheduleWithDays]:
        schedules = self.repo.list_active()
        return [
            ScheduleWithDays(s, self.repo.get_days(s.id))
            for s in schedules
        ]

    def get_schedule(self, schedule_id: int) -> ScheduleWithDays | None:
        schedule = self.repo.get_by_id(schedule_id)
        if not schedule:
            return None
        days = self.repo.get_days(schedule_id)
        return ScheduleWithDays(schedule, days)

    def create_schedule(
        self,
        *,
        name: str,
        description: str | None = None,
        weekly_hours_target: float | None = None,
        schedule_type: str = "flexible",
        days: list[dict],
    ) -> int:
        """
        Create a schedule template with its day definitions.
        `days` is a list of dicts (see WorkScheduleRepository.replace_days).
        Raises ValueError on validation failure.
        """
        name = (name or "").strip()
        if len(name) < 2:
            raise ValueError("El nombre del horario debe tener al menos 2 caracteres.")
        if schedule_type not in ("flexible", "strict"):
            schedule_type = "flexible"
        if not days:
            raise ValueError("El horario debe tener al menos un día definido.")
        _validate_days(days)

        schedule_id = self.repo.create_schedule(
            name=name,
            description=description,
            weekly_hours_target=weekly_hours_target,
            schedule_type=schedule_type,
        )
        self.repo.replace_days(schedule_id, days)
        return schedule_id

    def update_schedule(
        self,
        schedule_id: int,
        *,
        name: str,
        description: str | None = None,
        weekly_hours_target: float | None = None,
        schedule_type: str = "flexible",
        is_active: bool = True,
        days: list[dict],
    ) -> None:
        name = (name or "").strip()
        if len(name) < 2:
            raise ValueError("El nombre del horario debe tener al menos 2 caracteres.")
        if schedule_type not in ("flexible", "strict"):
            schedule_type = "flexible"
        if not days:
            raise ValueError("El horario debe tener al menos un día definido.")
        _validate_days(days)

        self.repo.update_schedule(
            schedule_id,
            name=name,
            description=description,
            weekly_hours_target=weekly_hours_target,
            schedule_type=schedule_type,
            is_active=is_active,
        )
        self.repo.replace_days(schedule_id, days)

    def delete_schedule(self, schedule_id: int) -> None:
        """Soft-delete: deactivates the schedule."""
        # Deactivate all employee assignments first
        assignments = self.repo.list_assignments_for_schedule(schedule_id)
        for a in assignments:
            self.repo.deactivate_assignment(a.id)
        self.repo.delete_schedule(schedule_id)

    # ------------------------------------------------------------------
    # Employee assignments
    # ------------------------------------------------------------------

    def assign_schedule(
        self,
        *,
        user_id: int,
        schedule_id: int,
        effective_from: date,
        effective_to: date | None = None,
    ) -> int:
        if effective_to and effective_to < effective_from:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio.")
        if self.repo.get_by_id(schedule_id) is None:
            raise ValueError("Horario no encontrado para este negocio.")
        if self.business_id is not None:
            employee = EmployeeRepository(business_id=self.business_id).get_by_id(user_id)
            if employee is None or not employee.active:
                raise ValueError("Empleado no encontrado en este negocio.")
        return self.repo.create_assignment(
            user_id=user_id,
            schedule_id=schedule_id,
            effective_from=effective_from,
            effective_to=effective_to,
        )

    def get_current_assignment(
        self,
        user_id: int,
        reference_date: date | None = None,
    ) -> ScheduleWithDays | None:
        assignment = self.repo.get_active_assignment(user_id, reference_date)
        if not assignment:
            return None
        return self.get_schedule(assignment.schedule_id)

    def get_assignment_record(
        self,
        user_id: int,
        reference_date: date | None = None,
    ) -> EmployeeSchedule | None:
        return self.repo.get_active_assignment(user_id, reference_date)

    def list_assignments_for_user(self, user_id: int) -> list[EmployeeSchedule]:
        return self.repo.list_assignments_for_user(user_id)

    def list_assignments_for_schedule(self, schedule_id: int) -> list[EmployeeSchedule]:
        return self.repo.list_assignments_for_schedule(schedule_id)

    def deactivate_assignment(self, assignment_id: int) -> None:
        self.repo.deactivate_assignment(assignment_id)

    # ------------------------------------------------------------------
    # Planned vs actual comparison
    # ------------------------------------------------------------------

    def get_planned_seconds_for_period(
        self,
        user_id: int,
        *,
        start: date,
        end: date,
    ) -> int:
        """
        Sum up scheduled work-minutes for `user_id` in [start, end].
        Uses the assignment(s) active during the period.
        """
        total_minutes = 0
        cursor = start
        while cursor <= end:
            assignment = self.repo.get_active_assignment(user_id, cursor)
            if assignment:
                days = self.repo.get_days(assignment.schedule_id)
                day_def = next((d for d in days if d.day_of_week == cursor.weekday()), None)
                if day_def:
                    total_minutes += day_def.net_minutes
            cursor += timedelta(days=1)
        return total_minutes * 60

    def build_planned_vs_actual(
        self,
        *,
        start: date,
        end: date,
        actual_seconds_by_user: dict[int, tuple[str, int]],  # user_id → (name, actual_seconds)
    ) -> list[PlannedVsActual]:
        """
        For each user in actual_seconds_by_user, compute planned vs actual.
        """
        results: list[PlannedVsActual] = []
        for user_id, (name, actual) in actual_seconds_by_user.items():
            planned = self.get_planned_seconds_for_period(user_id, start=start, end=end)
            results.append(PlannedVsActual(
                employee_id=user_id,
                employee_name=name,
                period_start=start,
                period_end=end,
                planned_seconds=planned,
                actual_seconds=actual,
                variance_seconds=actual - planned,
            ))
        return sorted(results, key=lambda r: r.variance_seconds, reverse=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DAY_NAMES = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")


def _validate_days(days: list[dict]) -> None:
    seen_dows: set[int] = set()
    for day in days:
        dow = int(day.get("day_of_week", -1))
        if dow not in range(7):
            raise ValueError(f"Día de semana inválido: {dow}")
        if dow in seen_dows:
            raise ValueError(f"{_DAY_NAMES[dow]} aparece más de una vez.")
        seen_dows.add(dow)
        _validate_time_str(str(day.get("start_time", "")), "Hora inicio")
        _validate_time_str(str(day.get("end_time", "")), "Hora fin")


def _validate_time_str(value: str, label: str) -> None:
    parts = value.strip().split(":")
    try:
        h, m = int(parts[0]), int(parts[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError
    except (ValueError, IndexError):
        raise ValueError(f"{label} tiene formato inválido. Use HH:MM.")
