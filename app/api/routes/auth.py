"""
app/api/routes/auth.py

Authentication routes: admin login page, login POST, logout.

Design decisions:
  - /login is admin-only. Employees authenticate via the kiosk (/kiosk/login).
  - Logout preserves kiosk context: if kiosk_business_id is in the session
    the browser returns to the kiosk view instead of the entry screen.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.api.dependencies import set_active_business_id, template_context
from app.core.flow_debug import flow_log, form_keys, mask_identifier
from app.core.security import build_session_payload, home_path_for_role
from app.core.templates import templates
from app.services.auth_service import AuthService
from app.services.business_service import BusinessService

router = APIRouter(tags=["auth"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the admin login form. Redirect to dashboard if already authenticated."""
    if request.session.get("user_id"):
        return RedirectResponse(
            home_path_for_role(request.session.get("user_role")),
            status_code=302,
        )
    ctx = template_context(request)
    return templates.TemplateResponse(request, "login.html", ctx)


@router.post("/login")
async def login_post(request: Request):
    """
    Process admin login form.
    Only accepts users with the 'admin' role — employees must use /kiosk/login.
    On success: set session → redirect to /dashboard.
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

        # This endpoint is admin-only; employees use the kiosk flow.
        if employee.role != "admin":
            flow_log(
                "endpoint.login.employee_rejected_at_admin_page",
                user_id=employee.id,
                role=employee.role,
            )
            ctx = template_context(request)
            ctx["error"] = (
                "Este acceso es exclusivo para administradores. "
                "Para fichar, utiliza el kiosk de empleados."
            )
            ctx["identifier"] = identifier
            return templates.TemplateResponse(request, "login.html", ctx, status_code=403)

        request.session.update(build_session_payload(employee))

        # Eagerly pick the admin's default business so the dashboard loads
        # immediately without an extra redirect through onboarding.
        default_business = BusinessService().choose_default_business(employee.id)
        if default_business:
            set_active_business_id(request, default_business.id)

        flow_log(
            "endpoint.login.success",
            user_id=employee.id,
            role=employee.role,
            target="/dashboard",
            business_id=default_business.id if default_business else None,
        )
        return RedirectResponse("/dashboard", status_code=303)

    except ValueError as exc:
        flow_log(
            "endpoint.login.failure",
            identifier=mask_identifier(identifier),
            error=str(exc),
        )
        ctx = template_context(request)
        ctx["error"] = str(exc)
        ctx["identifier"] = identifier
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
        return RedirectResponse("/kiosk", status_code=303)

    return RedirectResponse("/kiosk/enter", status_code=303)


@router.get("/logout")
async def logout_get(request: Request):
    """GET logout (e.g. from a nav link). Same semantics as POST."""
    kiosk_business_id = request.session.get("kiosk_business_id")
    request.session.clear()

    if kiosk_business_id:
        request.session["kiosk_business_id"] = kiosk_business_id
        return RedirectResponse("/kiosk", status_code=302)

    return RedirectResponse("/kiosk/enter", status_code=302)
