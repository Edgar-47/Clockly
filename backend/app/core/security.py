"""
app/core/security.py

Session management helpers for the FastAPI web layer.
Passwords are still handled by app/utils/security.py (PBKDF2-SHA256).

Auth strategy: cookie-based sessions via Starlette's SessionMiddleware.
  - Simple and appropriate for a server-rendered web app.
  - When adding a public REST API or mobile app, extend with JWT in a
    separate app/core/jwt.py module without touching this file.

Session payload keys:
  user_id   (int)   — primary key in the users table
  user_name (str)   — full name for display in the UI
  user_role (str)   — "admin" | "employee"
"""

from app.config import SECRET_KEY, SESSION_MAX_AGE

# SECRET_KEY and SESSION_MAX_AGE are loaded from app.config so .env, local CLI,
# and Railway runtime settings all use the same source of truth.

AUTH_SESSION_KEYS = ("user_id", "user_name", "user_role")
KIOSK_BUSINESS_KEY = "kiosk_business_id"
KIOSK_EMPLOYEE_ID_KEY = "kiosk_employee_id"
KIOSK_EMPLOYEE_KEYS = (
    KIOSK_EMPLOYEE_ID_KEY,
    "kiosk_employee_name",
    "kiosk_employee_role",
)


def build_session_payload(employee) -> dict:
    """
    Build the dict to store in the session cookie from an Employee dataclass.
    Only stores the minimum needed — the full employee object is loaded from DB
    on each protected request via get_current_user().
    """
    display_name = getattr(employee, "full_name", None) or getattr(employee, "name", "")
    return {
        "user_id": employee.id,
        "user_name": display_name,
        "user_role": getattr(employee, "role", "employee"),
    }


def home_path_for_role(role: str | None) -> str:
    """Return the first safe page for an authenticated role."""
    return "/dashboard" if role == "admin" else "/me"


def build_kiosk_session_payload(business_id: str) -> dict:
    """
    Build the dict to store in the session when entering kiosk mode.
    Stores only the business ID to identify the active kiosk business.
    """
    return {KIOSK_BUSINESS_KEY: business_id}


def build_kiosk_employee_payload(employee) -> dict:
    """
    Build the dict to add to the session when an employee logs in within kiosk.
    Kiosk employee state is kept separate from the normal web auth session.
    """
    return {
        KIOSK_EMPLOYEE_ID_KEY: employee.id,
        "kiosk_employee_name": employee.full_name,
        "kiosk_employee_role": employee.role,
    }


def clear_kiosk_employee_context(session: dict) -> None:
    """Remove the employee currently authenticated inside kiosk mode."""
    for key in KIOSK_EMPLOYEE_KEYS:
        session.pop(key, None)

    # Older kiosk sessions reused the global auth keys for employees. Clear
    # those stale keys so a previous employee cannot survive a business switch.
    if session.get("user_role") == "employee":
        for key in AUTH_SESSION_KEYS:
            session.pop(key, None)


def reset_kiosk_context(session: dict) -> str | None:
    """
    Clear the full kiosk context and return the previous business id, if any.

    Admin auth and the admin active_business_id are preserved on purpose:
    kiosk context and back-office context are separate concerns.
    """
    previous_business_id = session.get(KIOSK_BUSINESS_KEY)
    clear_kiosk_employee_context(session)
    session.pop(KIOSK_BUSINESS_KEY, None)
    return previous_business_id
