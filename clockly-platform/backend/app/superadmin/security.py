from __future__ import annotations

from fastapi import Request

from app.core.security import AUTH_SESSION_KEYS


SUPERADMIN_SESSION_KEYS = (
    "superadmin_user_id",
    "superadmin_name",
    "superadmin_email",
    "superadmin_role",
)


def build_superadmin_session_payload(user) -> dict:
    display_name = getattr(user, "full_name", None) or getattr(user, "name", "")
    return {
        "superadmin_user_id": user.id,
        "superadmin_name": display_name,
        "superadmin_email": getattr(user, "email", None),
        "superadmin_role": getattr(user, "platform_role", None),
    }


def clear_superadmin_context(session: dict) -> None:
    for key in SUPERADMIN_SESSION_KEYS:
        session.pop(key, None)


def clear_normal_auth_context(session: dict) -> None:
    for key in AUTH_SESSION_KEYS:
        session.pop(key, None)


def is_impersonating_tenant(request: Request) -> bool:
    return bool(
        request.session.get("impersonation_business_id")
        and request.session.get("impersonation_superadmin_id")
        and request.session.get("superadmin_user_id")
        == request.session.get("impersonation_superadmin_id")
    )


def superadmin_template_context(request: Request) -> dict:
    return {
        "flash_messages": _pop_superadmin_flash_messages(request),
        "superadmin_user_id": request.session.get("superadmin_user_id"),
        "superadmin_name": request.session.get("superadmin_name"),
        "superadmin_email": request.session.get("superadmin_email"),
        "superadmin_role": request.session.get("superadmin_role"),
        "impersonation_business_id": request.session.get("impersonation_business_id"),
        "impersonation_business_name": request.session.get("impersonation_business_name"),
    }


def superadmin_flash(request: Request, message: str, category: str = "info") -> None:
    messages = request.session.setdefault("superadmin_flash_messages", [])
    messages.append({"message": message, "category": category})


def _pop_superadmin_flash_messages(request: Request) -> list[dict]:
    return request.session.pop("superadmin_flash_messages", [])

