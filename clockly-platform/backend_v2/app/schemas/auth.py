from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import UserRole


class LoginRequest(BaseModel):
    email: str | None = Field(default=None, max_length=255)
    identifier: str | None = Field(default=None, max_length=255)
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email", "identifier", "password", mode="before")
    @classmethod
    def strip_strings(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @property
    def login_identifier(self) -> str:
        return (self.email or self.identifier or "").strip().lower()


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=512)


class CompanyContext(BaseModel):
    id: UUID
    name: str
    slug: str
    timezone: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    last_login_at: datetime | None = None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead
    company: CompanyContext
    permissions: list[str]


class MeResponse(BaseModel):
    user: UserRead
    company: CompanyContext
    permissions: list[str]

