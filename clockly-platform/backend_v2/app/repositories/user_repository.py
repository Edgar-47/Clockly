from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_active(self, user_id: UUID, company_id: UUID) -> User | None:
        return self.db.scalar(
            select(User).where(
                User.id == user_id,
                User.company_id == company_id,
                User.is_active.is_(True),
            )
        )

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def mark_login(self, user: User) -> None:
        user.last_login_at = datetime.now(UTC)
        self.db.add(user)

    def add_refresh_token(self, refresh_token: RefreshToken) -> RefreshToken:
        self.db.add(refresh_token)
        self.db.flush()
        return refresh_token

    def get_refresh_token(self, token_hash: str) -> RefreshToken | None:
        return self.db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))

    def revoke_refresh_token(
        self,
        refresh_token: RefreshToken,
        *,
        replacement_id: UUID | None = None,
    ) -> None:
        refresh_token.revoked_at = datetime.now(UTC)
        refresh_token.replaced_by_token_id = replacement_id
        self.db.add(refresh_token)

