import os
from pathlib import Path


APP_TITLE = "Fichaje Restaurante"
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
