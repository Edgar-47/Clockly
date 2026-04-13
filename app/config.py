import os
from pathlib import Path


APP_TITLE = "Fichaje Restaurante"

# ── Kiosk mode ────────────────────────────────────────────────────────────────
# Set the environment variable CLOCKLY_KIOSK_MODE=1 (or "true" / "yes") to
# launch the application directly into tablet kiosk mode, bypassing the
# individual login screen.  Admins can still reach the admin panel via the
# "Acceso admin" button inside the kiosk UI.
_kiosk_env: str = os.getenv("CLOCKLY_KIOSK_MODE", "").strip().lower()
KIOSK_MODE: bool = _kiosk_env in ("1", "true", "yes")
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "app" / "data"

_exports_dir = os.getenv("FICHAJE_EXPORTS_DIR")
EXPORTS_DIR = Path(_exports_dir) if _exports_dir else BASE_DIR / "exports"

_database_path = os.getenv("FICHAJE_DATABASE_PATH")
DATABASE_PATH = Path(_database_path) if _database_path else DATA_DIR / "fichaje.sqlite3"

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "Admin123"


def ensure_runtime_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
