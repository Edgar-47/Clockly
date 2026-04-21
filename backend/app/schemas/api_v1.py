from __future__ import annotations

import re
from datetime import date as _date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s]{2,}$")
_ISO_DATE_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$")


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=256)

    @field_validator("identifier", "password", mode="before")
    @classmethod
    def strip_strings(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class BusinessCreateRequest(BaseModel):
    business_name: str = Field(min_length=2, max_length=120)
    business_type: str = Field(default="otro", max_length=60)
    login_code: str = Field(default="", max_length=40)
    timezone: str = Field(default="Europe/Madrid", max_length=80)
    country: str | None = Field(default=None, max_length=80)
    plan_code: str | None = Field(default=None, max_length=40)

    @field_validator("business_name", "business_type", "login_code", "timezone", mode="before")
    @classmethod
    def strip_str(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v


class BusinessUpdateRequest(BaseModel):
    business_name: str = Field(min_length=2, max_length=120)
    business_type: str = Field(max_length=60)
    login_code: str = Field(max_length=40)
    timezone: str = Field(default="Europe/Madrid", max_length=80)
    country: str | None = Field(default=None, max_length=80)
    settings: dict | None = None

    @field_validator("business_name", "business_type", "login_code", "timezone", mode="before")
    @classmethod
    def strip_str(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v


class BusinessSwitchRequest(BaseModel):
    business_id: str = Field(min_length=1, max_length=80)


class EmployeeCreateRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=120)
    dni: str = Field(min_length=1, max_length=40)
    # password is optional at API level (service generates one if omitted).
    # When provided it must meet the 6-char minimum.
    password: str | None = Field(default=None, max_length=256)
    role: Literal["admin", "employee"] = "employee"
    internal_code: str | None = Field(default=None, max_length=40)
    pin_code: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=160)
    phone: str | None = Field(default=None, max_length=40)
    role_title: str | None = Field(default=None, max_length=100)

    @field_validator("first_name", "last_name", "dni", mode="before")
    @classmethod
    def strip_required(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, v: object) -> object:
        if v is None or v == "":
            return None
        if isinstance(v, str):
            v = v.strip()
            if len(v) < 6:
                raise ValueError("La contraseña debe tener al menos 6 caracteres.")
        return v

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: object) -> object:
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        if isinstance(v, str) and not _EMAIL_RE.match(v.strip().lower()):
            raise ValueError("Formato de email no válido.")
        return v.strip().lower() if isinstance(v, str) else v

    @field_validator("pin_code", mode="before")
    @classmethod
    def validate_pin(cls, v: object) -> object:
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        if isinstance(v, str) and not v.strip().isdigit():
            raise ValueError("El PIN solo puede contener dígitos.")
        return v.strip() if isinstance(v, str) else v


class EmployeeUpdateRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=120)
    dni: str = Field(min_length=1, max_length=40)
    role: Literal["admin", "employee"] = "employee"
    active: bool = True

    @field_validator("first_name", "last_name", "dni", mode="before")
    @classmethod
    def strip_required(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v


class ClockRequest(BaseModel):
    employee_id: int | None = None
    exit_note: str | None = Field(default=None, max_length=500)
    incident_type: str | None = Field(default=None, max_length=60)

    @field_validator("exit_note", "incident_type", mode="before")
    @classmethod
    def strip_optional(cls, v: object) -> object:
        if isinstance(v, str):
            stripped = v.strip()
            return stripped if stripped else None
        return v


class EmployeePatchRequest(BaseModel):
    active: bool | None = None


class AttendanceHistoryQuery(BaseModel):
    date_from: str | None = Field(default=None, max_length=10)
    date_to: str | None = Field(default=None, max_length=10)
    employee_id: int | None = None
    is_active: int | None = None
    incident_filter: str | None = Field(default=None, max_length=60)

    @field_validator("date_from", "date_to", mode="before")
    @classmethod
    def validate_iso_date(cls, v: object) -> object:
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        if isinstance(v, str):
            v = v.strip()
            if not _ISO_DATE_RE.match(v):
                raise ValueError("La fecha debe tener formato AAAA-MM-DD.")
            try:
                _date.fromisoformat(v)
            except ValueError as exc:
                raise ValueError("Fecha no válida.") from exc
        return v


class TicketCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    amount: float = Field(gt=0, le=99_999.99)
    category: Literal["expense", "purchase", "travel", "food", "other"] = "other"
    date: str = Field(min_length=10, max_length=10)
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, v: object) -> object:
        if not isinstance(v, str):
            raise ValueError("La fecha debe ser una cadena ISO (AAAA-MM-DD).")
        v = v.strip()
        if not _ISO_DATE_RE.match(v):
            raise ValueError("La fecha debe tener formato AAAA-MM-DD.")
        try:
            _date.fromisoformat(v)
        except ValueError as exc:
            raise ValueError("Fecha no válida.") from exc
        return v


class TicketReviewRequest(BaseModel):
    status: Literal["pending", "approved", "reimbursed", "rejected"]
    review_note: str | None = Field(default=None, max_length=1000)

    @field_validator("review_note", mode="before")
    @classmethod
    def strip_note(cls, v: object) -> object:
        if isinstance(v, str):
            stripped = v.strip()
            return stripped if stripped else None
        return v
