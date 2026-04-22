from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token_value,
    hash_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository
from app.services.permissions import permissions_for_role


@dataclass(frozen=True)
class AuthTokens:
    access_token: str
    refresh_token: str
    expires_in: int
    user: User


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.companies = CompanyRepository(db)

    def login(
        self,
        *,
        identifier: str,
        password: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> AuthTokens:
        user = self.users.get_by_email(identifier.lower())
        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password.")
        company = self.companies.get(user.company_id)
        if company is None:
            raise AuthenticationError("Company is not active.")
        self.users.mark_login(user)
        return self._issue_tokens(user, user_agent=user_agent, ip_address=ip_address)

    def refresh(
        self,
        *,
        refresh_token_value: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> AuthTokens:
        old_token = self.users.get_refresh_token(hash_token(refresh_token_value))
        if old_token is None or not old_token.is_active:
            raise AuthenticationError("Invalid refresh token.")
        user = self.users.get_active(old_token.user_id, old_token.company_id)
        if user is None:
            raise AuthenticationError("User is not active.")
        tokens = self._issue_tokens(user, user_agent=user_agent, ip_address=ip_address)
        replacement = self.users.get_refresh_token(hash_token(tokens.refresh_token))
        self.users.revoke_refresh_token(
            old_token,
            replacement_id=replacement.id if replacement else None,
        )
        self.db.commit()
        return tokens

    def _issue_tokens(
        self,
        user: User,
        *,
        user_agent: str | None,
        ip_address: str | None,
    ) -> AuthTokens:
        settings = get_settings()
        access_token = create_access_token(
            user_id=user.id,
            company_id=user.company_id,
            role=user.role.value,
        )
        refresh_token_value = create_refresh_token_value()
        refresh_token = RefreshToken(
            company_id=user.company_id,
            user_id=user.id,
            token_hash=hash_token(refresh_token_value),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.users.add_refresh_token(refresh_token)
        self.db.commit()
        return AuthTokens(
            access_token=access_token,
            refresh_token=refresh_token_value,
            expires_in=settings.access_token_expire_minutes * 60,
            user=user,
        )

    def permissions(self, user: User) -> list[str]:
        return permissions_for_role(user.role)
