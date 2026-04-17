"""
app/api/routes/businesses.py

Business management routes for the admin panel.

Responsibilities:
  - Onboarding: first-time business creation for a new admin
  - Business CRUD: create, view settings, update
  - Business selector: switch active business when managing multiple workspaces

Session key managed here:
  active_business_id  (str) — UUID of the currently selected business

All mutation routes are admin-only.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.api.dependencies import (
    flash,
    get_active_business_id,
    require_admin,
    require_active_business,
    set_active_business_id,
    set_active_business_role,
    template_context,
)
from app.core.flow_debug import flow_log, form_keys
from app.core.security import business_role_to_session_role
from app.core.templates import templates
from app.database.business_repository import BusinessRepository
from app.database.business_user_repository import BusinessUserRepository
from app.database.plan_repository import PlanRepository
from app.models.employee import Employee
from app.services.business_service import BusinessService
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/businesses", tags=["businesses"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _business_type_choices() -> list[dict]:
    return [
        {"value": k, "label": v}
        for k, v in BusinessService.BUSINESS_TYPES.items()
    ]


def _load_business_or_404(business_id: str, current_user: Employee) -> object:
    """Load a business by ID and verify the requesting admin has access."""
    repo = BusinessRepository()
    business = repo.get_by_id(business_id)
    if not business or not repo.user_has_access(business_id=business_id, user_id=current_user.id):
        return None
    return business


# ---------------------------------------------------------------------------
# 1. Business list / selector
# ---------------------------------------------------------------------------

@router.get("", response_class=HTMLResponse)
async def business_list(
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    """Show all businesses the admin has access to, with a switch action."""
    svc = BusinessService()
    businesses = svc.list_businesses_for_user(current_user.id)
    active_business_id = get_active_business_id(request)

    ctx = template_context(request)
    ctx.update({
        "businesses": businesses,
        "active_business_id": active_business_id,
    })
    return templates.TemplateResponse(request, "businesses/list.html", ctx)


# ---------------------------------------------------------------------------
# 2. Select / switch active business
# ---------------------------------------------------------------------------

@router.post("/select")
async def business_select(
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    """Switch the admin's active business context."""
    form_data = await request.form()
    business_id = str(form_data.get("business_id", "")).strip()
    next_url = str(form_data.get("next", "/dashboard")).strip() or "/dashboard"

    flow_log("businesses.select", user_id=current_user.id, business_id=business_id)

    if not business_id:
        flash(request, "Selecciona un negocio válido.", "error")
        return RedirectResponse("/businesses", status_code=303)

    try:
        svc = BusinessService()
        business = svc.activate_business_for_user(
            user_id=current_user.id,
            business_id=business_id,
        )
        set_active_business_id(request, business.id)
        business_role = BusinessUserRepository().get_active_role(
            business_id=business.id,
            user_id=current_user.id,
        )
        set_active_business_role(request, business_role)
        if business_role:
            request.session["user_role"] = business_role_to_session_role(business_role)
        flash(request, f"Negocio cambiado a «{business.business_name}».", "success")
        flow_log(
            "businesses.select.success",
            user_id=current_user.id,
            business_id=business.id,
            business_name=business.business_name,
        )
    except ValueError as exc:
        flash(request, str(exc), "error")
        return RedirectResponse("/businesses", status_code=303)

    # Honour `next` only for safe internal paths
    safe_next = next_url if next_url.startswith("/") else "/dashboard"
    return RedirectResponse(safe_next, status_code=303)


# ---------------------------------------------------------------------------
# 3. Create new business (also serves as the first-time onboarding screen)
# ---------------------------------------------------------------------------

@router.get("/new", response_class=HTMLResponse)
async def business_new_form(
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    """Render the business creation form.
    When the user has zero businesses this doubles as the onboarding screen."""
    svc = BusinessService()
    is_onboarding = svc.requires_onboarding(current_user.id)

    ctx = template_context(request)
    ctx.update({
        "form": {},
        "business_type_choices": _business_type_choices(),
        "plan_choices": PlanRepository().list_active(),
        "is_onboarding": is_onboarding,
    })
    return templates.TemplateResponse(request, "businesses/new.html", ctx)


@router.post("/new")
async def business_create(
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    """Create a new business workspace and activate it."""
    form_data = await request.form()

    business_name = str(form_data.get("business_name", "")).strip()
    business_type = str(form_data.get("business_type", "otro")).strip()
    timezone = str(form_data.get("timezone", "Europe/Madrid")).strip()
    country = str(form_data.get("country", "")).strip() or None
    plan_code = str(form_data.get("plan_code", "free")).strip() or "free"
    raw_code = str(form_data.get("login_code", "")).strip()

    flow_log(
        "businesses.create.form",
        user_id=current_user.id,
        form_keys=form_keys(form_data),
        business_name=business_name,
        business_type=business_type,
    )

    svc = BusinessService()
    is_onboarding = svc.requires_onboarding(current_user.id)

    try:
        business = svc.create_business(
            owner_user_id=current_user.id,
            business_name=business_name,
            business_type=business_type,
            login_code=raw_code,
            timezone=timezone,
            country=country,
            plan_code=plan_code,
        )
    except ValueError as exc:
        ctx = template_context(request)
        ctx.update({
            "error": str(exc),
                "form": {
                    "business_name": business_name,
                    "business_type": business_type,
                    "timezone": timezone,
                    "country": country,
                    "plan_code": plan_code,
                    "login_code": raw_code,
                },
                "business_type_choices": _business_type_choices(),
                "plan_choices": PlanRepository().list_active(),
                "is_onboarding": is_onboarding,
            })
        return templates.TemplateResponse(request, "businesses/new.html", ctx, status_code=400)

    # Activate the newly created business
    set_active_business_id(request, business.id)
    set_active_business_role(request, "owner")
    request.session["user_role"] = "admin"

    flow_log(
        "businesses.create.success",
        user_id=current_user.id,
        business_id=business.id,
        business_name=business.business_name,
    )

    if is_onboarding:
        flash(
            request,
            f"¡Bienvenido! Tu negocio «{business.business_name}» está listo. Código kiosk: {business.login_code}.",
            "success",
        )
    else:
        flash(
            request,
            f"Negocio «{business.business_name}» creado correctamente. Código kiosk: {business.login_code}.",
            "success",
        )

    return RedirectResponse("/dashboard", status_code=303)


# ---------------------------------------------------------------------------
# 4. Business settings (view + edit)
# ---------------------------------------------------------------------------

@router.get("/{business_id}/settings", response_class=HTMLResponse)
async def business_settings_form(
    business_id: str,
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    """Render the business settings / edit form."""
    business = _load_business_or_404(business_id, current_user)
    if not business:
        flash(request, "Negocio no encontrado o sin acceso.", "error")
        return RedirectResponse("/businesses", status_code=302)

    ctx = template_context(request)
    ctx.update({
        "business": business,
        "form": {
            "business_name": business.business_name,
            "business_type": business.business_type,
            "timezone": business.timezone,
            "country": business.country,
            "login_code": business.login_code,
        },
        "business_type_choices": _business_type_choices(),
        "usage": SubscriptionService().get_usage_summary(business.id),
    })
    return templates.TemplateResponse(request, "businesses/settings.html", ctx)


@router.post("/{business_id}/settings")
async def business_settings_update(
    business_id: str,
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    """Update business settings."""
    business = _load_business_or_404(business_id, current_user)
    if not business:
        flash(request, "Negocio no encontrado o sin acceso.", "error")
        return RedirectResponse("/businesses", status_code=302)

    form_data = await request.form()
    business_name = str(form_data.get("business_name", "")).strip()
    business_type = str(form_data.get("business_type", "")).strip()
    timezone = str(form_data.get("timezone", "Europe/Madrid")).strip()
    country = str(form_data.get("country", "")).strip() or None
    login_code = str(form_data.get("login_code", "")).strip()

    flow_log(
        "businesses.settings.form",
        user_id=current_user.id,
        business_id=business_id,
        form_keys=form_keys(form_data),
    )

    svc = BusinessService()
    try:
        updated = svc.update_business(
            requester_user_id=current_user.id,
            business_id=business_id,
            business_name=business_name,
            business_type=business_type,
            login_code=login_code,
            timezone=timezone,
            country=country,
        )
        flash(request, "Configuración guardada correctamente.", "success")
        flow_log(
            "businesses.settings.updated",
            user_id=current_user.id,
            business_id=updated.id,
        )
    except ValueError as exc:
        ctx = template_context(request)
        ctx.update({
            "business": business,
            "error": str(exc),
            "form": {
                "business_name": business_name,
                "business_type": business_type,
                "timezone": timezone,
                "country": country,
                "login_code": login_code,
            },
            "business_type_choices": _business_type_choices(),
            "usage": SubscriptionService().get_usage_summary(business_id),
        })
        return templates.TemplateResponse(
            request, "businesses/settings.html", ctx, status_code=400
        )

    return RedirectResponse(f"/businesses/{business_id}/settings", status_code=303)


# ---------------------------------------------------------------------------
# 5. Plan upgrade
# ---------------------------------------------------------------------------

@router.get("/{business_id}/upgrade", response_class=HTMLResponse)
async def business_upgrade_form(
    business_id: str,
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    """Show available upgrade plans for the business."""
    business = _load_business_or_404(business_id, current_user)
    if not business:
        flash(request, "Negocio no encontrado o sin acceso.", "error")
        return RedirectResponse("/businesses", status_code=302)

    svc = SubscriptionService()
    usage = svc.get_usage_summary(business.id)
    upgrade_options = svc.get_upgrade_options(business.id)

    ctx = template_context(request)
    ctx.update({
        "business": business,
        "usage": usage,
        "upgrade_options": upgrade_options,
    })
    return templates.TemplateResponse(request, "businesses/upgrade.html", ctx)


@router.post("/{business_id}/upgrade")
async def business_upgrade(
    business_id: str,
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    """Switch the business to a new plan (manual upgrade without Stripe)."""
    business = _load_business_or_404(business_id, current_user)
    if not business:
        flash(request, "Negocio no encontrado o sin acceso.", "error")
        return RedirectResponse("/businesses", status_code=302)

    form_data = await request.form()
    target_plan_code = str(form_data.get("plan_code", "")).strip()

    try:
        SubscriptionService().upgrade_plan(
            business_id=business.id,
            target_plan_code=target_plan_code,
        )
        flash(request, "Plan actualizado correctamente. ¡Bienvenido al plan Pro!", "success")
        flow_log(
            "businesses.upgrade.success",
            user_id=current_user.id,
            business_id=business.id,
            target_plan=target_plan_code,
        )
    except ValueError as exc:
        flash(request, str(exc), "error")

    return RedirectResponse(f"/businesses/{business_id}/settings", status_code=303)
