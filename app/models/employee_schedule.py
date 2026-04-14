from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class EmployeeSchedule:
    id: int
    user_id: int
    schedule_id: int
    business_id: str | None
    effective_from: str       # ISO date string "YYYY-MM-DD"
    effective_to: str | None  # None = open-ended (still active)
    is_active: bool
    created_at: str
    # Joined fields (may be None if not fetched with JOIN)
    schedule_name: str | None = None
    employee_name: str | None = None

    @staticmethod
    def from_row(row: dict) -> EmployeeSchedule:
        return EmployeeSchedule(
            id=int(row["id"]),
            user_id=int(row["user_id"]),
            schedule_id=int(row["schedule_id"]),
            business_id=row.get("business_id"),
            effective_from=str(row.get("effective_from") or ""),
            effective_to=str(row["effective_to"]) if row.get("effective_to") else None,
            is_active=bool(row.get("is_active", True)),
            created_at=str(row.get("created_at") or ""),
            schedule_name=row.get("schedule_name"),
            employee_name=row.get("employee_name"),
        )

    def is_current(self, reference: date | None = None) -> bool:
        """True if this assignment is in effect on the reference date (default today)."""
        if not self.is_active:
            return False
        ref = reference or date.today()
        try:
            from_date = date.fromisoformat(self.effective_from)
        except (ValueError, TypeError):
            return False
        if ref < from_date:
            return False
        if self.effective_to:
            try:
                to_date = date.fromisoformat(self.effective_to)
                return ref <= to_date
            except (ValueError, TypeError):
                pass
        return True
