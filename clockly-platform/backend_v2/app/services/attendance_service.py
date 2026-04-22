from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, PermissionDenied
from app.models.attendance_session import AttendanceSession
from app.models.enums import AttendanceMethod, AttendanceStatus, UserRole
from app.models.user import User
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.employee_repository import EmployeeRepository


class AttendanceService:
    def __init__(self, db: Session, *, company_id: UUID) -> None:
        self.db = db
        self.company_id = company_id
        self.attendance = AttendanceRepository(db, company_id=company_id)
        self.employees = EmployeeRepository(db, company_id=company_id)

    def list_sessions(
        self,
        *,
        employee_id: UUID | None = None,
        status: AttendanceStatus | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[AttendanceSession]:
        return self.attendance.list_sessions(
            employee_id=employee_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
        )

    def clock_in(
        self,
        *,
        actor: User,
        employee_id: UUID | None,
        method: AttendanceMethod,
        notes: str | None,
    ) -> AttendanceSession:
        employee = self._resolve_employee(actor, employee_id)
        if self.attendance.get_open_for_employee(employee.id, lock=True):
            raise ConflictError("Employee already has an open attendance session.")
        session = AttendanceSession(
            company_id=self.company_id,
            employee_id=employee.id,
            user_id=employee.user_id,
            clock_in=datetime.now(UTC),
            status=AttendanceStatus.OPEN,
            method=method,
            notes=notes,
            created_by_user_id=actor.id,
        )
        try:
            self.attendance.add(session)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Employee already has an open attendance session.") from exc
        return session

    def clock_out(
        self,
        *,
        actor: User,
        employee_id: UUID | None,
        session_id: UUID | None,
        notes: str | None,
    ) -> AttendanceSession:
        if session_id:
            session = self.attendance.get(session_id)
            if session is None:
                raise NotFoundError("Attendance session not found.")
            employee = self.employees.get(session.employee_id)
            if employee is None:
                raise NotFoundError("Employee not found.")
            self._ensure_can_manage_employee(actor, employee.user_id)
        else:
            employee = self._resolve_employee(actor, employee_id)
            session = self.attendance.get_open_for_employee(employee.id, lock=True)
            if session is None:
                raise ConflictError("Employee has no open attendance session.")

        if session.status != AttendanceStatus.OPEN or session.clock_out is not None:
            raise ConflictError("Attendance session is already closed.")

        closed_at = datetime.now(UTC)
        session.clock_out = closed_at
        session.duration_seconds = max(int((closed_at - session.clock_in).total_seconds()), 0)
        session.status = AttendanceStatus.CLOSED
        session.closed_by_user_id = actor.id
        if notes:
            session.notes = notes if not session.notes else f"{session.notes}\n{notes}"
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def _resolve_employee(self, actor: User, employee_id: UUID | None):
        if employee_id:
            employee = self.employees.get_active(employee_id)
            if employee is None:
                raise NotFoundError("Employee not found.")
            self._ensure_can_manage_employee(actor, employee.user_id)
            return employee

        own_employee = self.employees.get_by_user_id(actor.id)
        if own_employee is None:
            raise ConflictError("employee_id is required for users without an employee profile.")
        return own_employee

    def _ensure_can_manage_employee(self, actor: User, employee_user_id: UUID | None) -> None:
        if actor.role in {UserRole.OWNER, UserRole.ADMIN, UserRole.MANAGER}:
            return
        if employee_user_id == actor.id:
            return
        raise PermissionDenied("You cannot manage attendance for this employee.")

