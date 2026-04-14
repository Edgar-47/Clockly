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
    settings_json: str = "{}"
    last_accessed_at: str | None = None
    is_active: bool = True
    created_at: str | None = None
    updated_at: str | None = None

    @property
    def short_id(self) -> str:
        return self.id.split("-", 1)[0].upper()

    @classmethod
    def from_row(cls, row) -> "Business":
        d = dict(row)
        return cls(
            id=d["id"],
            owner_user_id=int(d["owner_user_id"]),
            business_name=d["business_name"],
            business_type=d["business_type"],
            login_code=d["login_code"],
            slug=d["slug"],
            business_key=d["business_key"],
            settings_json=d.get("settings_json") or "{}",
            last_accessed_at=normalize_datetime(d.get("last_accessed_at")),
            is_active=bool(d.get("is_active", 1)),
            created_at=normalize_datetime(d.get("created_at")),
            updated_at=normalize_datetime(d.get("updated_at")),
        )
