import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency may not be installed yet
    load_dotenv = None

_RAW_CLOCKLY_ENV = os.getenv("CLOCKLY_ENV", "development").strip().lower()

if load_dotenv is not None and _RAW_CLOCKLY_ENV != "production":
    load_dotenv()


APP_TITLE = "Fichaje Restaurante"

# ── Kiosk mode ────────────────────────────────────────────────────────────────
# Set the environment variable CLOCKLY_KIOSK_MODE=1 (or "true" / "yes") to
# launch the application directly into tablet kiosk mode, bypassing the
# individual login screen.  Admins can still reach the admin panel via the
# "Acceso admin" button inside the kiosk UI.
_TRUTHY = {"1", "true", "yes", "on"}


def _env_bool(name: str, *, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in _TRUTHY


KIOSK_MODE = _env_bool("CLOCKLY_KIOSK_MODE")
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
WEB_DIR = PROJECT_ROOT / "web"
WEB_TEMPLATES_DIR = WEB_DIR / "templates"
WEB_STATIC_DIR = WEB_DIR / "static"
UPLOADS_DIR = PROJECT_ROOT / "uploads"
BASE_DIR = PROJECT_ROOT
DATA_DIR = BACKEND_DIR / "app" / "data"

_exports_dir = os.getenv("FICHAJE_EXPORTS_DIR")
EXPORTS_DIR = Path(_exports_dir) if _exports_dir else PROJECT_ROOT / "exports"

CLOCKLY_ENV = os.getenv("CLOCKLY_ENV", "development").strip().lower() or "development"
IS_PRODUCTION = CLOCKLY_ENV == "production"

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

DEFAULT_ADMIN_USERNAME = os.getenv("CLOCKLY_DEFAULT_ADMIN_USERNAME", "admin").strip()
DEFAULT_ADMIN_PASSWORD = os.getenv(
    "CLOCKLY_DEFAULT_ADMIN_PASSWORD",
    "" if IS_PRODUCTION else "Admin123",
)

SECRET_KEY = os.getenv(
    "CLOCKLY_SECRET_KEY",
    "" if IS_PRODUCTION else "dev-insecure-key-change-in-production-please-use-a-real-secret",
)
SESSION_MAX_AGE = int(os.getenv("CLOCKLY_SESSION_MAX_AGE", str(8 * 60 * 60)))
SECURE_COOKIES = _env_bool("CLOCKLY_SECURE_COOKIES", default=IS_PRODUCTION)
DOCS_ENABLED = _env_bool("CLOCKLY_DOCS_ENABLED", default=not IS_PRODUCTION)
PORT = int(os.getenv("PORT", "8000"))

# Google OAuth owner/admin login.
# These are optional in development so the legacy password login and tests keep
# working. In production, set them to enable "Continue with Google".
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "").strip()
GOOGLE_AUTH_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)


def ensure_runtime_directories() -> None:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def validate_runtime_config() -> None:
    database_url = os.getenv("DATABASE_URL", DATABASE_URL).strip()
    admin_username = os.getenv(
        "CLOCKLY_DEFAULT_ADMIN_USERNAME",
        DEFAULT_ADMIN_USERNAME,
    ).strip()
    clockly_env = os.getenv("CLOCKLY_ENV", CLOCKLY_ENV).strip().lower()
    admin_password = os.getenv(
        "CLOCKLY_DEFAULT_ADMIN_PASSWORD",
        "" if clockly_env == "production" else DEFAULT_ADMIN_PASSWORD,
    )
    secret_key = os.getenv(
        "CLOCKLY_SECRET_KEY",
        "" if clockly_env == "production" else SECRET_KEY,
    )

    missing: list[str] = []
    if not database_url:
        missing.append("DATABASE_URL")
    if not admin_username:
        missing.append("CLOCKLY_DEFAULT_ADMIN_USERNAME")
    if not admin_password:
        missing.append("CLOCKLY_DEFAULT_ADMIN_PASSWORD")
    if not secret_key:
        missing.append("CLOCKLY_SECRET_KEY")

    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(sorted(missing))
        )

    if clockly_env == "production" and secret_key.startswith("dev-insecure-key"):
        raise RuntimeError("CLOCKLY_SECRET_KEY must be changed in production.")
    if clockly_env == "production" and admin_password == "Admin123":
        raise RuntimeError("CLOCKLY_DEFAULT_ADMIN_PASSWORD must be changed in production.")
