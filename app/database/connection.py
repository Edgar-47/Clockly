import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app.config import DATABASE_PATH, ensure_runtime_directories


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    ensure_runtime_directories()
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
