"""Tests for TimeClockService — clock-in, clock-out and session integrity."""

import pytest

from app.services.employee_service import EmployeeService
from app.services.time_clock_service import TimeClockService


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_employee(svc: EmployeeService, *, dni: str = "CLKTEST1") -> int:
    return svc.create_employee(
        first_name="Test",
        last_name="Empleado",
        dni=dni,
        password="clave123",
        role="employee",
    )


# ── start_session_for_employee ────────────────────────────────────────────────

def test_clock_in_creates_active_session(db):
    emp_svc = EmployeeService()
    clk_svc = TimeClockService()
    emp_id = _make_employee(emp_svc)

    session = clk_svc.start_session_for_employee(emp_id)

    assert session.user_id == emp_id
    assert session.is_active is True
    assert session.clock_in_time is not None
    assert session.clock_out_time is None


def test_clock_in_twice_returns_same_session(db):
    """A second clock-in while already clocked in must return the existing session."""
    emp_svc = EmployeeService()
    clk_svc = TimeClockService()
    emp_id = _make_employee(emp_svc)

    session1 = clk_svc.start_session_for_employee(emp_id)
    session2 = clk_svc.start_session_for_employee(emp_id)

    assert session1.id == session2.id


def test_clock_in_only_one_active_session_per_user(db):
    """The unique index on attendance_sessions enforces one active session."""
    emp_svc = EmployeeService()
    clk_svc = TimeClockService()
    emp_id = _make_employee(emp_svc)

    clk_svc.start_session_for_employee(emp_id)
    active = clk_svc.get_active_session(emp_id)
    # Force a second raw insert — should be blocked by the unique partial index.
    from app.database.connection import get_connection
    with pytest.raises(Exception):
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO attendance_sessions (user_id, clock_in_time, is_active) VALUES (?, ?, 1)",
                (emp_id, "2025-01-01 10:00:00"),
            )
    # Existing session unchanged.
    assert clk_svc.get_active_session(emp_id).id == active.id


def test_clock_in_admin_raises(db):
    """Admins cannot clock in."""
    clk_svc = TimeClockService()
    from app.database.employee_repository import EmployeeRepository
    repo = EmployeeRepository()
    admin = repo.get_by_identifier("admin")
    with pytest.raises(ValueError, match="Solo los empleados"):
        clk_svc.start_session_for_employee(admin.id)


def test_clock_in_inactive_employee_raises(db):
    emp_svc = EmployeeService()
    clk_svc = TimeClockService()
    emp_id = _make_employee(emp_svc)
    emp_svc.toggle_active(emp_id)       # deactivate

    with pytest.raises(ValueError, match="inactivo"):
        clk_svc.start_session_for_employee(emp_id)


# ── clock_out_employee ────────────────────────────────────────────────────────

def test_clock_out_closes_session(db):
    emp_svc = EmployeeService()
    clk_svc = TimeClockService()
    emp_id = _make_employee(emp_svc)

    clk_svc.start_session_for_employee(emp_id)
    closed = clk_svc.clock_out_employee(emp_id)

    assert closed.is_active is False
    assert closed.clock_out_time is not None
    assert closed.total_seconds is not None
    assert closed.total_seconds >= 0


def test_clock_out_no_active_session_raises(db):
    emp_svc = EmployeeService()
    clk_svc = TimeClockService()
    emp_id = _make_employee(emp_svc)

    with pytest.raises(ValueError, match="sesion activa"):
        clk_svc.clock_out_employee(emp_id)


def test_clock_out_clears_active_session(db):
    emp_svc = EmployeeService()
    clk_svc = TimeClockService()
    emp_id = _make_employee(emp_svc)

    clk_svc.start_session_for_employee(emp_id)
    clk_svc.clock_out_employee(emp_id)

    assert clk_svc.get_active_session(emp_id) is None


def test_clock_in_after_clock_out_opens_new_session(db):
    emp_svc = EmployeeService()
    clk_svc = TimeClockService()
    emp_id = _make_employee(emp_svc)

    session1 = clk_svc.start_session_for_employee(emp_id)
    clk_svc.clock_out_employee(emp_id)
    session2 = clk_svc.start_session_for_employee(emp_id)

    assert session2.id != session1.id
    assert session2.is_active is True


# ── get_attendance_statuses ───────────────────────────────────────────────────

def test_get_attendance_statuses_reflects_clocked_in(db):
    emp_svc = EmployeeService()
    clk_svc = TimeClockService()
    emp_id = _make_employee(emp_svc)
    clk_svc.start_session_for_employee(emp_id)

    from app.database.employee_repository import EmployeeRepository
    emp = EmployeeRepository().get_by_id(emp_id)
    statuses = clk_svc.get_attendance_statuses([emp])

    assert len(statuses) == 1
    assert statuses[0].is_clocked_in is True


def test_get_attendance_statuses_reflects_clocked_out(db):
    emp_svc = EmployeeService()
    clk_svc = TimeClockService()
    emp_id = _make_employee(emp_svc)

    from app.database.employee_repository import EmployeeRepository
    emp = EmployeeRepository().get_by_id(emp_id)
    statuses = clk_svc.get_attendance_statuses([emp])

    assert statuses[0].is_clocked_in is False


# ── register (facade) ─────────────────────────────────────────────────────────

def test_register_entry_creates_session(db):
    emp_svc = EmployeeService()
    clk_svc = TimeClockService()
    emp_id = _make_employee(emp_svc)

    session_id = clk_svc.register(employee_id=emp_id, entry_type="entrada")
    assert isinstance(session_id, int)
    assert clk_svc.get_active_session(emp_id) is not None


def test_register_exit_closes_session(db):
    emp_svc = EmployeeService()
    clk_svc = TimeClockService()
    emp_id = _make_employee(emp_svc)

    clk_svc.register(employee_id=emp_id, entry_type="entrada")
    clk_svc.register(employee_id=emp_id, entry_type="salida")

    assert clk_svc.get_active_session(emp_id) is None


def test_register_invalid_type_raises(db):
    emp_svc = EmployeeService()
    clk_svc = TimeClockService()
    emp_id = _make_employee(emp_svc)

    with pytest.raises(ValueError, match="Tipo"):
        clk_svc.register(employee_id=emp_id, entry_type="pausa")
