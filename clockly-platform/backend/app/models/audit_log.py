"""
app/models/audit_log.py

Audit log entry for critical platform actions.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from app.database.sql import normalize_datetime


@dataclass(frozen=True)
class AuditLog:
    id: int
    actor_user_id: int | None
    actor_email: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    business_id: str | None
    old_value: str | None   # JSON string
    new_value: str | None   # JSON string
    metadata: str | None    # JSON string
    ip_address: str | None
    created_at: str
    # Joined display fields
    actor_name: str | None = None
    business_name: str | None = None

    @property
    def old_value_dict(self) -> dict:
        if not self.old_value:
            return {}
        try:
            return json.loads(self.old_value)
        except (json.JSONDecodeError, TypeError):
            return {}

    @property
    def new_value_dict(self) -> dict:
        if not self.new_value:
            return {}
        try:
            return json.loads(self.new_value)
        except (json.JSONDecodeError, TypeError):
            return {}

    @property
    def metadata_dict(self) -> dict:
        if not self.metadata:
            return {}
        try:
            return json.loads(self.metadata)
        except (json.JSONDecodeError, TypeError):
            return {}

    @property
    def action_label(self) -> str:
        return _ACTION_LABELS.get(self.action, self.action)

    @classmethod
    def from_row(cls, row) -> "AuditLog":
        keys = set(row.keys())
        return cls(
            id=row["id"],
            actor_user_id=row.get("actor_user_id"),
            actor_email=row.get("actor_email"),
            action=row["action"],
            resource_type=row.get("resource_type"),
            resource_id=str(row["resource_id"]) if row.get("resource_id") is not None else None,
            business_id=row.get("business_id"),
            old_value=row.get("old_value"),
            new_value=row.get("new_value"),
            metadata=row.get("metadata"),
            ip_address=row.get("ip_address"),
            created_at=normalize_datetime(row["created_at"]) if "created_at" in keys else "",
            actor_name=row.get("actor_name"),
            business_name=row.get("business_name"),
        )


_ACTION_LABELS: dict[str, str] = {
    "superadmin.login": "Inicio de sesión superadmin",
    "superadmin.business.suspend": "Negocio suspendido",
    "superadmin.business.unsuspend": "Negocio reactivado",
    "superadmin.business.archive": "Negocio archivado",
    "superadmin.business.change_plan": "Plan cambiado",
    "superadmin.business.impersonate": "Impersonación iniciada",
    "superadmin.business.user_role": "Rol de usuario de negocio cambiado",
    "superadmin.subscription.cancel": "Suscripción cancelada",
    "superadmin.subscription.reactivate": "Suscripción reactivada",
    "superadmin.subscription.pause": "Suscripción pausada",
    "superadmin.subscription.change_status": "Estado de suscripción cambiado",
    "superadmin.user.set_role": "Rol de plataforma cambiado",
    "superadmin.user.create": "Usuario interno creado",
    "superadmin.user.activate": "Usuario activado",
    "superadmin.user.deactivate": "Usuario desactivado",
    "superadmin.settings.update": "Configuración global actualizada",
}
