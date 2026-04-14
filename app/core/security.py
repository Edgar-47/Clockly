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


def build_session_payload(employee) -> dict:
    """
    Build the dict to store in the session cookie from an Employee dataclass.
    Only stores the minimum needed — the full employee object is loaded from DB
    on each protected request via get_current_user().
    """
    return {
        "user_id": employee.id,
        "user_name": employee.full_name,
        "user_role": employee.role,
    }


def home_path_for_role(role: str | None) -> str:
    """Return the first safe page for an authenticated role."""
    return "/dashboard" if role == "admin" else "/me"


def build_kiosk_session_payload(business_id: str) -> dict:
    """
    Build the dict to store in the session when entering kiosk mode.
    Stores only the business ID to identify the active kiosk business.
    """
    return {"kiosk_business_id": business_id}


def build_kiosk_employee_payload(employee) -> dict:
    """
    Build the dict to add to the session when an employee logs in within kiosk.
    Reuses the same keys as admin login to minimize session complexity.
    """
    return {
        "user_id": employee.id,
        "user_name": employee.full_name,
        "user_role": employee.role,
    }
