"""
app/api/routes/employees.py

Employee CRUD routes: list, create, edit, toggle active, reset password.
All routes require admin role.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.api.dependencies import flash, require_admin, template_context
from app.core.templates import templates
from app.models.employee import Employee
from app.services.employee_service import EmployeeService

router = APIRouter(prefix="/employees", tags=["employees"])


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@router.get("", response_class=HTMLResponse)
async def employee_list(
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    service = EmployeeService()
    employees = service.list_employees()
    ctx = template_context(request)
    ctx["employees"] = employees
    return templates.TemplateResponse(request, "employees/list.html", ctx)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@router.get("/new", response_class=HTMLResponse)
async def employee_new_form(
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    ctx = template_context(request)
    ctx["form"] = {}
    return templates.TemplateResponse(request, "employees/create.html", ctx)


@router.post("/new")
async def employee_create(
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    form_data = await request.form()
    data = {
        "first_name": str(form_data.get("first_name", "")),
        "last_name": str(form_data.get("last_name", "")),
        "dni": str(form_data.get("dni", "")),
        "password": str(form_data.get("password", "")),
        "role": str(form_data.get("role", "employee")),
    }
    try:
        service = EmployeeService()
        service.create_employee(**data)
        flash(request, "Empleado creado correctamente.", "success")
        return RedirectResponse("/employees", status_code=303)
    except ValueError as exc:
        ctx = template_context(request)
        ctx["error"] = str(exc)
        ctx["form"] = data
        return templates.TemplateResponse(request, "employees/create.html", ctx, status_code=400)


# ---------------------------------------------------------------------------
# Edit
# ---------------------------------------------------------------------------

@router.get("/{employee_id}/edit", response_class=HTMLResponse)
async def employee_edit_form(
    employee_id: int,
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    service = EmployeeService()
    employee = service.employee_repository.get_by_id(employee_id)
    if not employee:
        flash(request, "Empleado no encontrado.", "error")
        return RedirectResponse("/employees", status_code=302)
    ctx = template_context(request)
    ctx["employee"] = employee
    return templates.TemplateResponse(request, "employees/edit.html", ctx)


@router.post("/{employee_id}/edit")
async def employee_update(
    employee_id: int,
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    form_data = await request.form()
    data = {
        "first_name": str(form_data.get("first_name", "")),
        "last_name": str(form_data.get("last_name", "")),
        "dni": str(form_data.get("dni", "")),
        "role": str(form_data.get("role", "employee")),
        # Checkbox: present in form only if checked
        "active": form_data.get("active") is not None,
    }
    try:
        service = EmployeeService()
        service.update_employee(employee_id, **data)
        flash(request, "Empleado actualizado.", "success")
        return RedirectResponse("/employees", status_code=303)
    except ValueError as exc:
        # Reload employee for the form
        service = EmployeeService()
        employee = service.employee_repository.get_by_id(employee_id)
        ctx = template_context(request)
        ctx["error"] = str(exc)
        ctx["employee"] = employee
        ctx["form"] = data
        return templates.TemplateResponse(request, "employees/edit.html", ctx, status_code=400)


# ---------------------------------------------------------------------------
# Toggle active / inactive
# ---------------------------------------------------------------------------

@router.post("/{employee_id}/toggle")
async def employee_toggle(
    employee_id: int,
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    try:
        service = EmployeeService()
        new_state = service.toggle_active(employee_id)
        label = "activado" if new_state else "desactivado"
        flash(request, f"Empleado {label}.", "success")
    except ValueError as exc:
        flash(request, str(exc), "error")
    return RedirectResponse("/employees", status_code=303)


# ---------------------------------------------------------------------------
# Password reset (generates a temporary password)
# ---------------------------------------------------------------------------

@router.post("/{employee_id}/reset-password")
async def employee_reset_password(
    employee_id: int,
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    try:
        service = EmployeeService()
        temp_password = service.reset_password(employee_id)
        flash(
            request,
            f"Contraseña temporal generada: {temp_password} — comunícasela al empleado.",
            "success",
        )
    except ValueError as exc:
        flash(request, str(exc), "error")
    return RedirectResponse("/employees", status_code=303)


# ---------------------------------------------------------------------------
# Set password manually
# ---------------------------------------------------------------------------

@router.post("/{employee_id}/set-password")
async def employee_set_password(
    employee_id: int,
    request: Request,
    current_user: Employee = Depends(require_admin),
):
    form_data = await request.form()
    new_password = str(form_data.get("new_password", ""))
    try:
        service = EmployeeService()
        service.set_password(employee_id, new_password)
        flash(request, "Contraseña actualizada.", "success")
    except ValueError as exc:
        flash(request, str(exc), "error")
    return RedirectResponse(f"/employees/{employee_id}/edit", status_code=303)
