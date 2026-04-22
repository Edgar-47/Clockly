from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import TenantContext, require_permission
from app.models.enums import AttendanceStatus
from app.schemas.attendance import (
    AttendanceSessionListResponse,
    AttendanceSessionRead,
    ClockInRequest,
    ClockOutRequest,
)
from app.services.attendance_service import AttendanceService


router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.get("/sessions", response_model=AttendanceSessionListResponse)
def list_sessions(
    employee_id: UUID | None = Query(default=None),
    session_status: AttendanceStatus | None = Query(default=None, alias="status"),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    ctx: TenantContext = Depends(require_permission("attendance:read")),
    db: Session = Depends(get_db),
) -> AttendanceSessionListResponse:
    sessions = AttendanceService(db, company_id=ctx.company_id).list_sessions(
        employee_id=employee_id,
        status=session_status,
        date_from=date_from,
        date_to=date_to,
    )
    return AttendanceSessionListResponse(items=sessions)


@router.post("/clock-in", response_model=AttendanceSessionRead, status_code=status.HTTP_201_CREATED)
def clock_in(
    payload: ClockInRequest | None = None,
    ctx: TenantContext = Depends(require_permission("attendance:write")),
    db: Session = Depends(get_db),
) -> AttendanceSessionRead:
    payload = payload or ClockInRequest()
    return AttendanceService(db, company_id=ctx.company_id).clock_in(
        actor=ctx.user,
        employee_id=payload.employee_id,
        method=payload.method,
        notes=payload.notes,
    )


@router.post("/clock-out", response_model=AttendanceSessionRead)
def clock_out(
    payload: ClockOutRequest | None = None,
    ctx: TenantContext = Depends(require_permission("attendance:write")),
    db: Session = Depends(get_db),
) -> AttendanceSessionRead:
    payload = payload or ClockOutRequest()
    return AttendanceService(db, company_id=ctx.company_id).clock_out(
        actor=ctx.user,
        employee_id=payload.employee_id,
        session_id=payload.session_id,
        notes=payload.notes,
    )
