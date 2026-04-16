from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    identifier: str
    password: str

    @field_validator("identifier", "password", mode="before")
    @classmethod
    def strip_strings(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class BusinessCreateRequest(BaseModel):
    business_name: str
    business_type: str = "otro"
    login_code: str = ""
    timezone: str = "Europe/Madrid"
    country: str | None = None
    plan_code: str | None = None


class BusinessUpdateRequest(BaseModel):
    business_name: str
    business_type: str
    login_code: str
    timezone: str = "Europe/Madrid"
    country: str | None = None
    settings: dict | None = None


class BusinessSwitchRequest(BaseModel):
    business_id: str


class EmployeeCreateRequest(BaseModel):
    first_name: str
    last_name: str
    dni: str
    password: str = ""
    role: str = "employee"
    internal_code: str | None = None
    pin_code: str | None = None
    email: str | None = None
    phone: str | None = None
    role_title: str | None = None


class EmployeeUpdateRequest(BaseModel):
    first_name: str
    last_name: str
    dni: str
    role: str = "employee"
    active: bool = True


class ClockRequest(BaseModel):
    employee_id: int | None = None
    exit_note: str | None = Field(default=None, max_length=500)
    incident_type: str | None = None


class AttendanceHistoryQuery(BaseModel):
    date_from: str | None = None
    date_to: str | None = None
    employee_id: int | None = None
    is_active: int | None = None
    incident_filter: str | None = None
