from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TicketStatus


class TicketCreate(BaseModel):
    employee_id: UUID | None = None
    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    occurred_on: date | None = None
    attachment_key: str | None = Field(default=None, max_length=500)


class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    employee_id: UUID | None
    user_id: UUID | None
    title: str
    description: str | None
    status: TicketStatus
    occurred_on: date | None
    attachment_key: str | None
    created_at: datetime
    updated_at: datetime

