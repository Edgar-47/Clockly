from dataclasses import dataclass


@dataclass(frozen=True)
class TimeEntry:
    id: int
    employee_id: int
    entry_type: str
    timestamp: str
    notes: str | None = None
    business_id: str | None = None

    @classmethod
    def from_row(cls, row) -> "TimeEntry":
        return cls(
            id=row["id"],
            employee_id=row["employee_id"],
            entry_type=row["entry_type"],
            timestamp=row["timestamp"],
            notes=row["notes"],
            business_id=row["business_id"] if "business_id" in row.keys() else None,
        )
