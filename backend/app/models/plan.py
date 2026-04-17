from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.models.plan_constants import PlanCode, PlanFeature


@dataclass(frozen=True)
class Plan:
    id: int
    code: str
    name: str
    max_employees: int
    max_admins: int
    # Infrastructure features
    has_kiosk: bool
    has_geolocation: bool
    has_multi_location: bool
    # Reporting & export features
    has_advanced_reports: bool
    has_exports_basic: bool
    has_exports_advanced: bool
    # Operational features
    has_filters_advanced: bool
    has_incident_management: bool
    has_admin_closures: bool
    # Implementation
    has_implementation_support: bool
    has_priority_support: bool
    has_custom_branding: bool
    # Billing
    price_monthly: Decimal
    price_yearly: Decimal
    is_active: bool

    # ------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------

    @property
    def is_free(self) -> bool:
        return self.code == PlanCode.FREE

    @property
    def is_pro(self) -> bool:
        return self.code == PlanCode.PRO

    @property
    def is_enterprise(self) -> bool:
        return self.code == PlanCode.ENTERPRISE

    @property
    def is_paid(self) -> bool:
        return self.price_monthly > 0

    @property
    def display_price(self) -> str:
        if self.price_monthly == 0:
            return "Gratis"
        return f"{self.price_monthly:.0f}€/mes"

    def has_feature(self, feature: str) -> bool:
        """Return True if this plan includes the given feature key."""
        mapping = _feature_attr_map()
        attr = mapping.get(feature)
        if attr is None:
            return False
        return bool(getattr(self, attr, False))

    @classmethod
    def from_row(cls, row) -> "Plan":
        d = dict(row)
        return cls(
            id=int(d["id"]),
            code=d["code"],
            name=d["name"],
            max_employees=int(d["max_employees"]),
            max_admins=int(d["max_admins"]),
            has_kiosk=bool(d["has_kiosk"]),
            has_geolocation=bool(d.get("has_geolocation", False)),
            has_multi_location=bool(d.get("has_multi_location", False)),
            has_advanced_reports=bool(d.get("has_advanced_reports", False)),
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
            is_active=bool(d["is_active"]),
        )


def _feature_attr_map() -> dict[str, str]:
    """Map PlanFeature keys → Plan attribute names."""
    return {
        PlanFeature.KIOSK: "has_kiosk",
        PlanFeature.GEOLOCATION: "has_geolocation",
        PlanFeature.MULTI_LOCATION: "has_multi_location",
        PlanFeature.ADVANCED_REPORTS: "has_advanced_reports",
        PlanFeature.EXPORTS_BASIC: "has_exports_basic",
        PlanFeature.EXPORTS_ADVANCED: "has_exports_advanced",
        PlanFeature.FILTERS_ADVANCED: "has_filters_advanced",
        PlanFeature.INCIDENT_MANAGEMENT: "has_incident_management",
        PlanFeature.ADMIN_CLOSURES: "has_admin_closures",
        PlanFeature.IMPLEMENTATION_SUPPORT: "has_implementation_support",
        PlanFeature.PRIORITY_SUPPORT: "has_priority_support",
        PlanFeature.CUSTOM_BRANDING: "has_custom_branding",
    }
