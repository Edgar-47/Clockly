from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Plan:
    id: int
    code: str
    name: str
    max_employees: int
    max_admins: int
    has_kiosk: bool
    has_advanced_reports: bool
    has_geolocation: bool
    has_multi_location: bool
    price_monthly: Decimal
    price_yearly: Decimal
    is_active: bool

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
            has_advanced_reports=bool(d["has_advanced_reports"]),
            has_geolocation=bool(d["has_geolocation"]),
            has_multi_location=bool(d["has_multi_location"]),
            price_monthly=Decimal(str(d["price_monthly"])),
            price_yearly=Decimal(str(d["price_yearly"])),
            is_active=bool(d["is_active"]),
        )
