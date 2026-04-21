from dataclasses import dataclass

from app.database.sql import normalize_datetime


@dataclass(frozen=True)
class BusinessUser:
    id: int
    business_id: str
    user_id: int
    role: str
    status: str
    invited_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    @classmethod
    def from_row(cls, row) -> "BusinessUser":
        d = dict(row)
        return cls(
            id=int(d["id"]),
            business_id=d["business_id"],
            user_id=int(d["user_id"]),
            role=d["role"],
            status=d["status"],
            invited_at=normalize_datetime(d.get("invited_at")),
            created_at=normalize_datetime(d.get("created_at")),
            updated_at=normalize_datetime(d.get("updated_at")),
        )
