from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import ApiContext, require_api_business
from app.api.v1.serializers import permissions_for_role
from app.services.authorization_service import ROLE_PERMISSIONS


router = APIRouter(prefix="/roles", tags=["api-roles"])


@router.get("/permissions")
async def permissions(ctx: ApiContext = Depends(require_api_business)) -> dict:
    return {
        "active_business_role": ctx.active_business_role,
        "permissions": permissions_for_role(ctx.active_business_role),
        "roles": {
            role: sorted(values)
            for role, values in ROLE_PERMISSIONS.items()
        },
    }
