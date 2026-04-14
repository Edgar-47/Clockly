"""
Shared test fixtures.

The `db` fixture resets a dedicated PostgreSQL test database for
every test that requests it, runs the full schema initialization (which includes
seeding the default admin), and patches the connection module so that every
service/repository call inside that test hits the temp DB — never the real one.
"""

import os
import re
import shutil
import tempfile
import uuid
from pathlib import Path
from urllib.parse import urlparse

import pytest

from app.database.connection import normalize_database_url


@pytest.fixture()
def tmp_path(request):
    """
    Stable replacement for pytest's tmp_path fixture.

    Export files are kept outside the OneDrive-backed workspace to avoid flaky
    cleanup on Windows.
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
def db(monkeypatch):
    """
    Reset a dedicated PostgreSQL test database and run bootstrap migrations.

    TEST_DATABASE_URL must point at a database whose name contains "test".
    The fixture drops and recreates the public schema for isolation.
    """
    test_database_url = os.getenv("TEST_DATABASE_URL", "").strip()
    if not test_database_url:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests.")

    database_name = urlparse(normalize_database_url(test_database_url)).path.rsplit(
        "/",
        1,
    )[-1]
    if "test" not in database_name.lower():
        pytest.fail("Refusing to reset a database whose name does not contain 'test'.")

    monkeypatch.setenv("DATABASE_URL", test_database_url)

    from app.database.connection import get_connection

    with get_connection() as connection:
        _reset_public_schema(connection)

    from app.database.schema import initialize_database

    initialize_database()

    yield test_database_url

    with get_connection() as connection:
        _reset_public_schema(connection)


def _reset_public_schema(connection) -> None:
    row = connection.execute("SELECT current_database() AS database_name").fetchone()
    database_name = row["database_name"]
    if "test" not in database_name.lower():
        raise RuntimeError(
            "Refusing to reset a database whose name does not contain 'test'."
        )
    connection.execute("DROP SCHEMA IF EXISTS public CASCADE")
    connection.execute("CREATE SCHEMA public")
