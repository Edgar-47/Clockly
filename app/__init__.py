"""Compatibility package for the incremental ClockLy backend split.

The canonical backend package now lives in ``backend/app``. Keeping this
lightweight package at the repository root preserves imports such as
``app.main`` for existing scripts, tests, and Railway's Procfile while Python
loads submodules from the new backend location first.
"""

from pathlib import Path

_ROOT_APP_DIR = Path(__file__).resolve().parent
_BACKEND_APP_DIR = _ROOT_APP_DIR.parent / "backend" / "app"

__path__ = [str(_BACKEND_APP_DIR), str(_ROOT_APP_DIR)]
