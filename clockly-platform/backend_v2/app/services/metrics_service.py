from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.attendance_repository import AttendanceRepository
from app.schemas.metrics import EmployeeHoursSummary, MetricsOverview


class MetricsService:
    def __init__(self, db: Session, *, company_id: UUID) -> None:
        self.attendance = AttendanceRepository(db, company_id=company_id)

    def overview(
        self,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> MetricsOverview:
        employee_rows = self.attendance.worked_seconds_by_employee(
            date_from=date_from,
            date_to=date_to,
        )
        return MetricsOverview(
            worked_seconds=self.attendance.sum_worked_seconds(
                date_from=date_from,
                date_to=date_to,
            ),
            open_sessions=self.attendance.count_open_sessions(),
            active_employees=self.attendance.count_active_employees(),
            employees=[
                EmployeeHoursSummary(
                    employee_id=employee_id,
                    employee_name=employee_name,
                    worked_seconds=worked_seconds,
                    closed_sessions=closed_sessions,
                )
                for employee_id, employee_name, worked_seconds, closed_sessions in employee_rows
            ],
        )

