"""Utility helpers shared across the application."""

from datetime import datetime


def format_timestamp(timestamp: str, fmt: str = "%d/%m/%Y %H:%M:%S") -> str:
    """Convert a stored ISO-like timestamp to a display string."""
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime(fmt)
    except (ValueError, TypeError):
        return timestamp or ""


def split_timestamp(timestamp: str) -> tuple[str, str]:
    """Return (date_str, time_str) from a stored timestamp."""
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%d/%m/%Y"), dt.strftime("%H:%M:%S")
    except (ValueError, TypeError):
        return timestamp, ""


def today_iso() -> str:
    """Return today's date as YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


def label_for_entry_type(entry_type: str) -> str:
    """Return a human-readable label for an entry_type value."""
    return {"entrada": "Entrada", "salida": "Salida"}.get(entry_type, entry_type.capitalize())
