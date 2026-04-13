"""
Shared test fixtures.

The `db` fixture spins up a fresh SQLite database in a temporary directory for
every test that requests it, runs the full schema initialisation (which includes
seeding the default admin), and patches the connection module so that every
service/repository call inside that test hits the temp DB — never the real one.
"""

import re
import shutil
import tempfile
import uuid
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_path(request):
    """
    Stable replacement for pytest's tmp_path fixture.

    SQLite files are intentionally kept outside the OneDrive-backed workspace
    because OneDrive can briefly lock journal files and make cleanup flaky.
    """
    root = Path(tempfile.gettempdir()) / "clockly_pytest_tmp"
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", request.node.name)[:80]
    path = root / f"{safe_name}_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
        try:
            root.rmdir()
        except OSError:
            pass


@pytest.fixture()
def db(tmp_path, monkeypatch):
    """
    Yield the path to an isolated, fully initialised SQLite test database.

    Patches applied (both the config constant and the connection-module binding):
      - app.config.DATABASE_PATH
      - app.database.connection.DATABASE_PATH
      - app.database.connection.ensure_runtime_directories  (no-op: tmp_path exists)

    All repositories and services read DATABASE_PATH from the connection module
    at call time, so patching it there is sufficient.
    """
    db_path = tmp_path / "test_fichaje.sqlite3"

    # Patch the value that connection.py reads on every get_connection() call.
    monkeypatch.setattr("app.database.connection.DATABASE_PATH", db_path)
    # Also patch ensure_runtime_directories so it does not try to create
    # app/data/ inside OneDrive during test runs.
    monkeypatch.setattr(
        "app.database.connection.ensure_runtime_directories", lambda: None
    )

    # Initialise schema + default admin on the temp DB.
    from app.database.schema import initialize_database
    initialize_database()

    yield db_path
