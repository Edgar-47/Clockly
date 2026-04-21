from dataclasses import dataclass

from app.database.sql import normalize_datetime


@dataclass(frozen=True)
class Employee:
    id: int
    first_name: str
    last_name: str
    dni: str
    password_hash: str
    role: str
    active: bool
    created_at: str | None = None
    last_business_id: str | None = None
    email: str | None = None
    platform_role: str | None = None
    last_login_at: str | None = None
    force_password_change: bool = False

    @property
    def username(self) -> str:
        """Backward-compatible alias for older UI/export code."""
        return self.dni

    @property
    def name(self) -> str:
        """Backward-compatible display name used by older UI code."""
        return self.full_name

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def initials(self) -> str:
        parts = [self.first_name.strip(), self.last_name.strip()]
        letters = [part[0] for part in parts if part]
        if not letters and self.dni:
            letters = [self.dni[0]]
        return "".join(letters[:2]).upper()

    @classmethod
    def from_row(cls, row) -> "Employee":
        keys = set(row.keys())
        first_name = row["first_name"] if "first_name" in keys else ""
        last_name = row["last_name"] if "last_name" in keys else ""

        if (not first_name and not last_name) and "name" in keys:
            parts = str(row["name"] or "").strip().split(maxsplit=1)
            first_name = parts[0] if parts else ""
            last_name = parts[1] if len(parts) > 1 else ""

        dni = row["dni"] if "dni" in keys else row["username"]

        return cls(
            id=row["id"],
            first_name=first_name or "",
            last_name=last_name or "",
            dni=dni,
            password_hash=row["password_hash"],
            role=row["role"],
            active=bool(row["active"]),
            created_at=normalize_datetime(row["created_at"]) if "created_at" in keys else None,
            last_business_id=row["last_business_id"] if "last_business_id" in keys else None,
            email=row["email"] if "email" in keys else None,
            platform_role=row["platform_role"] if "platform_role" in keys else None,
            last_login_at=normalize_datetime(row["last_login_at"]) if "last_login_at" in keys else None,
            force_password_change=bool(row["force_password_change"]) if "force_password_change" in keys else False,
        )
