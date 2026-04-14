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

import os

# Secret key used to sign the session cookie.
# In production, set the SECRET_KEY environment variable to a long random string.
# In development, a hard-coded fallback is used so the app starts without config.
SECRET_KEY: str = os.getenv(
    "CLOCKLY_SECRET_KEY",
    "dev-insecure-key-change-in-production-please-use-a-real-secret",
)

# How long the session cookie is valid (seconds). Default: 8 hours.
SESSION_MAX_AGE: int = int(os.getenv("CLOCKLY_SESSION_MAX_AGE", str(8 * 60 * 60)))


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
