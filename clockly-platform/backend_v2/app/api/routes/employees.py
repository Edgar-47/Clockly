from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import TenantContext, require_permission
from app.schemas.employee import EmployeeCreate, EmployeeListResponse, EmployeeRead, EmployeeUpdate
from app.services.employee_service import EmployeeService


router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=EmployeeListResponse)
def list_employees(
    include_inactive: bool = Query(default=False),
    ctx: TenantContext = Depends(require_permission("employees:read")),
    db: Session = Depends(get_db),
) -> EmployeeListResponse:
    employees = EmployeeService(db, company_id=ctx.company_id).list_employees(
        include_inactive=include_inactive
    )
    return EmployeeListResponse(items=employees)


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreate,
    ctx: TenantContext = Depends(require_permission("employees:write")),
    db: Session = Depends(get_db),
) -> EmployeeRead:
    return EmployeeService(db, company_id=ctx.company_id).create_employee(payload)


@router.patch("/{employee_id}", response_model=EmployeeRead)
def update_employee(
    employee_id: UUID,
    payload: EmployeeUpdate,
    ctx: TenantContext = Depends(require_permission("employees:write")),
    db: Session = Depends(get_db),
) -> EmployeeRead:
    return EmployeeService(db, company_id=ctx.company_id).update_employee(employee_id, payload)

