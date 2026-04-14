"""Small opt-in logs for tracing web/session/filter flows during migration."""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping


_TRUTHY = {"1", "true", "yes", "on", "debug"}
logger = logging.getLogger("clockly.flow")


def flow_debug_enabled() -> bool:
    return os.getenv("CLOCKLY_DEBUG_FLOW", "").strip().lower() in _TRUTHY


def configure_flow_logging() -> None:
    if not flow_debug_enabled():
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logger.setLevel(logging.INFO)


def flow_log(event: str, **fields: object) -> None:
    """Log temporary migration diagnostics when CLOCKLY_DEBUG_FLOW=1."""
    if not flow_debug_enabled():
        return
    clean_fields = " ".join(f"{key}={value!r}" for key, value in fields.items())
    logger.info("%s %s", event, clean_fields)


def form_keys(form_data: Mapping[str, object]) -> list[str]:
    return sorted(str(key) for key in form_data.keys())


def mask_identifier(value: str) -> str:
    clean_value = (value or "").strip()
    if len(clean_value) <= 2:
        return "*" * len(clean_value)
    return f"{clean_value[0]}***{clean_value[-1]}"
