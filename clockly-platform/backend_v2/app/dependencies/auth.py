from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AuthenticationError, PermissionDenied
from app.core.security import TokenDecodeError, decode_access_token
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User
from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository
from app.services.permissions import permissions_for_role, role_has_permission


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class TenantContext:
    user: User
    company: Company

    @property
    def company_id(self):
        return self.company.id

    @property
    def permissions(self) -> list[str]:
        return permissions_for_role(self.user.role)


def get_current_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> TenantContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError("Missing bearer token.")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(str(payload["sub"]))
        company_id = UUID(str(payload["company_id"]))
    except (KeyError, ValueError, TokenDecodeError) as exc:
        raise AuthenticationError("Invalid bearer token.") from exc

    user = UserRepository(db).get_active(user_id, company_id)
    company = CompanyRepository(db).get(company_id)
    if user is None or company is None:
        raise AuthenticationError("User or company is not active.")
    return TenantContext(user=user, company=company)


def require_permission(permission: str):
    def dependency(ctx: TenantContext = Depends(get_current_context)) -> TenantContext:
        if not role_has_permission(ctx.user.role, permission):
            raise PermissionDenied("Insufficient permissions.")
        return ctx

    return dependency

