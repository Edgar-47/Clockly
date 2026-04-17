from __future__ import annotations

from fastapi import Request

from app.database.employee_repository import EmployeeRepository
from app.models.employee import Employee
from app.models.plan_constants import PlatformRole


class RequiresSuperadminLoginException(Exception):
    """Raised when the internal console is accessed without its own session."""


class RequiresSuperadminException(Exception):
    """Raised when the internal console session is not an owner-level operator."""


def _session_superadmin_id(request: Request) -> int | None:
    raw = request.session.get("superadmin_user_id")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def require_superadmin(request: Request) -> Employee:
    user_id = _session_superadmin_id(request)
    if user_id is None:
        raise RequiresSuperadminLoginException()

    user = EmployeeRepository().get_by_id(user_id)
    if not user or not user.active:
        request.session.pop("superadmin_user_id", None)
        raise RequiresSuperadminLoginException()

    if user.platform_role != PlatformRole.SUPERADMIN.value:
        raise RequiresSuperadminException()

    request.session["superadmin_name"] = user.full_name
    request.session["superadmin_email"] = user.email
    request.session["superadmin_role"] = user.platform_role
    return user

