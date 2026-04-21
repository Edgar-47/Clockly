"""
app/api/routes/auth.py

Authentication routes: login page, login POST, logout.

Design decisions:
  - /login accepts admins and employees, then redirects each role to its own home.
  - Employees can also authenticate via the kiosk (/kiosk/login).
  - Logout preserves kiosk context: if kiosk_business_id is in the session
    the browser returns to the kiosk view instead of the entry screen.
"""

import secrets

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.api.dependencies import (
    flash,
    set_active_business_id,
    set_active_business_role,
    template_context,
)
from app.api.v1.dependencies import (
    build_auth_payload,
    clear_access_cookie,
    set_access_cookie,
)
from app.config import GOOGLE_AUTH_ENABLED, GOOGLE_REDIRECT_URI
from app.core.flow_debug import flow_log, form_keys, mask_identifier
from app.core.security import (
    build_session_payload,
    business_role_to_session_role,
    clear_kiosk_employee_context,
    home_path_for_role,
)
from app.core.templates import templates
from app.database.business_user_repository import BusinessUserRepository
from app.database.employee_repository import EmployeeRepository
from app.database.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.business_service import BusinessService
from app.services.google_auth_service import GoogleAuthError, GoogleAuthService

router = APIRouter(tags=["auth"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login form. Redirect to the role home if already authenticated."""
    if request.session.get("kiosk_business_id"):
        clear_kiosk_employee_context(request.session)

    if request.session.get("user_id"):
        return RedirectResponse(
            home_path_for_role(request.session.get("user_role")),
            status_code=302,
        )
    ctx = template_context(request)
    ctx["google_auth_enabled"] = GOOGLE_AUTH_ENABLED
    return templates.TemplateResponse(request, "login.html", ctx)


@router.get("/auth/google")
async def google_start(request: Request, next: str = "/dashboard"):
    if not GOOGLE_AUTH_ENABLED:
        flash(request, "Google OAuth no esta configurado todavia.", "error")
        return RedirectResponse("/login", status_code=302)

    state = secrets.token_urlsafe(32)
    request.session["google_oauth_state"] = state
    request.session["google_oauth_next"] = next if next.startswith("/") else "/dashboard"
    redirect_uri = _google_redirect_uri(request)
    url = GoogleAuthService().authorization_url(
        redirect_uri=redirect_uri,
        state=state,
    )
    return RedirectResponse(url, status_code=302)


@router.get("/auth/google/callback")
async def google_callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None):
    expected_state = request.session.pop("google_oauth_state", None)
    next_url = request.session.pop("google_oauth_next", "/dashboard")

    if error:
        flash(request, "Google cancelo o rechazo el inicio de sesion.", "error")
        return RedirectResponse("/login", status_code=302)
    if not code or not state or state != expected_state:
        flash(request, "No se pudo validar la sesion de Google.", "error")
        return RedirectResponse("/login", status_code=302)

    try:
        identity = await GoogleAuthService().exchange_code_for_identity(
            code=code,
            redirect_uri=_google_redirect_uri(request),
        )
        user = UserRepository().create_or_update_google_user(
            email=identity.email,
            full_name=identity.full_name,
            google_id=identity.google_id,
        )
    except (GoogleAuthError, ValueError) as exc:
        flash(request, str(exc), "error")
        return RedirectResponse("/login", status_code=302)

    request.session.update(build_session_payload(user))

    default_business, business_role = _activate_default_business_for_login(request, user)
    if default_business:
        target = next_url if next_url.startswith("/") else "/dashboard"
    else:
        target = "/businesses/new"

    flow_log(
        "endpoint.google_login.success",
        user_id=user.id,
        business_id=default_business.id if default_business else None,
        business_role=business_role,
        target=target,
    )
    api_user = EmployeeRepository().get_by_id(user.id)
    response = RedirectResponse(target, status_code=303)
    if api_user:
        auth_payload = build_auth_payload(
            api_user,
            active_business_id=default_business.id if default_business else None,
        )
        set_access_cookie(response, auth_payload["access_token"])
    return response


@router.post("/login")
async def login_post(request: Request):
    """
    Process login form and route each role to its own first screen.
    Admins go to /dashboard; employees go to /me.
    On failure: re-render login with a clear error message.
    """
    form_data = await request.form()
    identifier = str(form_data.get("identifier", "")).strip()
    password = str(form_data.get("password", ""))
    flow_log(
        "frontend.login.form",
        form_keys=form_keys(form_data),
        identifier=mask_identifier(identifier),
        password_present=bool(password),
    )

    try:
        auth_service = AuthService()
        employee = auth_service.login(identifier, password)

        clear_kiosk_employee_context(request.session)
        request.session.update(build_session_payload(employee))

        # Eagerly pick the user's default business so scoped screens and
        # employee self-service do not create unscoped attendance sessions.
        default_business, business_role = _activate_default_business_for_login(request, employee)

        target = home_path_for_role(request.session.get("user_role"))
        flow_log(
            "endpoint.login.success",
            user_id=employee.id,
            role=request.session.get("user_role"),
            business_role=business_role,
            target=target,
            business_id=default_business.id if default_business else None,
        )
        response = RedirectResponse(target, status_code=303)
        auth_payload = build_auth_payload(
            employee,
            active_business_id=default_business.id if default_business else None,
        )
        set_access_cookie(response, auth_payload["access_token"])
        return response

    except ValueError as exc:
        flow_log(
            "endpoint.login.failure",
            identifier=mask_identifier(identifier),
            error=str(exc),
        )
        ctx = template_context(request)
        ctx["error"] = str(exc)
        ctx["identifier"] = identifier
        ctx["google_auth_enabled"] = GOOGLE_AUTH_ENABLED
        return templates.TemplateResponse(request, "login.html", ctx, status_code=400)


@router.post("/logout")
async def logout(request: Request):
    """
    Clear the user session.
    If kiosk mode was active, preserve kiosk context and return to the kiosk view
    so the next employee can clock in without re-entering the business code.
    The admin's active_business_id is always cleared on logout.
    """
    kiosk_business_id = request.session.get("kiosk_business_id")
    request.session.clear()

    if kiosk_business_id:
        request.session["kiosk_business_id"] = kiosk_business_id
        response = RedirectResponse("/kiosk", status_code=303)
        clear_access_cookie(response)
        return response

    response = RedirectResponse("/kiosk/enter", status_code=303)
    clear_access_cookie(response)
    return response


@router.get("/logout")
async def logout_get(request: Request):
    """GET logout (e.g. from a nav link). Same semantics as POST."""
    kiosk_business_id = request.session.get("kiosk_business_id")
    request.session.clear()

    if kiosk_business_id:
        request.session["kiosk_business_id"] = kiosk_business_id
        response = RedirectResponse("/kiosk", status_code=302)
        clear_access_cookie(response)
        return response

    response = RedirectResponse("/kiosk/enter", status_code=302)
    clear_access_cookie(response)
    return response


def _google_redirect_uri(request: Request) -> str:
    if GOOGLE_REDIRECT_URI:
        return GOOGLE_REDIRECT_URI
    return str(request.url_for("google_callback"))


def _activate_default_business_for_login(request: Request, user) -> tuple[object | None, str | None]:
    business = BusinessService().choose_default_business(user.id)
    if not business:
        set_active_business_role(request, None)
        return None, None

    business_role = BusinessUserRepository().get_active_role(
        business_id=business.id,
        user_id=user.id,
    )
    set_active_business_id(request, business.id)
    set_active_business_role(request, business_role)
    if business_role:
        request.session["user_role"] = business_role_to_session_role(business_role)
    return business, business_role
