from dataclasses import dataclass

from app.models.attendance_session import AttendanceSession
from app.models.employee import Employee
from app.models.time_entry import TimeEntry


@dataclass(frozen=True)
class AttendanceStatus:
    employee: Employee
    last_entry: TimeEntry | None = None
    active_session: AttendanceSession | None = None

    @property
    def is_clocked_in(self) -> bool:
        return bool(self.active_session and self.active_session.is_active)

    @property
    def status_label(self) -> str:
        return "Clocked In" if self.is_clocked_in else "Clocked Out"

    @property
    def last_action_label(self) -> str:
        if self.is_clocked_in:
            return "Clock In"
        if not self.last_entry:
            return "No records"
        return "Clock In" if self.last_entry.entry_type == "entrada" else "Clock Out"

    @property
    def last_timestamp(self) -> str | None:
        if self.is_clocked_in and self.active_session:
            return self.active_session.clock_in_time
        return self.last_entry.timestamp if self.last_entry else None
