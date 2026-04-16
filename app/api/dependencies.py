"""
app/api/dependencies.py

FastAPI dependency injection helpers shared across all routes.

Auth strategy summary:
  - SessionMiddleware stores a signed cookie (server-side data via itsdangerous).
  - require_user()            → any authenticated user (admin or employee)
  - require_admin()           → admin role only
  - require_active_business() → admin + an active business must be selected
  - Both raise exception types handled by the global exception handler in main.py.

Session keys (admin):
  user_id            (int)  — canonical user PK
  user_name          (str)  — display name
  user_role          (str)  — "admin" | "employee"
  active_business_id (str)  — currently selected business UUID
"""

from fastapi import Request

from app.core.security import (
    KIOSK_BUSINESS_KEY,
    KIOSK_EMPLOYEE_ID_KEY,
    clear_kiosk_employee_context,
    reset_kiosk_context,
)
from app.core.flow_debug import flow_log
from app.database.employee_repository import EmployeeRepository
from app.models.employee import Employee


# ---------------------------------------------------------------------------
# Custom exceptions – caught by the exception handler in main.py
# ---------------------------------------------------------------------------

class RequiresLoginException(Exception):
    """Raised when a protected route is accessed without a valid session."""


class RequiresAdminException(Exception):
    """Raised when an admin-only route is accessed by a non-admin user."""


class RequiresKioskException(Exception):
    """Raised when a kiosk route is accessed without kiosk_business_id in session."""


class RequiresOnboardingException(Exception):
    """Raised when an admin has no businesses yet and must complete onboarding."""


# ---------------------------------------------------------------------------
# Core session helpers
# ---------------------------------------------------------------------------

def _get_user_id_from_session(request: Request) -> int | None:
    """Extract user_id from the session cookie, or None if absent."""
    raw = request.session.get("user_id")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Reusable dependencies
# ---------------------------------------------------------------------------

def require_user(request: Request) -> Employee:
    """
    Dependency: return the current authenticated Employee.
    Raises RequiresLoginException → redirected to /login by the exception handler.
    """
    user_id = _get_user_id_from_session(request)
    flow_log(
        "session.read",
        path=request.url.path,
        user_id=user_id,
        role=request.session.get("user_role"),
    )
    if not user_id:
        flow_log("session.missing", path=request.url.path)
        raise RequiresLoginException()

    employee = EmployeeRepository().get_by_id(user_id)
    if not employee or not employee.active:
        flow_log("session.invalid_user", path=request.url.path, user_id=user_id)
        request.session.clear()
        raise RequiresLoginException()

    flow_log(
        "session.user_loaded",
        path=request.url.path,
        user_id=employee.id,
        role=employee.role,
    )
    return employee


def require_admin(request: Request) -> Employee:
    """
    Dependency: return the current Employee only if they have the 'admin' role.
    Raises RequiresLoginException if not logged in.
    Raises RequiresAdminException if logged in but not admin.
    """
    employee = require_user(request)
    if employee.role != "admin":
        flow_log(
            "permission.denied_admin_required",
            path=request.url.path,
            user_id=employee.id,
            role=employee.role,
        )
        raise RequiresAdminException()
    return employee


# ---------------------------------------------------------------------------
# Template context helper
# ---------------------------------------------------------------------------

def flash(request: Request, message: str, category: str = "info") -> None:
    """
    Store a flash message in the session to be displayed on the next page load.
    Categories: "success" | "error" | "warning" | "info"
    """
    messages = request.session.setdefault("flash_messages", [])
    messages.append({"message": message, "category": category})


def get_flash_messages(request: Request) -> list[dict]:
    """Pop and return all pending flash messages."""
    messages = request.session.pop("flash_messages", [])
    return messages


def template_context(request: Request) -> dict:
    """
    Base context dict to pass to every template.
    NOTE: 'request' is NOT included here — Starlette 1.0+ injects it automatically
    when you call templates.TemplateResponse(request, name, context).
    """
    return {
        "flash_messages": get_flash_messages(request),
        "current_user_id": request.session.get("user_id"),
        "current_user_name": request.session.get("user_name"),
        "current_user_role": request.session.get("user_role"),
        # Active business is surfaced to every template for the sidebar/header
        "active_business_id": request.session.get("active_business_id"),
        "active_business_role": request.session.get("active_business_role"),
        "kiosk_business_id": request.session.get(KIOSK_BUSINESS_KEY),
        "kiosk_employee_id": request.session.get(KIOSK_EMPLOYEE_ID_KEY),
        "kiosk_employee_name": request.session.get("kiosk_employee_name"),
        "kiosk_employee_role": request.session.get("kiosk_employee_role"),
    }


# ---------------------------------------------------------------------------
# Business context helpers (admin panel)
# ---------------------------------------------------------------------------

def get_active_business_id(request: Request) -> str | None:
    """Return the admin's currently selected business ID from session, or None."""
    return request.session.get("active_business_id") or None


def set_active_business_id(request: Request, business_id: str) -> None:
    """Persist the admin's active business selection in the session."""
    request.session["active_business_id"] = business_id


def set_active_business_role(request: Request, role: str | None) -> None:
    if role:
        request.session["active_business_role"] = role
    else:
        request.session.pop("active_business_role", None)


def require_active_business(request: Request) -> str:
    """
    Dependency: ensure an admin is logged in AND has selected a business.

    On first login the `active_business_id` key may be absent even though the
    admin already owns businesses — BusinessService.choose_default_business()
    is called lazily here so every route that uses this dependency stays clean.

    Raises RequiresLoginException   → redirect to /login
    Raises RequiresAdminException   → redirect to role home
    Raises RequiresOnboardingException → redirect to /businesses/new
    Returns business_id (str)
    """
    # Must be an authenticated admin first
    employee = require_admin(request)

    business_id = get_active_business_id(request)
    if business_id:
        from app.database.business_repository import BusinessRepository
        from app.database.business_user_repository import BusinessUserRepository
        if BusinessRepository().user_has_access(
            business_id=business_id,
            user_id=employee.id,
        ):
            role = BusinessUserRepository().get_active_role(
                business_id=business_id,
                user_id=employee.id,
            )
            set_active_business_role(request, role)
            return business_id
        request.session.pop("active_business_id", None)
        request.session.pop("active_business_role", None)
        flow_log(
            "business.session_invalid",
            user_id=employee.id,
            business_id=business_id,
        )

    # Lazy default: pick the most recently accessed business
    from app.services.business_service import BusinessService
    svc = BusinessService()
    if svc.requires_onboarding(employee.id):
        legacy_business = svc.ensure_legacy_business_for_user(employee.id)
        if legacy_business is not None:
            set_active_business_id(request, legacy_business.id)
            set_active_business_role(request, "owner")
            flow_log(
                "business.legacy_default_selected",
                user_id=employee.id,
                business_id=legacy_business.id,
            )
            return legacy_business.id
        flow_log("business.onboarding_required", user_id=employee.id)
        raise RequiresOnboardingException()

    business = svc.choose_default_business(employee.id)
    if business is None:
        raise RequiresOnboardingException()

    set_active_business_id(request, business.id)
    from app.database.business_user_repository import BusinessUserRepository
    set_active_business_role(
        request,
        BusinessUserRepository().get_active_role(
            business_id=business.id,
            user_id=employee.id,
        ),
    )
    flow_log(
        "business.default_selected",
        user_id=employee.id,
        business_id=business.id,
        business_name=business.business_name,
    )
    return business.id


def require_business_permission(permission: str):
    def _dependency(request: Request) -> tuple[Employee, str]:
        employee = require_admin(request)
        business_id = require_active_business(request)
        from app.services.authorization_service import AuthorizationError, AuthorizationService
        try:
            principal = AuthorizationService().require_permission(
                user_id=employee.id,
                business_id=business_id,
                permission=permission,
            )
            set_active_business_role(request, principal.role)
        except AuthorizationError:
            raise RequiresAdminException()
        return employee, business_id

    return _dependency


# ---------------------------------------------------------------------------
# Kiosk-specific dependencies
# ---------------------------------------------------------------------------

def _get_kiosk_business_id(request: Request) -> str | None:
    """Extract kiosk_business_id from session, or None if not in kiosk mode."""
    return request.session.get(KIOSK_BUSINESS_KEY)


def require_kiosk_active(request: Request) -> str:
    """
    Dependency: ensure kiosk mode is active (business_id in session).
    Returns: business_id (str)
    Raises RequiresKioskException → redirected to /kiosk/enter by exception handler.
    """
    business_id = _get_kiosk_business_id(request)
    flow_log("kiosk.check_active", path=request.url.path, has_business_id=bool(business_id))
    if not business_id:
        raise RequiresKioskException()
    from app.database.business_repository import BusinessRepository
    business = BusinessRepository().get_by_id(business_id)
    if business is None or not business.is_active:
        reset_kiosk_context(request.session)
        flow_log("kiosk.invalid_business", path=request.url.path, business_id=business_id)
        raise RequiresKioskException()
    return business_id


def require_kiosk_employee(request: Request) -> tuple[Employee, str]:
    """
    Dependency: ensure kiosk is active AND an employee is logged in (not admin).
    Returns: (Employee, business_id)
    Raises RequiresKioskException if kiosk not active.
    Raises RequiresLoginException if no kiosk employee is logged in.
    """
    business_id = require_kiosk_active(request)
    employee_id = _get_kiosk_employee_id(request)
    if employee_id is None:
        flow_log("kiosk.employee_missing", path=request.url.path, business_id=business_id)
        raise RequiresLoginException()

    employee = EmployeeRepository(business_id=business_id).get_by_id(employee_id)
    if not employee or not employee.active:
        clear_kiosk_employee_context(request.session)
        flow_log(
            "kiosk.employee_invalid",
            path=request.url.path,
            employee_id=employee_id,
            business_id=business_id,
        )
        raise RequiresLoginException()

    if employee.role != "employee":
        clear_kiosk_employee_context(request.session)
        flow_log(
            "kiosk.non_employee_not_allowed",
            path=request.url.path,
            user_id=employee.id,
            role=employee.role,
        )
        raise RequiresLoginException()
    return employee, business_id


def _get_kiosk_employee_id(request: Request) -> int | None:
    """Return the kiosk-scoped employee id, including legacy cookie fallback."""
    raw = request.session.get(KIOSK_EMPLOYEE_ID_KEY)
    if raw is None and request.session.get("user_role") == "employee":
        raw = request.session.get("user_id")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        clear_kiosk_employee_context(request.session)
        return None
