import os
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg import IntegrityError as DatabaseIntegrityError
from psycopg.rows import dict_row

from app.config import DATABASE_URL


class DatabaseConfigurationError(RuntimeError):
    """Raised when PostgreSQL connection settings are missing or invalid."""


_CONNECT_TIMEOUT = int(os.getenv("CLOCKLY_DB_CONNECT_TIMEOUT", "15"))


def normalize_database_url(url: str) -> str:
    clean_url = (url or "").strip()
    if clean_url.startswith("postgres://"):
        return "postgresql://" + clean_url.removeprefix("postgres://")
    return clean_url


def get_database_url() -> str:
    raw_url = os.getenv("DATABASE_URL", DATABASE_URL)
    database_url = normalize_database_url(raw_url)
    if not database_url:
        raise DatabaseConfigurationError(
            "DATABASE_URL is required. Set it to your PostgreSQL connection URL."
        )
    return database_url


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    try:
        connection = psycopg.connect(
            get_database_url(),
            connect_timeout=_CONNECT_TIMEOUT,
            row_factory=dict_row,
        )
    except psycopg.Error as exc:
        raise DatabaseConfigurationError(
            "Could not connect to PostgreSQL using DATABASE_URL."
        ) from exc
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
