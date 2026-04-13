from datetime import datetime

from app.database.attendance_session_repository import AttendanceSessionRepository
from app.database.employee_repository import EmployeeRepository
from app.database.time_entry_repository import TimeEntryRepository
from app.models.attendance_session import AttendanceSession
from app.models.attendance_status import AttendanceStatus
from app.models.employee import Employee
from app.models.time_entry import TimeEntry


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
        self.time_entry_repository = time_entry_repository or TimeEntryRepository()

    def register(self, *, employee_id: int, entry_type: str) -> int:
        if entry_type not in self.VALID_TYPES:
            raise ValueError("Tipo de fichaje no valido.")

        if entry_type == self.ENTRY:
            session = self.start_session_for_employee(employee_id)
            return session.id

        session = self.clock_out_employee(employee_id)
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
            notes="Started automatically on login",
        )
        self.time_entry_repository.create(
            employee_id=employee.id,
            entry_type=self.ENTRY,
            timestamp=timestamp,
            notes="Automatic clock-in on login",
        )
        session = self.attendance_session_repository.get_by_id(session_id)
        if session is None:
            raise RuntimeError("No se pudo crear la sesion de asistencia.")
        return session

    def clock_out_employee(self, employee_id: int) -> AttendanceSession:
        employee = self._require_clockable_employee(employee_id)
        active = self.attendance_session_repository.get_active_for_user(employee.id)
        if not active:
            raise ValueError("No hay una sesion activa para cerrar.")

        timestamp = self._now_local()
        total_seconds = self._seconds_between(active.clock_in_time, timestamp)
        self.attendance_session_repository.clock_out(
            session_id=active.id,
            clock_out_time=timestamp,
            total_seconds=total_seconds,
            notes="Clocked out by user",
        )
        self.time_entry_repository.create(
            employee_id=employee.id,
            entry_type=self.EXIT,
            timestamp=timestamp,
            notes="Clock-out saved from attendance session",
        )
        session = self.attendance_session_repository.get_by_id(active.id)
        if session is None:
            raise RuntimeError("No se pudo cerrar la sesion de asistencia.")
        return session

    def get_last_entry(self, employee_id: int) -> TimeEntry | None:
        return self.time_entry_repository.get_last_for_employee(employee_id)

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
        latest_by_employee = self.time_entry_repository.get_latest_for_employees(
            [employee.id for employee in employees]
        )
        active_by_employee = self.attendance_session_repository.get_active_for_users(
            [employee.id for employee in employees]
        )
        return [
            AttendanceStatus(
                employee=employee,
                last_entry=latest_by_employee.get(employee.id),
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

    def _validate_sequence(self, last_entry: TimeEntry | None, entry_type: str) -> None:
        if entry_type == self.ENTRY and last_entry and last_entry.entry_type == self.ENTRY:
            raise ValueError("Ya tienes una entrada registrada. Ficha salida primero.")

        if entry_type == self.EXIT and (
            last_entry is None or last_entry.entry_type == self.EXIT
        ):
            raise ValueError("No puedes fichar salida sin una entrada abierta.")

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
