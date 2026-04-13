from datetime import datetime

from app.database.attendance_session_repository import AttendanceSessionRepository
from app.database.employee_repository import EmployeeRepository
from app.database.time_entry_repository import TimeEntryRepository
from app.models.attendance_session import AttendanceSession
from app.models.attendance_status import AttendanceStatus
from app.models.employee import Employee
from app.models.time_entry import TimeEntry
from app.services.attendance_policy import (
    normalize_exit_note,
    normalize_incident_type,
)


class TimeClockService:
    ENTRY = "entrada"
    EXIT = "salida"
    VALID_TYPES = {ENTRY, EXIT}

    def __init__(
        self,
        employee_repository: EmployeeRepository | None = None,
        attendance_session_repository: AttendanceSessionRepository | None = None,
        time_entry_repository: TimeEntryRepository | None = None,
    ) -> None:
        self.employee_repository = employee_repository or EmployeeRepository()
        self.attendance_session_repository = (
            attendance_session_repository or AttendanceSessionRepository()
        )
        # Legacy: kept only for get_last_entry(), which is used by admin_view.py
        # and clock_view.py (inactive views). New code should read from
        # attendance_session_repository instead.
        self.time_entry_repository = time_entry_repository or TimeEntryRepository()

    def register(
        self,
        *,
        employee_id: int,
        entry_type: str,
        exit_note: str | None = None,
        incident_type: str | None = None,
    ) -> int:
        if entry_type not in self.VALID_TYPES:
            raise ValueError("Tipo de fichaje no valido.")

        if entry_type == self.ENTRY:
            session = self.start_session_for_employee(employee_id)
            return session.id

        session = self.clock_out_employee(
            employee_id,
            exit_note=exit_note,
            incident_type=incident_type,
        )
        return session.id

    def start_session_for_employee(self, employee_id: int) -> AttendanceSession:
        employee = self._require_clockable_employee(employee_id)
        active = self.attendance_session_repository.get_active_for_user(employee.id)
        if active:
            return active

        timestamp = self._now_local()
        session_id = self.attendance_session_repository.create(
            user_id=employee.id,
            clock_in_time=timestamp,
        )
        session = self.attendance_session_repository.get_by_id(session_id)
        if session is None:
            raise RuntimeError("No se pudo crear la sesion de asistencia.")
        return session

    def clock_out_employee(
        self,
        employee_id: int,
        *,
        exit_note: str | None = None,
        incident_type: str | None = None,
    ) -> AttendanceSession:
        employee = self._require_clockable_employee(employee_id)
        active = self.attendance_session_repository.get_active_for_user(employee.id)
        if not active:
            raise ValueError("No hay una sesion activa para cerrar.")

        clean_exit_note = normalize_exit_note(exit_note)
        clean_incident_type = normalize_incident_type(incident_type)
        timestamp = self._now_local()
        total_seconds = self._seconds_between(active.clock_in_time, timestamp)
        self.attendance_session_repository.clock_out(
            session_id=active.id,
            clock_out_time=timestamp,
            total_seconds=total_seconds,
            exit_note=clean_exit_note,
            incident_type=clean_incident_type,
        )
        session = self.attendance_session_repository.get_by_id(active.id)
        if session is None:
            raise RuntimeError("No se pudo cerrar la sesion de asistencia.")
        return session

    def get_active_session(self, employee_id: int) -> AttendanceSession | None:
        return self.attendance_session_repository.get_active_for_user(employee_id)

    def get_attendance_status(self, employee: Employee) -> AttendanceStatus:
        return AttendanceStatus(
            employee=employee,
            last_entry=self.get_last_entry(employee.id),
            active_session=self.get_active_session(employee.id),
        )

    def get_attendance_statuses(
        self,
        employees: list[Employee],
    ) -> list[AttendanceStatus]:
        # Only fetch active sessions — the canonical source of truth.
        # last_entry (from legacy time_entries) is not populated here because
        # no active view relies on it; admin_view.py reads it separately.
        active_by_employee = self.attendance_session_repository.get_active_for_users(
            [employee.id for employee in employees]
        )
        return [
            AttendanceStatus(
                employee=employee,
                active_session=active_by_employee.get(employee.id),
            )
            for employee in employees
        ]

    def list_current_statuses(self, *, active_only: bool = True) -> list[AttendanceStatus]:
        employees = (
            self.employee_repository.list_active()
            if active_only
            else self.employee_repository.list_all()
        )
        return self.get_attendance_statuses(employees)

    def list_currently_clocked_in(
        self,
        *,
        active_only: bool = True,
    ) -> list[AttendanceStatus]:
        return [
            status
            for status in self.list_current_statuses(active_only=active_only)
            if status.is_clocked_in
        ]

    def list_currently_clocked_out(
        self,
        *,
        active_only: bool = True,
    ) -> list[AttendanceStatus]:
        return [
            status
            for status in self.list_current_statuses(active_only=active_only)
            if not status.is_clocked_in
        ]

    def admin_close_session(
        self,
        session_id: int,
        *,
        reason: str,
        admin_user_id: int,
    ) -> AttendanceSession:
        """
        Close an active session from the admin panel.
        Requires a non-empty reason. Records who closed it and why.
        Raises ValueError if session not found, already closed, or reason missing.
        """
        clean_reason = reason.strip()
        if not clean_reason:
            raise ValueError("El motivo del cierre es obligatorio.")

        session = self.attendance_session_repository.get_by_id(session_id)
        if session is None:
            raise ValueError("Sesión no encontrada.")
        if not session.is_active:
            raise ValueError("Esta sesión ya está cerrada.")

        timestamp = self._now_local()
        total_seconds = self._seconds_between(session.clock_in_time, timestamp)
        clean_exit_note = normalize_exit_note(clean_reason)
        self.attendance_session_repository.admin_clock_out(
            session_id=session_id,
            clock_out_time=timestamp,
            total_seconds=total_seconds,
            reason=clean_reason,
            closed_by_user_id=admin_user_id,
            exit_note=clean_exit_note,
            incident_type="correccion_manual",
        )
        updated = self.attendance_session_repository.get_by_id(session_id)
        if updated is None:
            raise RuntimeError("Error al cerrar la sesión.")
        return updated

    # ── Legacy API ────────────────────────────────────────────────────────────
    # Used by admin_view.py, clock_view.py, clock_kiosk_view.py (inactive views).
    # New views read directly from attendance_session_repository.

    def get_last_entry(self, employee_id: int) -> TimeEntry | None:
        """Legacy: returns last time_entry for an employee."""
        return self.time_entry_repository.get_last_for_employee(employee_id)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _require_clockable_employee(self, employee_id: int) -> Employee:
        employee = self.employee_repository.get_by_id(employee_id)
        if not employee or not employee.active:
            raise ValueError("Empleado no valido o inactivo.")
        if employee.role != "employee":
            raise ValueError("Solo los empleados pueden registrar asistencia.")
        return employee

    def _now_local(self) -> str:
        return datetime.now().replace(microsecond=0).isoformat(sep=" ")

    def _seconds_between(self, start: str, end: str) -> int:
        try:
            started = datetime.fromisoformat(start)
            ended = datetime.fromisoformat(end)
        except (TypeError, ValueError):
            return 0
        return max(int((ended - started).total_seconds()), 0)
