from dataclasses import dataclass

from app.database.sql import normalize_datetime


@dataclass(frozen=True)
class SaaSEmployee:
    id: int
    business_id: str
    user_id: int | None
    internal_code: str
    pin_code: str | None
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    role_title: str | None
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @classmethod
    def from_row(cls, row) -> "SaaSEmployee":
        d = dict(row)
        return cls(
            id=int(d["id"]),
            business_id=d["business_id"],
            user_id=d.get("user_id"),
            internal_code=d["internal_code"],
            pin_code=d.get("pin_code"),
            first_name=d.get("first_name") or "",
            last_name=d.get("last_name") or "",
            email=d.get("email"),
            phone=d.get("phone"),
            role_title=d.get("role_title"),
            is_active=bool(d.get("is_active", True)),
            created_at=normalize_datetime(d.get("created_at")),
            updated_at=normalize_datetime(d.get("updated_at")),
        )
