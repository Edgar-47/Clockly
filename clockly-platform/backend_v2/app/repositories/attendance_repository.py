from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.attendance_session import AttendanceSession
from app.models.employee import Employee
from app.models.enums import AttendanceStatus


class AttendanceRepository:
    def __init__(self, db: Session, *, company_id: UUID) -> None:
        self.db = db
        self.company_id = company_id

    def list_sessions(
        self,
        *,
        employee_id: UUID | None = None,
        status: AttendanceStatus | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 100,
    ) -> list[AttendanceSession]:
        statement: Select[tuple[AttendanceSession]] = select(AttendanceSession).where(
            AttendanceSession.company_id == self.company_id
        )
        if employee_id:
            statement = statement.where(AttendanceSession.employee_id == employee_id)
        if status:
            statement = statement.where(AttendanceSession.status == status)
        if date_from:
            statement = statement.where(AttendanceSession.clock_in >= date_from)
        if date_to:
            statement = statement.where(AttendanceSession.clock_in <= date_to)
        statement = statement.order_by(AttendanceSession.clock_in.desc()).limit(limit)
        return list(self.db.scalars(statement))

    def get(self, session_id: UUID) -> AttendanceSession | None:
        return self.db.scalar(
            select(AttendanceSession).where(
                AttendanceSession.id == session_id,
                AttendanceSession.company_id == self.company_id,
            )
        )

    def get_open_for_employee(self, employee_id: UUID, *, lock: bool = False) -> AttendanceSession | None:
        statement = select(AttendanceSession).where(
            AttendanceSession.company_id == self.company_id,
            AttendanceSession.employee_id == employee_id,
            AttendanceSession.status == AttendanceStatus.OPEN,
        )
        if lock:
            statement = statement.with_for_update()
        return self.db.scalar(statement)

    def add(self, session: AttendanceSession) -> AttendanceSession:
        self.db.add(session)
        self.db.flush()
        return session

    def worked_seconds_by_employee(
        self,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[tuple[UUID, str, int, int]]:
        statement = (
            select(
                Employee.id,
                func.concat(Employee.first_name, " ", Employee.last_name).label("employee_name"),
                func.coalesce(func.sum(AttendanceSession.duration_seconds), 0).label("worked_seconds"),
                func.count(AttendanceSession.id).label("closed_sessions"),
            )
            .join(AttendanceSession, AttendanceSession.employee_id == Employee.id)
            .where(
                AttendanceSession.company_id == self.company_id,
                AttendanceSession.status == AttendanceStatus.CLOSED,
            )
            .group_by(Employee.id, Employee.first_name, Employee.last_name)
            .order_by(func.coalesce(func.sum(AttendanceSession.duration_seconds), 0).desc())
        )
        if date_from:
            statement = statement.where(AttendanceSession.clock_in >= date_from)
        if date_to:
            statement = statement.where(AttendanceSession.clock_in <= date_to)
        return [(row[0], row[1], int(row[2] or 0), int(row[3] or 0)) for row in self.db.execute(statement).all()]

    def count_open_sessions(self) -> int:
        return int(
            self.db.scalar(
                select(func.count(AttendanceSession.id)).where(
                    AttendanceSession.company_id == self.company_id,
                    AttendanceSession.status == AttendanceStatus.OPEN,
                )
            )
            or 0
        )

    def sum_worked_seconds(
        self,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int:
        statement = select(func.coalesce(func.sum(AttendanceSession.duration_seconds), 0)).where(
            AttendanceSession.company_id == self.company_id,
            AttendanceSession.status == AttendanceStatus.CLOSED,
        )
        if date_from:
            statement = statement.where(AttendanceSession.clock_in >= date_from)
        if date_to:
            statement = statement.where(AttendanceSession.clock_in <= date_to)
        return int(self.db.scalar(statement) or 0)

    def count_active_employees(self) -> int:
        return int(
            self.db.scalar(
                select(func.count(Employee.id)).where(
                    Employee.company_id == self.company_id,
                    Employee.is_active.is_(True),
                )
            )
            or 0
        )
