from dataclasses import dataclass

from app.database.sql import normalize_datetime
from app.models.plan import Plan


@dataclass(frozen=True)
class Subscription:
    id: int
    business_id: str
    plan_id: int
    status: str
    current_period_start: str | None
    current_period_end: str | None
    stripe_customer_id: str | None
    stripe_subscription_id: str | None
    created_at: str | None = None
    updated_at: str | None = None
    plan: Plan | None = None

    @classmethod
    def from_row(cls, row) -> "Subscription":
        d = dict(row)
        plan = None
        if "plan_code" in d:
            plan = Plan(
                id=int(d["plan_id"]),
                code=d["plan_code"],
                name=d["plan_name"],
                max_employees=int(d["max_employees"]),
                max_admins=int(d["max_admins"]),
                has_kiosk=bool(d["has_kiosk"]),
                has_advanced_reports=bool(d["has_advanced_reports"]),
                has_geolocation=bool(d["has_geolocation"]),
                has_multi_location=bool(d["has_multi_location"]),
                price_monthly=d["price_monthly"],
                price_yearly=d["price_yearly"],
                is_active=bool(d["plan_is_active"]),
            )
        return cls(
            id=int(d["id"]),
            business_id=d["business_id"],
            plan_id=int(d["plan_id"]),
            status=d["status"],
            current_period_start=normalize_datetime(d.get("current_period_start")),
            current_period_end=normalize_datetime(d.get("current_period_end")),
            stripe_customer_id=d.get("stripe_customer_id"),
            stripe_subscription_id=d.get("stripe_subscription_id"),
            created_at=normalize_datetime(d.get("created_at")),
            updated_at=normalize_datetime(d.get("updated_at")),
            plan=plan,
        )
