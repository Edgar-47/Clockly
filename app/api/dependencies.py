"""
app/api/dependencies.py

FastAPI dependency injection helpers shared across all routes.

Auth strategy summary:
  - SessionMiddleware stores a signed cookie (server-side data via itsdangerous).
  - require_user()       → any authenticated user (admin or employee)
  - require_admin()      → admin role only
  - Both raise RequiresLoginException on missing/invalid session; the global
    exception handler in main.py converts that to a 302 redirect to /login.

Future extension: when adding a REST API or mobile app, add a separate
  require_api_user() dependency that validates a Bearer JWT instead of the
  session cookie, without modifying these web-layer dependencies.
"""

from fastapi import Request

from app.core.flow_debug import flow_log
from app.database.employee_repository import EmployeeRepository
from app.models.employee import Employee


# ---------------------------------------------------------------------------
# Custom exception – caught by the exception handler in main.py
# ---------------------------------------------------------------------------

class RequiresLoginException(Exception):
    """Raised when a protected route is accessed without a valid session."""


class RequiresAdminException(Exception):
    """Raised when an admin-only route is accessed by a non-admin user."""


class RequiresKioskException(Exception):
    """Raised when a kiosk route is accessed without kiosk_business_id in session."""


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
    }


# ---------------------------------------------------------------------------
# Kiosk-specific dependencies
# ---------------------------------------------------------------------------

def _get_kiosk_business_id(request: Request) -> str | None:
    """Extract kiosk_business_id from session, or None if not in kiosk mode."""
    return request.session.get("kiosk_business_id")


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
    return business_id


def require_kiosk_employee(request: Request) -> tuple[Employee, str]:
    """
    Dependency: ensure kiosk is active AND an employee is logged in (not admin).
    Returns: (Employee, business_id)
    Raises RequiresKioskException if kiosk not active.
    Raises RequiresLoginException if no employee logged in.
    Raises RequiresAdminException if employee is admin (admin cannot use kiosk).
    """
    business_id = require_kiosk_active(request)
    employee = require_user(request)
    if employee.role == "admin":
        flow_log(
            "kiosk.admin_not_allowed",
            path=request.url.path,
            user_id=employee.id,
        )
        raise RequiresAdminException()
    return employee, business_id
