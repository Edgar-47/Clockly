from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import TenantContext, get_current_context
from app.schemas.auth import CompanyContext, LoginRequest, MeResponse, RefreshRequest, TokenResponse
from app.services.auth_service import AuthService, AuthTokens
from app.services.permissions import permissions_for_role


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    tokens = AuthService(db).login(
        identifier=payload.login_identifier,
        password=payload.password,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    return _token_response(tokens)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    tokens = AuthService(db).refresh(
        refresh_token_value=payload.refresh_token,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    return _token_response(tokens)


@router.get("/me", response_model=MeResponse)
def me(ctx: TenantContext = Depends(get_current_context)) -> MeResponse:
    return MeResponse(
        user=ctx.user,
        company=CompanyContext(
            id=ctx.company.id,
            name=ctx.company.name,
            slug=ctx.company.slug,
            timezone=ctx.company.timezone,
        ),
        permissions=ctx.permissions,
    )


def _token_response(tokens: AuthTokens) -> TokenResponse:
    company = tokens.user.company
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
        user=tokens.user,
        company=CompanyContext(
            id=company.id,
            name=company.name,
            slug=company.slug,
            timezone=company.timezone,
        ),
        permissions=permissions_for_role(tokens.user.role),
    )
