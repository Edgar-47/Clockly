from dataclasses import dataclass

from app.database.sql import normalize_datetime


@dataclass(frozen=True)
class Business:
    id: str
    owner_user_id: int
    business_name: str
    business_type: str
    login_code: str
    slug: str
    business_key: str
    timezone: str = "Europe/Madrid"
    country: str | None = None
    settings_json: str = "{}"
    last_accessed_at: str | None = None
    is_active: bool = True
    created_at: str | None = None
    updated_at: str | None = None

    @property
    def short_id(self) -> str:
        return self.id.split("-", 1)[0].upper()

    @property
    def name(self) -> str:
        return self.business_name

    @classmethod
    def from_row(cls, row) -> "Business":
        d = dict(row)
        business_name = d.get("business_name") or d.get("name") or ""
        return cls(
            id=d["id"],
            owner_user_id=int(d["owner_user_id"]),
            business_name=business_name,
            business_type=d.get("business_type") or "otro",
            login_code=d["login_code"],
            slug=d["slug"],
            business_key=d["business_key"],
            timezone=d.get("timezone") or "Europe/Madrid",
            country=d.get("country"),
            settings_json=d.get("settings_json") or "{}",
            last_accessed_at=normalize_datetime(d.get("last_accessed_at")),
            is_active=bool(d.get("is_active", 1)),
            created_at=normalize_datetime(d.get("created_at")),
            updated_at=normalize_datetime(d.get("updated_at")),
        )
