"""Tests for ExportService — Excel generation from attendance_sessions."""

import pytest
from pathlib import Path

from app.services.employee_service import EmployeeService
from app.services.export_service import ExportService
from app.services.time_clock_service import TimeClockService


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_employee(emp_svc: EmployeeService, *, dni: str = "EXPTEST1") -> int:
    return emp_svc.create_employee(
        first_name="Export",
        last_name="Test",
        dni=dni,
        password="clave123",
        role="employee",
    )


def _patch_exports_dir(tmp_path, monkeypatch):
    """Redirect exports to tmp_path so tests don't write to OneDrive."""
    monkeypatch.setattr("app.services.export_service.EXPORTS_DIR", tmp_path)
    monkeypatch.setattr(
        "app.services.export_service.ensure_runtime_directories", lambda: None
    )


# ── File generation ───────────────────────────────────────────────────────────

def test_export_creates_xlsx_file(db, tmp_path, monkeypatch):
    _patch_exports_dir(tmp_path, monkeypatch)
    emp_svc = EmployeeService()
    clk_svc = TimeClockService()
    exp_svc = ExportService()

    emp_id = _make_employee(emp_svc)
    clk_svc.start_session_for_employee(emp_id)
    clk_svc.clock_out_employee(emp_id)

    path = exp_svc.export_sessions_to_excel()

    assert path.exists()
    assert path.suffix == ".xlsx"


def test_export_empty_db_creates_file_without_data_rows(db, tmp_path, monkeypatch):
    """Export works even with no sessions (header only)."""
    _patch_exports_dir(tmp_path, monkeypatch)
    exp_svc = ExportService()

    path = exp_svc.export_sessions_to_excel()
    assert path.exists()

    from openpyxl import load_workbook
    wb = load_workbook(path)
    ws = wb.active
    # Row 1 is the header; no data rows.
    assert ws.max_row == 1


def test_export_columns_match_sessions(db, tmp_path, monkeypatch):
    """The header row must contain the canonical session columns."""
    _patch_exports_dir(tmp_path, monkeypatch)
    exp_svc = ExportService()

    path = exp_svc.export_sessions_to_excel()

    from openpyxl import load_workbook
    wb = load_workbook(path)
    ws = wb.active
    headers = [ws.cell(row=1, column=c).value for c in range(1, ws.max_column + 1)]

    assert "Empleado" in headers
    assert "DNI" in headers
    assert "Entrada" in headers
    assert "Salida" in headers
    assert "Duración" in headers
    assert "Estado" in headers
    assert "Incidencias" in headers
    assert "Nota salida" in headers
    assert "Motivo cierre admin" in headers


def test_export_data_rows_count(db, tmp_path, monkeypatch):
    """Each complete clock-in/out cycle produces exactly one data row."""
    _patch_exports_dir(tmp_path, monkeypatch)
    emp_svc = EmployeeService()
    clk_svc = TimeClockService()
    exp_svc = ExportService()

    emp_id = _make_employee(emp_svc)
    # Two complete sessions.
    clk_svc.start_session_for_employee(emp_id)
    clk_svc.clock_out_employee(emp_id)
    clk_svc.start_session_for_employee(emp_id)
    clk_svc.clock_out_employee(emp_id)

    path = exp_svc.export_sessions_to_excel()

    from openpyxl import load_workbook
    wb = load_workbook(path)
    ws = wb.active
    # max_row includes the header row.
    assert ws.max_row == 3   # 1 header + 2 sessions


def test_export_open_session_shows_en_curso(db, tmp_path, monkeypatch):
    """A session that has not been closed must appear with 'En curso' duration."""
    _patch_exports_dir(tmp_path, monkeypatch)
    emp_svc = EmployeeService()
    clk_svc = TimeClockService()
    exp_svc = ExportService()

    emp_id = _make_employee(emp_svc)
    clk_svc.start_session_for_employee(emp_id)   # clock in, no clock out

    path = exp_svc.export_sessions_to_excel()

    from openpyxl import load_workbook
    wb = load_workbook(path)
    ws = wb.active

    # Find the Duración column index.
    headers = [ws.cell(row=1, column=c).value for c in range(1, ws.max_column + 1)]
    dur_col = headers.index("Duración") + 1
    duration_value = ws.cell(row=2, column=dur_col).value

    assert duration_value == "En curso"


def test_export_includes_exit_note_and_incident(db, tmp_path, monkeypatch):
    _patch_exports_dir(tmp_path, monkeypatch)
    emp_svc = EmployeeService()
    clk_svc = TimeClockService()
    exp_svc = ExportService()

    emp_id = _make_employee(emp_svc)
    clk_svc.start_session_for_employee(emp_id)
    clk_svc.clock_out_employee(
        emp_id,
        exit_note="Olvido de fichaje avisado",
        incident_type="olvido",
    )

    path = exp_svc.export_sessions_to_excel()

    from openpyxl import load_workbook
    wb = load_workbook(path)
    ws = wb.active
    headers = [ws.cell(row=1, column=c).value for c in range(1, ws.max_column + 1)]

    incident_col = headers.index("Incidencias") + 1
    exit_note_col = headers.index("Nota salida") + 1

    assert ws.cell(row=2, column=incident_col).value == "Olvido"
    assert ws.cell(row=2, column=exit_note_col).value == "Olvido de fichaje avisado"


def test_export_backward_compat_alias(db, tmp_path, monkeypatch):
    """export_time_entries_to_excel() must still work (backward-compat alias)."""
    _patch_exports_dir(tmp_path, monkeypatch)
    exp_svc = ExportService()

    path = exp_svc.export_time_entries_to_excel()
    assert path.exists()
    assert path.suffix == ".xlsx"


def test_export_date_filter(db, tmp_path, monkeypatch):
    """date_from / date_to filters must narrow the result set."""
    _patch_exports_dir(tmp_path, monkeypatch)
    emp_svc = EmployeeService()
    clk_svc = TimeClockService()
    exp_svc = ExportService()

    emp_id = _make_employee(emp_svc)
    clk_svc.start_session_for_employee(emp_id)
    clk_svc.clock_out_employee(emp_id)

    # Filter to an old date range that contains no sessions.
    path = exp_svc.export_sessions_to_excel(date_from="2000-01-01", date_to="2000-12-31")

    from openpyxl import load_workbook
    wb = load_workbook(path)
    ws = wb.active
    assert ws.max_row == 1   # header only — no matching sessions
