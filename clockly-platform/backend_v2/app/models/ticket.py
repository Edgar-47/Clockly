from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import TicketStatus
from app.models.types import enum_column

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.employee import Employee


class Ticket(TimestampMixin, Base):
    __tablename__ = "tickets"
    __table_args__ = (
        Index("ix_tickets_company_status", "company_id", "status"),
        Index("ix_tickets_company_date", "company_id", "occurred_on"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    employee_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"))
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TicketStatus] = mapped_column(
        enum_column(TicketStatus, name="ticket_status"),
        default=TicketStatus.OPEN,
        nullable=False,
    )
    occurred_on: Mapped[date | None] = mapped_column(Date)
    attachment_key: Mapped[str | None] = mapped_column(String(500))

    company: Mapped[Company] = relationship(back_populates="tickets")
    employee: Mapped[Employee | None] = relationship(back_populates="tickets")

