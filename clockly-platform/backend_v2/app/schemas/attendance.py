from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AttendanceMethod, AttendanceStatus


class AttendanceSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    employee_id: UUID
    user_id: UUID | None
    clock_in: datetime
    clock_out: datetime | None
    duration_seconds: int | None
    status: AttendanceStatus
    method: AttendanceMethod
    notes: str | None
    created_at: datetime
    updated_at: datetime


class AttendanceSessionListResponse(BaseModel):
    items: list[AttendanceSessionRead]


class ClockInRequest(BaseModel):
    employee_id: UUID | None = None
    method: AttendanceMethod = AttendanceMethod.WEB
    notes: str | None = Field(default=None, max_length=1000)


class ClockOutRequest(BaseModel):
    employee_id: UUID | None = None
    session_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=1000)


class AttendanceQuery(BaseModel):
    employee_id: UUID | None = None
    status: AttendanceStatus | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
