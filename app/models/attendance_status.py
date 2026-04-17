from dataclasses import dataclass

from app.models.attendance_session import AttendanceSession
from app.models.employee import Employee


@dataclass(frozen=True)
class AttendanceStatus:
    employee: Employee
    active_session: AttendanceSession | None = None
    latest_session: AttendanceSession | None = None

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
        if self.latest_session:
            return "Clock Out" if self.latest_session.clock_out_time else "Clock In"
        return "No records"

    @property
    def last_timestamp(self) -> str | None:
        if self.is_clocked_in and self.active_session:
            return self.active_session.clock_in_time
        if self.latest_session:
            return self.latest_session.clock_out_time or self.latest_session.clock_in_time
        return None
