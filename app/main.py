"""
app/main.py

FastAPI application entry point for Clockly web.

Architecture overview:
  app/
  ├── main.py              ← you are here (app factory + wiring)
  ├── core/
  │   └── security.py      ← session secret, build_session_payload()
  ├── api/
  │   ├── dependencies.py  ← auth guards, flash messages, template_context()
  │   └── routes/          ← one module per resource (auth, employees, clock, sessions)
  ├── services/            ← business logic (unchanged from desktop version)
  ├── repositories/        ← data access (unchanged from desktop version, lives in database/)
  ├── models/              ← domain dataclasses (unchanged)
  ├── templates/           ← Jinja2 HTML templates
  └── static/              ← CSS, JS, images

Auth strategy: cookie-based sessions (SessionMiddleware).
  Extend with JWT (app/core/jwt.py) when adding a public REST API.

Database: SQLite via app/database/connection.py.
  Swap to PostgreSQL by updating DATABASE_PATH and connection.py to use
  SQLAlchemy or asyncpg — no other layer needs to change.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.flow_debug import configure_flow_logging, flow_log
from app.core.security import SECRET_KEY, SESSION_MAX_AGE, home_path_for_role
from app.core.templates import templates  # noqa: F401 — imported to register Jinja2 globals
from app.api.dependencies import RequiresAdminException, RequiresLoginException
from app.api.routes import auth, clock, dashboard, employees, me, sessions
from app.database.schema import initialize_database


# ---------------------------------------------------------------------------
# Lifespan: runs once at startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite schema and run all pending migrations on startup.
    # Safe to call every time — all migrations are idempotent.
    configure_flow_logging()
    initialize_database()
    yield
    # Shutdown: nothing to clean up for SQLite.


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Clockly",
    description="Employee time-tracking web application",
    version="2.0.0",
    # Disable auto-generated docs in production; enable for development.
    # Set CLOCKLY_DOCS_ENABLED=1 to turn them back on.
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=SESSION_MAX_AGE,
    same_site="lax",        # CSRF protection for same-origin forms
    https_only=False,       # Set to True in production (HTTPS)
)


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory="app/static"), name="static")


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(RequiresLoginException)
async def requires_login_handler(request: Request, exc: RequiresLoginException):
    """Redirect to login when a protected route is accessed without a session."""
    return RedirectResponse("/login", status_code=302)


@app.exception_handler(RequiresAdminException)
async def requires_admin_handler(request: Request, exc: RequiresAdminException):
    """Redirect non-admin users to their own flow, avoiding dashboard loops."""
    target = (
        home_path_for_role(request.session.get("user_role"))
        if request.session.get("user_id")
        else "/login"
    )
    flow_log(
        "permission.redirect",
        path=request.url.path,
        user_id=request.session.get("user_id"),
        role=request.session.get("user_role"),
        target=target,
    )
    return RedirectResponse(target, status_code=302)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(employees.router)
app.include_router(clock.router)
app.include_router(sessions.router)
app.include_router(me.router)


# ---------------------------------------------------------------------------
# Root redirect
# ---------------------------------------------------------------------------

@app.get("/")
async def root(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=302)
    return RedirectResponse(
        home_path_for_role(request.session.get("user_role")),
        status_code=302,
    )
