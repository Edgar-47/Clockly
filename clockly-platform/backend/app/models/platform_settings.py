"""
app/models/platform_settings.py

Global platform configuration stored as key-value pairs.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.database.sql import normalize_datetime


PLATFORM_SETTING_DEFAULTS: dict[str, str] = {
    "platform_name": "Clockly",
    "support_email": "",
    "default_trial_days": "14",
    "max_businesses_per_user": "10",
    "default_plan_code": "free",
    "public_registration_enabled": "true",
    "maintenance_mode": "false",
    "maintenance_message": "",
    "max_session_hours": "24",
    "allow_employee_self_register": "false",
}

PLATFORM_SETTING_DESCRIPTIONS: dict[str, str] = {
    "platform_name": "Nombre de la plataforma mostrado en la UI",
    "support_email": "Email de soporte visible para clientes",
    "default_trial_days": "Días de trial para nuevos negocios",
    "max_businesses_per_user": "Máximo de negocios por usuario",
    "default_plan_code": "Plan asignado al crear un nuevo negocio",
    "public_registration_enabled": "Permitir registro público de nuevos administradores",
    "maintenance_mode": "Activar modo mantenimiento (bloquea acceso de clientes)",
    "maintenance_message": "Mensaje mostrado durante el mantenimiento",
    "max_session_hours": "Horas máximas de una sesión de fichaje sin cerrar",
    "allow_employee_self_register": "Permitir que empleados se registren solos",
}


@dataclass(frozen=True)
class PlatformSetting:
    key: str
    value: str
    description: str | None
    updated_at: str | None

    @property
    def as_bool(self) -> bool:
        return self.value.lower() in ("true", "1", "yes", "on")

    @property
    def as_int(self) -> int:
        try:
            return int(self.value)
        except (ValueError, TypeError):
            return 0

    @classmethod
    def from_row(cls, row) -> "PlatformSetting":
        return cls(
            key=row["key"],
            value=row["value"] or "",
            description=row.get("description"),
            updated_at=normalize_datetime(row["updated_at"]) if row.get("updated_at") else None,
        )
