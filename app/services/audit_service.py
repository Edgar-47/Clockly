"""
app/services/audit_service.py

Helper to write structured audit log entries for critical platform actions.
"""
from __future__ import annotations

from fastapi import Request

from app.database.audit_log_repository import AuditLogRepository


def audit_log(
    request: Request,
    action: str,
    *,
    resource_type: str | None = None,
    resource_id: str | int | None = None,
    business_id: str | None = None,
    old_value: dict | None = None,
    new_value: dict | None = None,
    metadata: dict | None = None,
) -> None:
    """Write an audit log entry from the current request context."""
    actor_user_id: int | None = None
    actor_email: str | None = None

    raw_id = request.session.get("superadmin_user_id") or request.session.get("user_id")
    if raw_id is not None:
        try:
            actor_user_id = int(raw_id)
        except (TypeError, ValueError):
            pass

    actor_email = (
        request.session.get("superadmin_email")
        or request.session.get("superadmin_name")
        or request.session.get("user_email")
        or request.session.get("user_name")
    )

    ip_address = _extract_ip(request)

    AuditLogRepository().create(
        actor_user_id=actor_user_id,
        actor_email=actor_email,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        business_id=business_id,
        old_value=old_value,
        new_value=new_value,
        metadata=metadata,
        ip_address=ip_address,
    )


def _extract_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None
