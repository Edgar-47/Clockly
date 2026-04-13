import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app.config import DATABASE_PATH, ensure_runtime_directories

# ── OneDrive / network-drive notice ──────────────────────────────────────────
# SQLite is unreliable on paths synced by OneDrive, Dropbox, or any network
# drive because those services hold advisory locks on the file during sync,
# which causes "disk I/O error" or "database is locked" failures.
#
# Recommended solution: store the database outside the synced folder.
# Set the environment variable FICHAJE_DATABASE_PATH to a local path, e.g.
#   $Env:FICHAJE_DATABASE_PATH = "C:\Users\<user>\AppData\Local\Clockly\fichaje.sqlite3"
# and Clockly will use that location on every startup.
#
# WAL journal mode + a generous busy_timeout reduce (but do not eliminate)
# lock contention when the path cannot be moved.
# ─────────────────────────────────────────────────────────────────────────────

_CONNECT_TIMEOUT = 15        # seconds SQLite waits for the file to be openable
_BUSY_TIMEOUT_MS = 8_000     # ms SQLite retries on SQLITE_BUSY before raising
_JOURNAL_MODE = os.getenv("FICHAJE_SQLITE_JOURNAL_MODE", "WAL").strip().upper()
if _JOURNAL_MODE not in {"WAL", "DELETE", "TRUNCATE", "PERSIST", "MEMORY", "OFF"}:
    _JOURNAL_MODE = "WAL"


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    ensure_runtime_directories()
    connection = sqlite3.connect(DATABASE_PATH, timeout=_CONNECT_TIMEOUT)
    connection.row_factory = sqlite3.Row
    # WAL mode: readers never block writers and writers rarely block readers.
    # Also reduces the window during which OneDrive can steal the lock.
    connection.execute(f"PRAGMA journal_mode = {_JOURNAL_MODE}")
    connection.execute("PRAGMA synchronous = NORMAL")   # safe with WAL
    connection.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
