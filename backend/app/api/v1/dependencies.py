from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Request, Response

from app.api.v1.errors import ApiError, forbidden, unauthorized
from app.api.v1.serializers import business_to_dict, permissions_for_role, user_to_dict
from app.config import SECURE_COOKIES, SESSION_MAX_AGE
from app.core.jwt import TokenError, create_access_token, decode_access_token
from app.database.business_repository import BusinessRepository
from app.database.business_user_repository import BusinessUserRepository
from app.database.employee_repository import EmployeeRepository
from app.models.employee import Employee
from app.services.authorization_service import AuthorizationError, AuthorizationService
from app.services.business_service import BusinessService


ACCESS_COOKIE_NAME = "clockly_access_token"


@dataclass(frozen=True)
class ApiContext:
    user: Employee
    active_business_id: str | None
    active_business_role: str | None
    token_payload: dict

    @property
    def permissions(self) -> list[str]:
        return permissions_for_role(self.active_business_role)


def set_access_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        ACCESS_COOKIE_NAME,
        token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=SECURE_COOKIES,
        samesite="lax",
    )


def clear_access_cookie(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE_NAME)


def build_auth_payload(
    user: Employee,
    *,
    active_business_id: str | None = None,
) -> dict:
    business_repo = BusinessRepository()
    business_user_repo = BusinessUserRepository()
    business_service = BusinessService()
    businesses = business_service.list_businesses_for_user(user.id)

    if active_business_id and not business_repo.user_has_access(
        business_id=active_business_id,
        user_id=user.id,
    ):
        active_business_id = None
    if active_business_id is None:
        default_business = business_service.choose_default_business(user.id)
        active_business_id = default_business.id if default_business else None

    active_role = None
    if active_business_id:
        active_role = business_user_repo.get_active_role(
            business_id=active_business_id,
            user_id=user.id,
        )

    token = create_access_token(
        user_id=user.id,
        role=user.role,
        active_business_id=active_business_id,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": SESSION_MAX_AGE,
        "user": user_to_dict(user, business_role=active_role),
        "active_business_id": active_business_id,
        "active_business_role": active_role,
        "permissions": permissions_for_role(active_role),
        "businesses": [
            business_to_dict(
                business,
                active=business.id == active_business_id,
                role=business_user_repo.get_active_role(
                    business_id=business.id,
                    user_id=user.id,
                ),
            )
            for business in businesses
        ],
    }


def require_api_user(request: Request) -> ApiContext:
    token = _token_from_request(request)
    if not token:
        raise unauthorized()
    try:
        payload = decode_access_token(token)
    except TokenError as exc:
        raise unauthorized(str(exc)) from exc

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise unauthorized("Token sin usuario valido.") from exc

    user = EmployeeRepository().get_by_id(user_id)
    if user is None or not user.active:
        raise unauthorized("Usuario no disponible.")

    active_business_id = payload.get("active_business_id")
    active_role = None
    if active_business_id and BusinessRepository().user_has_access(
        business_id=active_business_id,
        user_id=user.id,
    ):
        active_role = BusinessUserRepository().get_active_role(
            business_id=active_business_id,
            user_id=user.id,
        )
    else:
        active_business_id = None

    return ApiContext(
        user=user,
        active_business_id=active_business_id,
        active_business_role=active_role,
        token_payload=payload,
    )


def require_api_business(ctx: ApiContext = Depends(require_api_user)) -> ApiContext:
    if not ctx.active_business_id:
        raise ApiError(
            status_code=409,
            code="business_required",
            message="Selecciona o crea un negocio para continuar.",
        )
    return ctx


def require_api_permission(permission: str):
    def _dependency(ctx: ApiContext = Depends(require_api_business)) -> ApiContext:
        try:
            AuthorizationService().require_permission(
                user_id=ctx.user.id,
                business_id=ctx.active_business_id or "",
                permission=permission,
            )
        except AuthorizationError as exc:
            raise forbidden(str(exc)) from exc
        return ctx

    return _dependency


def require_any_api_permission(*permissions: str):
    def _dependency(ctx: ApiContext = Depends(require_api_business)) -> ApiContext:
        if any(permission in ctx.permissions for permission in permissions):
            return ctx
        raise forbidden()

    return _dependency


def _token_from_request(request: Request) -> str | None:
    authorization = request.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    cookie_value = request.cookies.get(ACCESS_COOKIE_NAME)
    return cookie_value.strip() if cookie_value else None
