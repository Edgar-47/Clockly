"""
app/core/templates.py

Single shared Jinja2Templates instance for the entire application.
All routes import 'templates' from here to ensure globals are available.

If each route creates its own Jinja2Templates(), the globals registered in
main.py (format_timestamp, format_duration) won't be present in those instances.
"""

from fastapi.templating import Jinja2Templates

from app.utils.helpers import format_timestamp

templates = Jinja2Templates(directory="app/templates")


def _format_duration(total_seconds: int | None) -> str:
    """Convert seconds to 'Xh Ym' for display in templates."""
    if total_seconds is None:
        return "—"
    total = int(total_seconds)
    hours, remainder = divmod(total, 3600)
    minutes = remainder // 60
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m"


# Register helpers as Jinja2 globals — available in every template automatically
templates.env.globals["format_timestamp"] = format_timestamp
templates.env.globals["format_duration"] = _format_duration
