from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import AttendanceMethod, AttendanceStatus
from app.models.types import enum_column

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.employee import Employee


class AttendanceSession(TimestampMixin, Base):
    __tablename__ = "attendance_sessions"
    __table_args__ = (
        CheckConstraint("duration_seconds IS NULL OR duration_seconds >= 0", name="duration_non_negative"),
        CheckConstraint("clock_out IS NULL OR clock_out >= clock_in", name="clock_out_after_clock_in"),
        Index(
            "uq_attendance_sessions_one_open_per_employee",
            "company_id",
            "employee_id",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
        Index("ix_attendance_sessions_company_clock_in", "company_id", "clock_in"),
        Index("ix_attendance_sessions_company_status", "company_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    clock_in: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    clock_out: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[AttendanceStatus] = mapped_column(
        enum_column(AttendanceStatus, name="attendance_status"),
        default=AttendanceStatus.OPEN,
        nullable=False,
    )
    method: Mapped[AttendanceMethod] = mapped_column(
        enum_column(AttendanceMethod, name="attendance_method"),
        default=AttendanceMethod.WEB,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    closed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    source: Mapped[str | None] = mapped_column(String(40))

    company: Mapped[Company] = relationship(back_populates="attendance_sessions")
    employee: Mapped[Employee] = relationship(back_populates="attendance_sessions")

