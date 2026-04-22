from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EmployeeCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=40)
    dni: str | None = Field(default=None, max_length=40)
    role_title: str | None = Field(default=None, max_length=100)
    pin: str | None = Field(default=None, min_length=4, max_length=12)
    password: str | None = Field(default=None, min_length=8, max_length=256)
    hired_on: date | None = None
    is_active: bool = True

    @field_validator("first_name", "last_name", "email", "phone", "dni", "role_title", "pin", mode="before")
    @classmethod
    def strip_optional_strings(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        return value.lower() if value else value

    @field_validator("pin")
    @classmethod
    def validate_pin(cls, value: str | None) -> str | None:
        if value and not value.isdigit():
            raise ValueError("PIN must contain digits only.")
        return value


class EmployeeUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    last_name: str | None = Field(default=None, min_length=1, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=40)
    dni: str | None = Field(default=None, max_length=40)
    role_title: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None

    @field_validator("first_name", "last_name", "email", "phone", "dni", "role_title", mode="before")
    @classmethod
    def strip_strings(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    user_id: UUID | None
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    dni: str | None
    role_title: str | None
    hired_on: date | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class EmployeeListResponse(BaseModel):
    items: list[EmployeeRead]

