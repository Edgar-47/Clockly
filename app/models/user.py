from dataclasses import dataclass

from app.database.sql import normalize_datetime


@dataclass(frozen=True)
class User:
    id: int
    email: str | None
    full_name: str
    google_id: str | None
    auth_provider: str
    password_hash: str | None
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None
    first_name: str = ""
    last_name: str = ""
    dni: str = ""
    role: str = "employee"

    @classmethod
    def from_row(cls, row) -> "User":
        d = dict(row)
        first_name = d.get("first_name") or ""
        last_name = d.get("last_name") or ""
        full_name = d.get("full_name") or f"{first_name} {last_name}".strip()
        active = d.get("is_active", d.get("active", True))
        return cls(
            id=int(d["id"]),
            email=d.get("email"),
            full_name=full_name,
            google_id=d.get("google_id"),
            auth_provider=d.get("auth_provider") or "password",
            password_hash=d.get("password_hash"),
            is_active=bool(active),
            created_at=normalize_datetime(d.get("created_at")),
            updated_at=normalize_datetime(d.get("updated_at")),
            first_name=first_name,
            last_name=last_name,
            dni=d.get("dni") or "",
            role=d.get("role") or "employee",
        )
