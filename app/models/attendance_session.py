from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AttendanceSession:
    id: int
    user_id: int
    clock_in_time: str
    clock_out_time: str | None
    is_active: bool
    total_seconds: int | None = None
    notes: str | None = None
    exit_note: str | None = None
    incident_type: str | None = None
    closed_by_admin: bool = False
    manual_close_reason: str | None = None
    closed_by_user_id: int | None = None

    @classmethod
    def from_row(cls, row) -> "AttendanceSession":
        d = dict(row)
        return cls(
            id=d["id"],
            user_id=d["user_id"],
            clock_in_time=d["clock_in_time"],
            clock_out_time=d["clock_out_time"],
            is_active=bool(d["is_active"]),
            total_seconds=d.get("total_seconds"),
            notes=d.get("notes"),
            exit_note=d.get("exit_note"),
            incident_type=d.get("incident_type"),
            closed_by_admin=bool(d.get("closed_by_admin", 0)),
            manual_close_reason=d.get("manual_close_reason"),
            closed_by_user_id=d.get("closed_by_user_id"),
        )

    def elapsed_seconds(self, now: datetime | None = None) -> int:
        if self.total_seconds is not None and not self.is_active:
            return int(self.total_seconds)

        try:
            started = datetime.fromisoformat(self.clock_in_time)
        except (TypeError, ValueError):
            return 0

        current = now or datetime.now()
        return max(int((current - started).total_seconds()), 0)
