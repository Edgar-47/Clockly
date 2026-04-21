from dataclasses import dataclass
from decimal import Decimal

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
    billing_cycle: str = "monthly"
    price: Decimal = Decimal("0")
    currency: str = "EUR"
    renewal_date: str | None = None
    cancel_at: str | None = None
    cancelled_at: str | None = None
    trial_ends_at: str | None = None
    paused_at: str | None = None
    payment_status: str = "none"
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    plan: Plan | None = None

    @property
    def is_active(self) -> bool:
        return self.status in ("active", "trial", "trialing")

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
                has_advanced_reports=bool(d.get("has_advanced_reports", False)),
                has_geolocation=bool(d.get("has_geolocation", False)),
                has_multi_location=bool(d.get("has_multi_location", False)),
                has_exports_basic=bool(d.get("has_exports_basic", True)),
                has_exports_advanced=bool(d.get("has_exports_advanced", False)),
                has_filters_advanced=bool(d.get("has_filters_advanced", False)),
                has_incident_management=bool(d.get("has_incident_management", False)),
                has_admin_closures=bool(d.get("has_admin_closures", False)),
                has_implementation_support=bool(d.get("has_implementation_support", False)),
                has_priority_support=bool(d.get("has_priority_support", False)),
                has_custom_branding=bool(d.get("has_custom_branding", False)),
                price_monthly=Decimal(str(d["price_monthly"])),
                price_yearly=Decimal(str(d["price_yearly"])),
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
            billing_cycle=d.get("billing_cycle") or "monthly",
            price=Decimal(str(d.get("price") or d.get("price_monthly") or 0)),
            currency=d.get("currency") or "EUR",
            renewal_date=normalize_datetime(d.get("renewal_date")),
            cancel_at=normalize_datetime(d.get("cancel_at")),
            cancelled_at=normalize_datetime(d.get("cancelled_at")),
            trial_ends_at=normalize_datetime(d.get("trial_ends_at")),
            paused_at=normalize_datetime(d.get("paused_at")),
            payment_status=d.get("payment_status") or "none",
            notes=d.get("notes"),
            created_at=normalize_datetime(d.get("created_at")),
            updated_at=normalize_datetime(d.get("updated_at")),
            plan=plan,
        )
