from datetime import datetime

from app.core.flow_debug import flow_log
from app.database.attendance_session_repository import AttendanceSessionRepository
from app.database.employee_repository import EmployeeRepository
from app.models.attendance_session import AttendanceSession
from app.models.attendance_status import AttendanceStatus
from app.models.employee import Employee
from app.services.attendance_policy import (
    normalize_exit_note,
    normalize_incident_type,
)
from app.services.schedule_validation_service import ScheduleValidationService


class TimeClockService:
    ENTRY = "entrada"
    EXIT = "salida"
    VALID_TYPES = {ENTRY, EXIT}

    def __init__(
        self,
        employee_repository: EmployeeRepository | None = None,
        attendance_session_repository: AttendanceSessionRepository | None = None,
        schedule_validation_service: ScheduleValidationService | None = None,
        *,
        business_id: str | None = None,
    ) -> None:
        self.business_id = business_id
        self.employee_repository = employee_repository or EmployeeRepository(
            business_id=business_id
        )
        self.attendance_session_repository = (
            attendance_session_repository or AttendanceSessionRepository(
                business_id=business_id
            )
        )
        self._schedule_validator = schedule_validation_service or ScheduleValidationService(
            business_id=business_id
        )

    def register(
        self,
        *,
        employee_id: int,
        entry_type: str,
        exit_note: str | None = None,
        incident_type: str | None = None,
    ) -> int:
        flow_log(
            "service.clock.register.request",
            employee_id=employee_id,
            entry_type=entry_type,
            has_exit_note=bool(exit_note),
            incident_type=incident_type,
        )
        if entry_type not in self.VALID_TYPES:
            raise ValueError("Tipo de fichaje no valido.")

        if entry_type == self.ENTRY:
            session = self.start_session_for_employee(employee_id)
            flow_log(
                "service.clock.register.result",
                employee_id=employee_id,
                entry_type=entry_type,
                session_id=session.id,
            )
            return session.id

        session = self.clock_out_employee(
            employee_id,
            exit_note=exit_note,
            incident_type=incident_type,
        )
        flow_log(
            "service.clock.register.result",
            employee_id=employee_id,
            entry_type=entry_type,
            session_id=session.id,
        )
        return session.id

    def start_session_for_employee(self, employee_id: int) -> AttendanceSession:
        employee = self._require_clockable_employee(employee_id)

        # Schedule enforcement: only blocks when a strict schedule is active
        permission = self._schedule_validator.validate_clock_in(employee.id)
        if not permission.allowed:
            raise ValueError(permission.reason)

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
        active_session = self.get_active_session(employee.id)
        latest_session = active_session or self.attendance_session_repository.get_latest_for_user(
            employee.id
        )
        return AttendanceStatus(
            employee=employee,
            active_session=active_session,
            latest_session=latest_session,
        )

    def get_attendance_statuses(
        self,
        employees: list[Employee],
    ) -> list[AttendanceStatus]:
        employee_ids = [employee.id for employee in employees]
        active_by_employee = self.attendance_session_repository.get_active_for_users(
            employee_ids
        )
        latest_by_employee = self.attendance_session_repository.get_latest_for_users(
            employee_ids
        )
        return [
            AttendanceStatus(
                employee=employee,
                active_session=active_by_employee.get(employee.id),
                latest_session=(
                    active_by_employee.get(employee.id)
                    or latest_by_employee.get(employee.id)
                ),
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
