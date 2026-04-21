"""Tests for AuthService — login and password verification."""

import pytest

from app.services.auth_service import AuthService
from app.services.employee_service import EmployeeService


# ── Helpers ───────────────────────────────────────────────────────────────────

def _create_employee(employee_service: EmployeeService, *, dni: str = "12345678A") -> int:
    return employee_service.create_employee(
        first_name="Ana",
        last_name="García",
        dni=dni,
        password="segura123",
        role="employee",
    )


# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_admin_success(db):
    """Default admin seeded by initialize_database can log in."""
    auth = AuthService()
    employee = auth.login("admin", "Admin123")
    assert employee.role == "admin"
    assert employee.dni.lower() == "admin"


def test_login_employee_success(db):
    svc = EmployeeService()
    _create_employee(svc)
    auth = AuthService()
    employee = auth.login("12345678A", "segura123")
    assert employee.full_name == "Ana García"
    assert employee.role == "employee"


def test_login_wrong_password_raises(db):
    svc = EmployeeService()
    _create_employee(svc)
    auth = AuthService()
    with pytest.raises(ValueError, match="incorrectos"):
        auth.login("12345678A", "contraseña_errónea")


def test_login_unknown_identifier_raises(db):
    auth = AuthService()
    with pytest.raises(ValueError, match="incorrectos"):
        auth.login("NOEXISTE", "cualquiera")


def test_login_empty_credentials_raises(db):
    auth = AuthService()
    with pytest.raises(ValueError):
        auth.login("", "")


def test_login_inactive_employee_raises(db):
    svc = EmployeeService()
    emp_id = _create_employee(svc)
    svc.toggle_active(emp_id)          # deactivate
    auth = AuthService()
    with pytest.raises(ValueError, match="incorrectos"):
        auth.login("12345678A", "segura123")


# ── verify_employee_password ──────────────────────────────────────────────────

def test_verify_employee_password_success(db):
    svc = EmployeeService()
    emp_id = _create_employee(svc)
    auth = AuthService()
    employee = auth.verify_employee_password(emp_id, "segura123")
    assert employee.id == emp_id


def test_verify_employee_password_wrong_raises(db):
    svc = EmployeeService()
    emp_id = _create_employee(svc)
    auth = AuthService()
    with pytest.raises(ValueError, match="incorrecta"):
        auth.verify_employee_password(emp_id, "mala")


def test_verify_employee_password_empty_raises(db):
    svc = EmployeeService()
    emp_id = _create_employee(svc)
    auth = AuthService()
    with pytest.raises(ValueError):
        auth.verify_employee_password(emp_id, "")
