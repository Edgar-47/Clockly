from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.attendance_session import AttendanceSession
    from app.models.employee import Employee
    from app.models.ticket import Ticket
    from app.models.user import User


class Company(TimestampMixin, Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    business_type: Mapped[str | None] = mapped_column(String(80))
    timezone: Mapped[str] = mapped_column(String(80), default="Europe/Madrid", nullable=False)
    country: Mapped[str | None] = mapped_column(String(80))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[list[User]] = relationship(back_populates="company", cascade="all, delete-orphan")
    employees: Mapped[list[Employee]] = relationship(back_populates="company", cascade="all, delete-orphan")
    attendance_sessions: Mapped[list[AttendanceSession]] = relationship(back_populates="company")
    tickets: Mapped[list[Ticket]] = relationship(back_populates="company")

