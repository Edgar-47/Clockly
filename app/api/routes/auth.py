"""
app/api/routes/auth.py

Authentication routes: login page, login POST, logout.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.api.dependencies import template_context
from app.core.flow_debug import flow_log, form_keys, mask_identifier
from app.core.security import build_session_payload, home_path_for_role
from app.core.templates import templates
from app.services.auth_service import AuthService

router = APIRouter(tags=["auth"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login form. Redirect to dashboard if already authenticated."""
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
    Process login form.
    On success: store user in session → redirect to /dashboard.
    On failure: re-render login with error message.
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
        request.session.update(build_session_payload(employee))
        target = home_path_for_role(employee.role)
        flow_log(
            "endpoint.login.success",
            user_id=employee.id,
            role=employee.role,
            target=target,
        )
        return RedirectResponse(target, status_code=303)
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
    """Clear session and redirect to login page."""
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@router.get("/logout")
async def logout_get(request: Request):
    """Support GET logout (e.g. from a simple link in the nav)."""
    request.session.clear()
    return RedirectResponse("/login", status_code=302)
