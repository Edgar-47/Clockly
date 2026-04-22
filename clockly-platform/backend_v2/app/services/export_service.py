from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.attendance_session import AttendanceSession
from app.models.enums import AttendanceStatus
from app.repositories.attendance_repository import AttendanceRepository


class ExportService:
    """Prepared backend-side export query surface.

    Rendering XLSX/CSV/PDF can build on this without duplicating report queries.
    """

    def __init__(self, db: Session, *, company_id: UUID) -> None:
        self.attendance = AttendanceRepository(db, company_id=company_id)

    def list_exportable_sessions(
        self,
        *,
        employee_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[AttendanceSession]:
        return self.attendance.list_sessions(
            employee_id=employee_id,
            status=AttendanceStatus.CLOSED,
            date_from=date_from,
            date_to=date_to,
            limit=10_000,
        )

