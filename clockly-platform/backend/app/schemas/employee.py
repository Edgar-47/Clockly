"""
app/schemas/employee.py

Pydantic models for employee HTTP requests.
These are separate from the domain dataclasses in app/models/employee.py.
"""

from pydantic import BaseModel, field_validator


class EmployeeCreateForm(BaseModel):
    first_name: str
    last_name: str
    dni: str
    password: str
    role: str = "employee"

    @field_validator("first_name", "last_name", "dni", "password", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v


class EmployeeUpdateForm(BaseModel):
    first_name: str
    last_name: str
    dni: str
    role: str
    active: bool = True

    @field_validator("first_name", "last_name", "dni", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v


class PasswordChangeForm(BaseModel):
    new_password: str

    @field_validator("new_password", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v
