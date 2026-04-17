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

Database: PostgreSQL via app/database/connection.py.
  Railway provides DATABASE_URL; local development can load it from .env.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import DOCS_ENABLED, SECURE_COOKIES, validate_runtime_config
from app.core.flow_debug import configure_flow_logging, flow_log
from app.core.security import SECRET_KEY, SESSION_MAX_AGE, home_path_for_role
from app.core.templates import templates  # noqa: F401 — imported to register Jinja2 globals
from app.api.dependencies import (
    RequiresAdminException,
    RequiresLoginException,
    RequiresKioskException,
    RequiresOnboardingException,
    RequiresPlatformAdminException,
)
from app.api.routes import auth, businesses, clock, dashboard, employees, expenses, kiosk, me, sessions
from app.api.routes import analytics, schedules
from app.api.routes import superadmin
from app.database.schema import initialize_database
from app.superadmin.dependencies import (
    RequiresSuperadminException,
    RequiresSuperadminLoginException,
)


# ---------------------------------------------------------------------------
# Lifespan: runs once at startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_runtime_config()
    # Initialize PostgreSQL schema and run all pending migrations on startup.
    # Safe to call every time — all migrations are idempotent.
    configure_flow_logging()
    initialize_database()
    yield


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Clockly",
    description="Employee time-tracking web application",
    version="2.0.0",
    # Disable auto-generated docs in production; enable for development.
    # Set CLOCKLY_DOCS_ENABLED=1 to turn them back on.
    docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url="/redoc" if DOCS_ENABLED else None,
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
    https_only=SECURE_COOKIES,
)


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Serve uploaded expense ticket images.
# The directory is created on first upload; ensure it exists at startup.
import os as _os
_os.makedirs("uploads/tickets", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(RequiresLoginException)
async def requires_login_handler(request: Request, exc: RequiresLoginException):
    """Redirect to login when a protected route is accessed without a session.
    Special case: kiosk routes redirect to /kiosk/enter instead of /login."""
    if request.url.path.startswith("/kiosk"):
        target = (
            "/kiosk/login"
            if request.session.get("kiosk_business_id")
            else "/kiosk/enter"
        )
        return RedirectResponse(target, status_code=302)
    return RedirectResponse("/login", status_code=302)


@app.exception_handler(RequiresAdminException)
async def requires_admin_handler(request: Request, exc: RequiresAdminException):
    """Redirect non-admin users to their own flow, avoiding dashboard loops."""
    if request.url.path.startswith("/kiosk"):
        target = (
            "/kiosk/login"
            if request.session.get("kiosk_business_id")
            else "/kiosk/enter"
        )
        return RedirectResponse(target, status_code=302)

    target = (
        home_path_for_role(
            request.session.get("user_role"),
        )
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


@app.exception_handler(RequiresPlatformAdminException)
async def requires_platform_admin_handler(request: Request, exc: RequiresPlatformAdminException):
    """Block tenant admins from global platform operations."""
    if request.url.path.startswith("/superadmin"):
        return RedirectResponse("/superadmin/login", status_code=302)
    target = (
        home_path_for_role(request.session.get("user_role"))
        if request.session.get("user_id")
        else "/login"
    )
    flow_log(
        "permission.redirect_platform_admin",
        path=request.url.path,
        user_id=request.session.get("user_id"),
        role=request.session.get("user_role"),
        platform_role=request.session.get("user_platform_role"),
        target=target,
    )
    return RedirectResponse(target, status_code=302)


@app.exception_handler(RequiresSuperadminLoginException)
async def requires_superadmin_login_handler(request: Request, exc: RequiresSuperadminLoginException):
    return RedirectResponse("/superadmin/login", status_code=302)


@app.exception_handler(RequiresSuperadminException)
async def requires_superadmin_handler(request: Request, exc: RequiresSuperadminException):
    return RedirectResponse("/superadmin/login", status_code=302)


@app.exception_handler(RequiresKioskException)
async def requires_kiosk_handler(request: Request, exc: RequiresKioskException):
    """Redirect to kiosk entry when kiosk mode is required but not active."""
    flow_log("kiosk.not_active_redirect", path=request.url.path)
    return RedirectResponse("/kiosk/enter", status_code=302)


@app.exception_handler(RequiresOnboardingException)
async def requires_onboarding_handler(request: Request, exc: RequiresOnboardingException):
    """Redirect admins with no businesses to the onboarding / business creation screen."""
    flow_log("onboarding.redirect", path=request.url.path)
    return RedirectResponse("/businesses/new", status_code=302)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth.router)
app.include_router(kiosk.router)
app.include_router(businesses.router)
app.include_router(dashboard.router)
app.include_router(employees.router)
app.include_router(clock.router)
app.include_router(sessions.router)
app.include_router(me.router)
app.include_router(analytics.router)
app.include_router(schedules.router)
app.include_router(expenses.router)
app.include_router(superadmin.router)


# ---------------------------------------------------------------------------
# Root redirect
# ---------------------------------------------------------------------------

@app.get("/")
async def root(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=302)
    return RedirectResponse(
        home_path_for_role(
            request.session.get("user_role"),
        ),
        status_code=302,
    )
