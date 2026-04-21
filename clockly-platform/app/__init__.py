"""Compatibility package for ClockLy Platform.

The canonical backend package lives in ``backend/app``. Keeping this lightweight
package at the repository root preserves imports such as ``app.main`` for local
scripts, tests and deploy Procfiles while Python loads submodules from the
backend location first.
"""

from pathlib import Path

_ROOT_APP_DIR = Path(__file__).resolve().parent
_BACKEND_APP_DIR = _ROOT_APP_DIR.parent / "backend" / "app"

__path__ = [str(_BACKEND_APP_DIR), str(_ROOT_APP_DIR)]
