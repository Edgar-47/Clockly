"""
Shared test fixtures.

The `db` fixture spins up a fresh SQLite database in a temporary directory for
every test that requests it, runs the full schema initialisation (which includes
seeding the default admin), and patches the connection module so that every
service/repository call inside that test hits the temp DB — never the real one.
"""

import pytest


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
