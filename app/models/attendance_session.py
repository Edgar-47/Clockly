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

    @classmethod
    def from_row(cls, row) -> "AttendanceSession":
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            clock_in_time=row["clock_in_time"],
            clock_out_time=row["clock_out_time"],
            is_active=bool(row["is_active"]),
            total_seconds=row["total_seconds"],
            notes=row["notes"],
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
