from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.api.v1.dependencies import (
    ApiContext,
    build_auth_payload,
    clear_access_cookie,
    require_api_user,
    set_access_cookie,
)
from app.api.v1.errors import invalid_credentials
from app.schemas.api_v1 import LoginRequest
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["api-auth"])


@router.post("/login")
async def api_login(payload: LoginRequest, response: Response) -> dict:
    try:
        user = AuthService().login(payload.identifier, payload.password)
    except ValueError as exc:
        raise invalid_credentials() from exc

    auth_payload = build_auth_payload(user)
    set_access_cookie(response, auth_payload["access_token"])
    return auth_payload


@router.post("/logout")
async def api_logout(response: Response) -> dict:
    clear_access_cookie(response)
    return {"ok": True}


@router.get("/me")
async def api_me(ctx: ApiContext = Depends(require_api_user)) -> dict:
    return build_auth_payload(
        ctx.user,
        active_business_id=ctx.active_business_id,
    )
