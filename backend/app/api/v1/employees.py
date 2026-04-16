from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import ApiContext, require_any_api_permission, require_api_permission
from app.api.v1.errors import not_found, validation_error
from app.api.v1.serializers import user_to_dict
from app.schemas.api_v1 import EmployeeCreateRequest, EmployeeUpdateRequest
from app.services.employee_service import EmployeeService


router = APIRouter(prefix="/employees", tags=["api-employees"])


@router.get("")
async def list_employees(
    ctx: ApiContext = Depends(
        require_any_api_permission("employees:view", "employees:manage")
    ),
) -> dict:
    employees = EmployeeService(business_id=ctx.active_business_id).list_employees()
    return {"items": [user_to_dict(employee) for employee in employees]}


@router.post("")
async def create_employee(
    payload: EmployeeCreateRequest,
    ctx: ApiContext = Depends(require_api_permission("employees:manage")),
) -> dict:
    try:
        employee_id = EmployeeService(business_id=ctx.active_business_id).create_employee(
            first_name=payload.first_name,
            last_name=payload.last_name,
            dni=payload.dni,
            password=payload.password,
            role=payload.role,
            internal_code=payload.internal_code,
            pin_code=payload.pin_code,
            email=payload.email,
            phone=payload.phone,
            role_title=payload.role_title,
            actor_user_id=ctx.user.id,
        )
        employee = EmployeeService(
            business_id=ctx.active_business_id,
        ).employee_repository.get_by_id(employee_id)
    except ValueError as exc:
        raise validation_error(str(exc)) from exc
    return {"employee": user_to_dict(employee)}


@router.get("/{employee_id}")
async def get_employee(
    employee_id: int,
    ctx: ApiContext = Depends(
        require_any_api_permission("employees:view", "employees:manage")
    ),
) -> dict:
    employee = EmployeeService(
        business_id=ctx.active_business_id,
    ).employee_repository.get_by_id(employee_id)
    if employee is None:
        raise not_found("Empleado no encontrado.")
    return {"employee": user_to_dict(employee)}


@router.put("/{employee_id}")
async def update_employee(
    employee_id: int,
    payload: EmployeeUpdateRequest,
    ctx: ApiContext = Depends(require_api_permission("employees:manage")),
) -> dict:
    service = EmployeeService(business_id=ctx.active_business_id)
    try:
        service.update_employee(
            employee_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            dni=payload.dni,
            role=payload.role,
            active=payload.active,
            actor_user_id=ctx.user.id,
        )
    except ValueError as exc:
        raise validation_error(str(exc)) from exc
    employee = service.employee_repository.get_by_id(employee_id)
    if employee is None:
        raise not_found("Empleado no encontrado.")
    return {"employee": user_to_dict(employee)}


@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: int,
    ctx: ApiContext = Depends(require_api_permission("employees:manage")),
) -> dict:
    try:
        EmployeeService(business_id=ctx.active_business_id).remove_employee_from_business(
            employee_id,
            actor_user_id=ctx.user.id,
        )
    except ValueError as exc:
        raise validation_error(str(exc)) from exc
    return {"ok": True, "employee_id": employee_id, "deleted": True}
