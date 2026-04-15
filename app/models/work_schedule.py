from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WorkSchedule:
    id: int
    business_id: str | None
    name: str
    description: str | None
    weekly_hours_target: float | None
    schedule_type: str          # 'flexible' | 'strict'
    is_active: bool
    created_at: str
    updated_at: str

    @staticmethod
    def from_row(row: dict) -> WorkSchedule:
        return WorkSchedule(
            id=int(row["id"]),
            business_id=row.get("business_id"),
            name=row["name"],
            description=row.get("description"),
            weekly_hours_target=row.get("weekly_hours_target"),
            schedule_type=str(row.get("schedule_type") or "flexible"),
            is_active=bool(row.get("is_active", True)),
            created_at=str(row.get("created_at") or ""),
            updated_at=str(row.get("updated_at") or ""),
        )

    @property
    def weekly_hours_label(self) -> str:
        if self.weekly_hours_target is None:
            return "—"
        return f"{self.weekly_hours_target:.1f}h/semana"

    @property
    def schedule_type_label(self) -> str:
        return "Estricto" if self.schedule_type == "strict" else "Flexible"

    @property
    def is_strict(self) -> bool:
        return self.schedule_type == "strict"
