from datetime import date, datetime
from typing import Any


def placeholders(count: int) -> str:
    if count <= 0:
        raise ValueError("Placeholder count must be greater than zero.")
    return ", ".join("%s" for _ in range(count))


def normalize_datetime(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.replace(microsecond=0).isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    return value


def normalize_row(row: Any) -> dict:
    return {key: normalize_datetime(value) for key, value in dict(row).items()}
