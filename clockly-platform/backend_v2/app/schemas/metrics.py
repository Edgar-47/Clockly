from uuid import UUID

from pydantic import BaseModel


class EmployeeHoursSummary(BaseModel):
    employee_id: UUID
    employee_name: str
    worked_seconds: int
    closed_sessions: int


class MetricsOverview(BaseModel):
    worked_seconds: int
    open_sessions: int
    active_employees: int
    employees: list[EmployeeHoursSummary]

