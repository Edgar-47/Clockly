"""Tests for EmployeeService — CRUD and validation."""

import pytest

from app.services.employee_service import EmployeeService


# ── create_employee ───────────────────────────────────────────────────────────

def test_create_employee_returns_id(db):
    svc = EmployeeService()
    emp_id = svc.create_employee(
        first_name="Luis",
        last_name="Martínez",
        dni="99887766B",
        password="clave123",
    )
    assert isinstance(emp_id, int)
    assert emp_id > 0


def test_create_employee_persisted(db):
    svc = EmployeeService()
    svc.create_employee(
        first_name="Carla",
        last_name="López",
        dni="11223344C",
        password="clave123",
    )
    employees = svc.list_employees()
    names = [e.full_name for e in employees]
    assert "Carla López" in names


def test_create_employee_missing_first_name_raises(db):
    svc = EmployeeService()
    with pytest.raises(ValueError, match="nombre"):
        svc.create_employee(
            first_name="",
            last_name="López",
            dni="11223344C",
            password="clave123",
        )


def test_create_employee_missing_last_name_raises(db):
    svc = EmployeeService()
    with pytest.raises(ValueError, match="apellido"):
        svc.create_employee(
            first_name="Carla",
            last_name="",
            dni="11223344C",
            password="clave123",
        )


def test_create_employee_missing_dni_raises(db):
    svc = EmployeeService()
    with pytest.raises(ValueError, match="DNI"):
        svc.create_employee(
            first_name="Carla",
            last_name="López",
            dni="",
            password="clave123",
        )


def test_create_employee_short_password_raises(db):
    svc = EmployeeService()
    with pytest.raises(ValueError, match="contrase"):
        svc.create_employee(
            first_name="Carla",
            last_name="López",
            dni="11223344C",
            password="abc",
        )


def test_create_employee_duplicate_dni_raises(db):
    svc = EmployeeService()
    svc.create_employee(
        first_name="Carla",
        last_name="López",
        dni="11223344C",
        password="clave123",
    )
    with pytest.raises(ValueError, match="DNI"):
        svc.create_employee(
            first_name="Otro",
            last_name="Apellido",
            dni="11223344C",
            password="clave456",
        )


def test_create_employee_dni_normalised_uppercase(db):
    """DNI is stored uppercase; duplicate check is case-insensitive."""
    svc = EmployeeService()
    svc.create_employee(
        first_name="Pedro",
        last_name="Ruiz",
        dni="55667788d",
        password="clave123",
    )
    with pytest.raises(ValueError, match="DNI"):
        svc.create_employee(
            first_name="Pedro",
            last_name="Ruiz",
            dni="55667788D",     # same, uppercase
            password="clave123",
        )


def test_create_employee_invalid_role_raises(db):
    svc = EmployeeService()
    with pytest.raises(ValueError, match="Rol"):
        svc.create_employee(
            first_name="A",
            last_name="B",
            dni="ROLTEST1",
            password="clave123",
            role="superadmin",
        )


# ── list_employees ────────────────────────────────────────────────────────────

def test_list_employees_includes_admin(db):
    """Default admin is always present after initialize_database."""
    svc = EmployeeService()
    employees = svc.list_employees()
    roles = [e.role for e in employees]
    assert "admin" in roles


def test_list_clockable_excludes_admin(db):
    svc = EmployeeService()
    svc.create_employee(
        first_name="Trabajador",
        last_name="Uno",
        dni="WORKER001",
        password="clave123",
        role="employee",
    )
    clockable = svc.list_clockable_employees()
    assert all(e.role == "employee" for e in clockable)


# ── toggle_active ─────────────────────────────────────────────────────────────

def test_toggle_active_deactivates_and_reactivates(db):
    svc = EmployeeService()
    emp_id = svc.create_employee(
        first_name="Temporal",
        last_name="Trabajador",
        dni="TEMP0001A",
        password="clave123",
    )

    new_state = svc.toggle_active(emp_id)
    assert new_state is False

    new_state = svc.toggle_active(emp_id)
    assert new_state is True
