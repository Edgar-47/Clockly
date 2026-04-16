from __future__ import annotations

from dataclasses import dataclass

_CONTRACT_TYPES = {
    "indefinido": "Indefinido",
    "temporal": "Temporal",
    "practicas": "Prácticas",
    "autonomo": "Autónomo",
    "formacion": "Formación",
    "otro": "Otro",
}


@dataclass(frozen=True)
class EmployeeProfile:
    user_id: int
    hire_date: str | None          # ISO date "YYYY-MM-DD"
    contract_type: str | None      # key from _CONTRACT_TYPES
    department: str | None
    job_title: str | None
    phone: str | None
    personal_email: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    social_security_number: str | None
    notes: str | None
    created_at: str
    updated_at: str

    @staticmethod
    def from_row(row: dict) -> EmployeeProfile:
        hire_raw = row.get("hire_date")
        return EmployeeProfile(
            user_id=int(row["user_id"]),
            hire_date=str(hire_raw) if hire_raw else None,
            contract_type=row.get("contract_type"),
            department=row.get("department"),
            job_title=row.get("job_title"),
            phone=row.get("phone"),
            personal_email=row.get("personal_email"),
            emergency_contact_name=row.get("emergency_contact_name"),
            emergency_contact_phone=row.get("emergency_contact_phone"),
            social_security_number=row.get("social_security_number"),
            notes=row.get("notes"),
            created_at=str(row.get("created_at") or ""),
            updated_at=str(row.get("updated_at") or ""),
        )

    @staticmethod
    def empty(user_id: int) -> EmployeeProfile:
        return EmployeeProfile(
            user_id=user_id,
            hire_date=None,
            contract_type=None,
            department=None,
            job_title=None,
            phone=None,
            personal_email=None,
            emergency_contact_name=None,
            emergency_contact_phone=None,
            social_security_number=None,
            notes=None,
            created_at="",
            updated_at="",
        )

    @property
    def contract_type_label(self) -> str:
        return _CONTRACT_TYPES.get(self.contract_type or "", self.contract_type or "—")

    @property
    def hire_date_display(self) -> str:
        if not self.hire_date:
            return "—"
        try:
            from datetime import date
            d = date.fromisoformat(str(self.hire_date)[:10])
            return d.strftime("%d/%m/%Y")
        except (ValueError, TypeError):
            return str(self.hire_date)

    @property
    def has_emergency_contact(self) -> bool:
        return bool(self.emergency_contact_name or self.emergency_contact_phone)


CONTRACT_TYPE_CHOICES = list(_CONTRACT_TYPES.items())
