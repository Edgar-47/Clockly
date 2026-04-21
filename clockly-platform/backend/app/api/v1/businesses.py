from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.api.v1.dependencies import (
    ApiContext,
    build_auth_payload,
    require_api_permission,
    require_api_user,
    set_access_cookie,
)
from app.api.v1.errors import forbidden, not_found, validation_error
from app.api.v1.serializers import business_to_dict
from app.database.business_repository import BusinessRepository
from app.database.business_user_repository import BusinessUserRepository
from app.schemas.api_v1 import (
    BusinessCreateRequest,
    BusinessSwitchRequest,
    BusinessUpdateRequest,
)
from app.services.business_service import BusinessService


router = APIRouter(prefix="/businesses", tags=["api-businesses"])


@router.get("")
async def list_businesses(ctx: ApiContext = Depends(require_api_user)) -> dict:
    business_user_repo = BusinessUserRepository()
    businesses = BusinessService().list_businesses_for_user(ctx.user.id)
    return {
        "items": [
            business_to_dict(
                business,
                active=business.id == ctx.active_business_id,
                role=business_user_repo.get_active_role(
                    business_id=business.id,
                    user_id=ctx.user.id,
                ),
            )
            for business in businesses
        ],
        "active_business_id": ctx.active_business_id,
    }


@router.post("")
async def create_business(
    payload: BusinessCreateRequest,
    response: Response,
    ctx: ApiContext = Depends(require_api_user),
) -> dict:
    if ctx.user.role != "admin":
        raise forbidden("Solo un administrador puede crear negocios.")
    try:
        business = BusinessService().create_business(
            owner_user_id=ctx.user.id,
            business_name=payload.business_name,
            business_type=payload.business_type,
            login_code=payload.login_code,
            timezone=payload.timezone,
            country=payload.country,
            plan_code=payload.plan_code,
        )
    except ValueError as exc:
        raise validation_error(str(exc)) from exc

    auth_payload = build_auth_payload(ctx.user, active_business_id=business.id)
    set_access_cookie(response, auth_payload["access_token"])
    return {
        "business": business_to_dict(business, active=True, role="owner"),
        "auth": auth_payload,
    }


@router.put("/{business_id}")
async def update_business(
    business_id: str,
    payload: BusinessUpdateRequest,
    ctx: ApiContext = Depends(require_api_permission("business:update")),
) -> dict:
    if business_id != ctx.active_business_id:
        raise forbidden("Solo puedes modificar el negocio activo.")
    try:
        business = BusinessService().update_business(
            requester_user_id=ctx.user.id,
            business_id=business_id,
            business_name=payload.business_name,
            business_type=payload.business_type,
            login_code=payload.login_code,
            timezone=payload.timezone,
            country=payload.country,
            settings_json=payload.settings,
        )
    except ValueError as exc:
        raise validation_error(str(exc)) from exc
    return {"business": business_to_dict(business, active=True, role=ctx.active_business_role)}


@router.delete("/{business_id}")
async def delete_business(
    business_id: str,
    ctx: ApiContext = Depends(require_api_permission("business:update")),
) -> dict:
    if business_id != ctx.active_business_id:
        raise forbidden("Solo puedes desactivar el negocio activo.")
    business = BusinessRepository().get_by_id(business_id)
    if business is None or not business.is_active:
        raise not_found("Negocio no encontrado.")
    BusinessRepository().soft_delete(business_id=business_id)
    return {"ok": True, "business_id": business_id, "deleted": True}


@router.post("/switch")
async def switch_business(
    payload: BusinessSwitchRequest,
    response: Response,
    ctx: ApiContext = Depends(require_api_user),
) -> dict:
    try:
        business = BusinessService().activate_business_for_user(
            user_id=ctx.user.id,
            business_id=payload.business_id,
        )
    except ValueError as exc:
        raise validation_error(str(exc)) from exc

    auth_payload = build_auth_payload(ctx.user, active_business_id=business.id)
    set_access_cookie(response, auth_payload["access_token"])
    return {
        "business": business_to_dict(
            business,
            active=True,
            role=auth_payload["active_business_role"],
        ),
        "auth": auth_payload,
    }
