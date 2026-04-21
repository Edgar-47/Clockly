from __future__ import annotations

from dataclasses import dataclass

_DAY_NAMES_ES = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
_DAY_NAMES_SHORT = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")


@dataclass(frozen=True)
class ScheduleDay:
    id: int
    schedule_id: int
    day_of_week: int          # 0 = Monday … 6 = Sunday
    start_time: str           # "HH:MM:SS" string from DB
    end_time: str
    break_minutes: int
    late_tolerance_minutes: int
    early_leave_tolerance_minutes: int

    @staticmethod
    def from_row(row: dict) -> ScheduleDay:
        return ScheduleDay(
            id=int(row["id"]),
            schedule_id=int(row["schedule_id"]),
            day_of_week=int(row["day_of_week"]),
            start_time=str(row.get("start_time") or "09:00:00"),
            end_time=str(row.get("end_time") or "17:00:00"),
            break_minutes=int(row.get("break_minutes") or 0),
            late_tolerance_minutes=int(row.get("late_tolerance_minutes") or 0),
            early_leave_tolerance_minutes=int(row.get("early_leave_tolerance_minutes") or 0),
        )

    @property
    def day_name(self) -> str:
        if 0 <= self.day_of_week <= 6:
            return _DAY_NAMES_ES[self.day_of_week]
        return str(self.day_of_week)

    @property
    def day_name_short(self) -> str:
        if 0 <= self.day_of_week <= 6:
            return _DAY_NAMES_SHORT[self.day_of_week]
        return str(self.day_of_week)

    @property
    def start_time_display(self) -> str:
        return self.start_time[:5]

    @property
    def end_time_display(self) -> str:
        return self.end_time[:5]

    @property
    def net_minutes(self) -> int:
        """Planned work minutes: (end - start) minus break."""
        try:
            sh, sm = int(self.start_time[:2]), int(self.start_time[3:5])
            eh, em = int(self.end_time[:2]), int(self.end_time[3:5])
            total = (eh * 60 + em) - (sh * 60 + sm)
            return max(total - self.break_minutes, 0)
        except (ValueError, IndexError):
            return 0

    @property
    def net_hours_label(self) -> str:
        h, m = divmod(self.net_minutes, 60)
        if m:
            return f"{h}h {m}m"
        return f"{h}h"
