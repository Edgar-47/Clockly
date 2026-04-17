from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.security import build_session_payload
from app.core.templates import templates
from app.database.audit_log_repository import AuditLogRepository
from app.database.platform_settings_repository import PlatformSettingsRepository
from app.models.employee import Employee
from app.services.audit_service import audit_log
from app.services.platform_analytics_service import PlatformAnalyticsService
from app.services.superadmin_auth_service import SuperadminAuthService
from app.services.superadmin_service import SuperadminService
from app.superadmin.dependencies import require_superadmin
from app.superadmin.security import (
    build_superadmin_session_payload,
    clear_normal_auth_context,
    clear_superadmin_context,
    superadmin_flash,
    superadmin_template_context,
)


router = APIRouter(prefix="/superadmin", tags=["superadmin"])


def _page(value: int | str | None) -> int:
    try:
        return max(int(value), 1)
    except (TypeError, ValueError):
        return 1


def _ctx(request: Request, **extra) -> dict:
    ctx = superadmin_template_context(request)
    ctx.update(extra)
    return ctx


@router.get("/login", response_class=HTMLResponse)
async def superadmin_login_page(request: Request):
    if request.session.get("superadmin_user_id"):
        return RedirectResponse("/superadmin/dashboard", status_code=302)
    return templates.TemplateResponse(
        request,
        "superadmin/login.html",
        _ctx(request),
        headers={"X-Robots-Tag": "noindex, nofollow"},
    )


@router.post("/login", response_class=HTMLResponse)
async def superadmin_login_post(request: Request):
    form = await request.form()
    identifier = str(form.get("identifier", "")).strip()
    password = str(form.get("password", ""))
    try:
        user = SuperadminAuthService().login(identifier, password)
    except ValueError as exc:
        return templates.TemplateResponse(
            request,
            "superadmin/login.html",
            _ctx(request, error=str(exc), identifier=identifier),
            status_code=400,
            headers={"X-Robots-Tag": "noindex, nofollow"},
        )

    clear_normal_auth_context(request.session)
    request.session.update(build_superadmin_session_payload(user))
    audit_log(
        request,
        "superadmin.login",
        resource_type="platform_user",
        resource_id=user.id,
        metadata={"platform_role": user.platform_role},
    )
    return RedirectResponse("/superadmin/dashboard", status_code=303)


@router.post("/logout")
async def superadmin_logout(request: Request):
    clear_normal_auth_context(request.session)
    clear_superadmin_context(request.session)
    return RedirectResponse("/superadmin/login", status_code=303)


@router.get("/logout")
async def superadmin_logout_get(request: Request):
    clear_normal_auth_context(request.session)
    clear_superadmin_context(request.session)
    return RedirectResponse("/superadmin/login", status_code=302)


@router.get("", response_class=HTMLResponse)
async def superadmin_root():
    return RedirectResponse("/superadmin/dashboard", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    analytics = PlatformAnalyticsService()
    stats = analytics.get_global_stats()
    growth = analytics.get_monthly_growth(months=11)
    revenue = analytics.get_mrr_trend(months=11)
    subscriptions = analytics.get_subscription_evolution()
    return templates.TemplateResponse(
        request,
        "superadmin/dashboard.html",
        _ctx(
            request,
            stats=stats,
            growth=growth,
            revenue=revenue,
            subscriptions=subscriptions,
        ),
    )


@router.get("/businesses", response_class=HTMLResponse)
async def businesses(
    request: Request,
    search: str | None = None,
    status: str | None = None,
    plan: str | None = None,
    page: int = 1,
    current_user: Employee = Depends(require_superadmin),
):
    svc = SuperadminService()
    rows, total = svc.list_businesses(
        search=search,
        status_filter=status,
        plan_filter=plan,
        page=_page(page),
    )
    return templates.TemplateResponse(
        request,
        "superadmin/businesses.html",
        _ctx(
            request,
            businesses=rows,
            total=total,
            filters={"search": search or "", "status": status or "", "plan": plan or ""},
            plans=svc.list_plans(),
            page=_page(page),
        ),
    )


@router.get("/businesses/{business_id}", response_class=HTMLResponse)
async def business_detail(
    business_id: str,
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    svc = SuperadminService()
    detail = svc.get_business_detail(business_id)
    if not detail:
        superadmin_flash(request, "Negocio no encontrado.", "error")
        return RedirectResponse("/superadmin/businesses", status_code=302)
    return templates.TemplateResponse(
        request,
        "superadmin/business_detail.html",
        _ctx(request, detail=detail, plans=svc.list_plans()),
    )


@router.get("/users", response_class=HTMLResponse)
async def users(
    request: Request,
    search: str | None = None,
    role: str | None = None,
    platform: str | None = None,
    status: str | None = None,
    page: int = 1,
    current_user: Employee = Depends(require_superadmin),
):
    svc = SuperadminService()
    rows, total = svc.list_users(
        search=search,
        role_filter=role,
        platform_filter=platform,
        status_filter=status,
        page=_page(page),
    )
    return templates.TemplateResponse(
        request,
        "superadmin/users.html",
        _ctx(
            request,
            users=rows,
            total=total,
            filters={
                "search": search or "",
                "role": role or "",
                "platform": platform or "",
                "status": status or "",
            },
            page=_page(page),
        ),
    )


@router.post("/users/{user_id}/active")
async def user_active(
    user_id: int,
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    form = await request.form()
    active = str(form.get("active", "false")).lower() == "true"
    try:
        SuperadminService().set_user_active(user_id=user_id, active=active)
        audit_log(
            request,
            "superadmin.user.activate" if active else "superadmin.user.deactivate",
            resource_type="user",
            resource_id=user_id,
            new_value={"active": active},
        )
        superadmin_flash(request, "Estado global del usuario actualizado.", "success")
    except ValueError as exc:
        superadmin_flash(request, str(exc), "error")
    return RedirectResponse("/superadmin/users", status_code=303)


@router.post("/businesses/{business_id}/update")
async def business_update(
    business_id: str,
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    form = await request.form()
    svc = SuperadminService()
    try:
        changes = svc.update_business(
            business_id=business_id,
            business_name=str(form.get("business_name", "")),
            primary_email=str(form.get("primary_email", "")) or None,
            phone=str(form.get("phone", "")) or None,
            business_type=str(form.get("business_type", "otro")),
            timezone=str(form.get("timezone", "Europe/Madrid")),
            country=str(form.get("country", "")) or None,
        )
        audit_log(
            request,
            "superadmin.business.update",
            resource_type="business",
            resource_id=business_id,
            business_id=business_id,
            old_value=changes["old"],
            new_value=changes["new"],
        )
        superadmin_flash(request, "Negocio actualizado.", "success")
    except ValueError as exc:
        superadmin_flash(request, str(exc), "error")
    return RedirectResponse(f"/superadmin/businesses/{business_id}", status_code=303)


@router.post("/businesses/{business_id}/users/{user_id}/role")
async def business_user_role(
    business_id: str,
    user_id: int,
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    form = await request.form()
    role = str(form.get("role", "")).strip()
    try:
        SuperadminService().set_business_user_role(
            business_id=business_id,
            user_id=user_id,
            role=role,
        )
        audit_log(
            request,
            "superadmin.business.user_role",
            resource_type="business_user",
            resource_id=user_id,
            business_id=business_id,
            new_value={"role": role},
        )
        superadmin_flash(request, "Rol de usuario actualizado.", "success")
    except ValueError as exc:
        superadmin_flash(request, str(exc), "error")
    return RedirectResponse(f"/superadmin/businesses/{business_id}", status_code=303)


@router.post("/businesses/{business_id}/change-plan")
async def business_change_plan(
    business_id: str,
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    form = await request.form()
    plan_code = str(form.get("plan_code", "")).strip()
    try:
        SuperadminService().change_plan(business_id, plan_code, current_user.id)
        audit_log(
            request,
            "superadmin.business.change_plan",
            resource_type="business",
            resource_id=business_id,
            business_id=business_id,
            new_value={"plan_code": plan_code},
        )
        superadmin_flash(request, "Plan actualizado.", "success")
    except ValueError as exc:
        superadmin_flash(request, str(exc), "error")
    return RedirectResponse(f"/superadmin/businesses/{business_id}", status_code=303)


@router.post("/businesses/{business_id}/suspend")
async def business_suspend(
    business_id: str,
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    form = await request.form()
    if str(form.get("confirm_text", "")).strip() != "SUSPENDER":
        superadmin_flash(request, "Escribe SUSPENDER para confirmar.", "error")
        return RedirectResponse(f"/superadmin/businesses/{business_id}", status_code=303)
    reason = str(form.get("reason", "")).strip()
    try:
        SuperadminService().suspend_business(business_id, reason, current_user.id)
        audit_log(
            request,
            "superadmin.business.suspend",
            resource_type="business",
            resource_id=business_id,
            business_id=business_id,
            new_value={"reason": reason},
        )
        superadmin_flash(request, "Negocio suspendido.", "warning")
    except ValueError as exc:
        superadmin_flash(request, str(exc), "error")
    return RedirectResponse(f"/superadmin/businesses/{business_id}", status_code=303)


@router.post("/businesses/{business_id}/unsuspend")
async def business_unsuspend(
    business_id: str,
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    SuperadminService().unsuspend_business(business_id, current_user.id)
    audit_log(
        request,
        "superadmin.business.unsuspend",
        resource_type="business",
        resource_id=business_id,
        business_id=business_id,
    )
    superadmin_flash(request, "Negocio reactivado.", "success")
    return RedirectResponse(f"/superadmin/businesses/{business_id}", status_code=303)


@router.post("/businesses/{business_id}/archive")
async def business_archive(
    business_id: str,
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    form = await request.form()
    if str(form.get("confirm_text", "")).strip() != business_id:
        superadmin_flash(request, "Escribe el ID completo del negocio para archivarlo.", "error")
        return RedirectResponse(f"/superadmin/businesses/{business_id}", status_code=303)
    SuperadminService().archive_business(business_id, current_user.id)
    audit_log(
        request,
        "superadmin.business.archive",
        resource_type="business",
        resource_id=business_id,
        business_id=business_id,
    )
    superadmin_flash(request, "Negocio archivado con soft delete.", "warning")
    return RedirectResponse("/superadmin/businesses", status_code=303)


@router.post("/businesses/{business_id}/impersonate")
async def business_impersonate(
    business_id: str,
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    detail = SuperadminService().get_business_detail(business_id)
    if not detail:
        superadmin_flash(request, "Negocio no encontrado.", "error")
        return RedirectResponse("/superadmin/businesses", status_code=303)
    business = detail["business"]
    request.session.update(build_session_payload(current_user))
    request.session["impersonation_business_id"] = business_id
    request.session["impersonation_business_name"] = business["business_name"]
    request.session["impersonation_superadmin_id"] = current_user.id
    request.session["active_business_id"] = business_id
    request.session["active_business_role"] = "owner"
    audit_log(
        request,
        "superadmin.business.impersonate",
        resource_type="business",
        resource_id=business_id,
        business_id=business_id,
    )
    superadmin_flash(request, f"Impersonacion activa en {business['business_name']}.", "warning")
    return RedirectResponse("/dashboard", status_code=303)


@router.post("/impersonation/stop")
async def stop_impersonation(
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    clear_normal_auth_context(request.session)
    superadmin_flash(request, "Impersonacion finalizada.", "success")
    return RedirectResponse("/superadmin/dashboard", status_code=303)


@router.get("/subscriptions", response_class=HTMLResponse)
async def subscriptions(
    request: Request,
    status: str | None = None,
    plan: str | None = None,
    page: int = 1,
    current_user: Employee = Depends(require_superadmin),
):
    svc = SuperadminService()
    rows, total = svc.list_subscriptions(
        status_filter=status,
        plan_filter=plan,
        page=_page(page),
    )
    return templates.TemplateResponse(
        request,
        "superadmin/subscriptions.html",
        _ctx(
            request,
            subscriptions=rows,
            total=total,
            filters={"status": status or "", "plan": plan or ""},
            plans=svc.list_plans(),
            page=_page(page),
        ),
    )


@router.post("/subscriptions/{subscription_id}/status")
async def subscription_status(
    subscription_id: int,
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    form = await request.form()
    status = str(form.get("status", "")).strip()
    notes = str(form.get("notes", "")).strip()
    try:
        SuperadminService().change_subscription_status(subscription_id, status, notes)
        audit_log(
            request,
            "superadmin.subscription.change_status",
            resource_type="subscription",
            resource_id=subscription_id,
            new_value={"status": status, "notes": notes},
        )
        superadmin_flash(request, "Suscripcion actualizada.", "success")
    except ValueError as exc:
        superadmin_flash(request, str(exc), "error")
    return RedirectResponse("/superadmin/subscriptions", status_code=303)


@router.post("/subscriptions/{subscription_id}/trial")
async def subscription_trial(
    subscription_id: int,
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    form = await request.form()
    trial_ends_at = str(form.get("trial_ends_at", "")).strip()
    notes = str(form.get("notes", "")).strip()
    if not trial_ends_at:
        superadmin_flash(request, "Indica la fecha de fin de trial.", "error")
        return RedirectResponse("/superadmin/subscriptions", status_code=303)
    SuperadminService().extend_trial(
        subscription_id=subscription_id,
        trial_ends_at=trial_ends_at,
        notes=notes,
    )
    audit_log(
        request,
        "superadmin.subscription.extend_trial",
        resource_type="subscription",
        resource_id=subscription_id,
        new_value={"trial_ends_at": trial_ends_at, "notes": notes},
    )
    superadmin_flash(request, "Trial extendido.", "success")
    return RedirectResponse("/superadmin/subscriptions", status_code=303)


@router.get("/plans", response_class=HTMLResponse)
async def plans(
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    return templates.TemplateResponse(
        request,
        "superadmin/plans.html",
        _ctx(request, plans=SuperadminService().list_plans()),
    )


@router.get("/billing", response_class=HTMLResponse)
async def billing(
    request: Request,
    search: str | None = None,
    current_user: Employee = Depends(require_superadmin),
):
    return templates.TemplateResponse(
        request,
        "superadmin/billing.html",
        _ctx(
            request,
            payment_records=SuperadminService().list_payment_records(search=search),
            search=search or "",
        ),
    )


@router.get("/metrics", response_class=HTMLResponse)
async def metrics(
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    analytics = PlatformAnalyticsService()
    return templates.TemplateResponse(
        request,
        "superadmin/metrics.html",
        _ctx(
            request,
            stats=analytics.get_global_stats(),
            growth=analytics.get_monthly_growth(months=11),
            revenue=analytics.get_mrr_trend(months=11),
            usage_metrics=analytics.get_usage_metrics(),
        ),
    )


@router.get("/internal-users", response_class=HTMLResponse)
async def internal_users(
    request: Request,
    search: str | None = None,
    current_user: Employee = Depends(require_superadmin),
):
    svc = SuperadminService()
    return templates.TemplateResponse(
        request,
        "superadmin/internal_users.html",
        _ctx(
            request,
            internal_users=svc.list_internal_users(),
            admin_candidates=svc.list_all_admin_users(search=search),
            search=search or "",
        ),
    )


@router.post("/internal-users/create")
async def internal_user_create(
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    form = await request.form()
    try:
        user = SuperadminService().create_internal_user(
            full_name=str(form.get("full_name", "")),
            email=str(form.get("email", "")),
            password=str(form.get("password", "")),
            platform_role=str(form.get("platform_role", "internal_admin")),
        )
        audit_log(
            request,
            "superadmin.user.create",
            resource_type="platform_user",
            resource_id=user["id"],
            new_value={"email": user["email"], "platform_role": user["platform_role"]},
        )
        superadmin_flash(request, "Usuario interno creado.", "success")
    except ValueError as exc:
        superadmin_flash(request, str(exc), "error")
    return RedirectResponse("/superadmin/internal-users", status_code=303)


@router.post("/internal-users/{user_id}/role")
async def internal_user_role(
    user_id: int,
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    form = await request.form()
    role = str(form.get("platform_role", "")).strip() or None
    try:
        SuperadminService().set_platform_role(user_id, role, current_user.id)
        audit_log(
            request,
            "superadmin.user.set_role",
            resource_type="platform_user",
            resource_id=user_id,
            new_value={"platform_role": role},
        )
        superadmin_flash(request, "Rol interno actualizado.", "success")
    except ValueError as exc:
        superadmin_flash(request, str(exc), "error")
    return RedirectResponse("/superadmin/internal-users", status_code=303)


@router.post("/internal-users/{user_id}/active")
async def internal_user_active(
    user_id: int,
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    form = await request.form()
    active = str(form.get("active", "false")).lower() == "true"
    SuperadminService().set_internal_user_active(user_id=user_id, active=active)
    audit_log(
        request,
        "superadmin.user.activate" if active else "superadmin.user.deactivate",
        resource_type="platform_user",
        resource_id=user_id,
        new_value={"active": active},
    )
    superadmin_flash(request, "Acceso actualizado.", "success")
    return RedirectResponse("/superadmin/internal-users", status_code=303)


@router.post("/internal-users/{user_id}/reset-password")
async def internal_user_reset_password(
    user_id: int,
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    form = await request.form()
    try:
        SuperadminService().reset_internal_password(
            user_id=user_id,
            new_password=str(form.get("new_password", "")),
            force_change=str(form.get("force_change", "true")).lower() == "true",
        )
        audit_log(
            request,
            "superadmin.user.reset_password",
            resource_type="platform_user",
            resource_id=user_id,
        )
        superadmin_flash(request, "Password reseteada.", "success")
    except ValueError as exc:
        superadmin_flash(request, str(exc), "error")
    return RedirectResponse("/superadmin/internal-users", status_code=303)


@router.get("/logs", response_class=HTMLResponse)
async def logs(
    request: Request,
    action: str | None = None,
    resource_type: str | None = None,
    business_id: str | None = None,
    current_user: Employee = Depends(require_superadmin),
):
    repo = AuditLogRepository()
    return templates.TemplateResponse(
        request,
        "superadmin/audit_logs.html",
        _ctx(
            request,
            logs=repo.list_recent(
                limit=150,
                action_filter=action,
                resource_type=resource_type,
                business_id=business_id,
            ),
            filters={
                "action": action or "",
                "resource_type": resource_type or "",
                "business_id": business_id or "",
            },
        ),
    )


@router.get("/settings", response_class=HTMLResponse)
async def settings(
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    settings_map = PlatformSettingsRepository().get_all()
    return templates.TemplateResponse(
        request,
        "superadmin/settings.html",
        _ctx(request, settings=settings_map),
    )


@router.post("/settings")
async def settings_update(
    request: Request,
    current_user: Employee = Depends(require_superadmin),
):
    form = await request.form()
    values = {str(k): str(v) for k, v in form.items()}
    PlatformSettingsRepository().set_many(values)
    audit_log(
        request,
        "superadmin.settings.update",
        resource_type="platform_settings",
        new_value=values,
    )
    superadmin_flash(request, "Configuracion global guardada.", "success")
    return RedirectResponse("/superadmin/settings", status_code=303)
