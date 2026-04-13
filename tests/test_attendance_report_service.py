from datetime import date, datetime

from app.database.connection import get_connection
from app.services.attendance_report_service import AttendanceReportService
from app.services.employee_service import EmployeeService


def _make_employee(svc: EmployeeService, *, dni: str = "RPTTEST1") -> int:
    return svc.create_employee(
        first_name="Report",
        last_name="User",
        dni=dni,
        password="clave123",
        role="employee",
    )


def _insert_session(
    *,
    employee_id: int,
    clock_in: str,
    clock_out: str | None = None,
    total_seconds: int | None = None,
    is_active: bool = False,
    incident_type: str | None = None,
    exit_note: str | None = None,
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO attendance_sessions
                (
                    user_id,
                    clock_in_time,
                    clock_out_time,
                    is_active,
                    total_seconds,
                    incident_type,
                    exit_note
                )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                employee_id,
                clock_in,
                clock_out,
                int(is_active),
                total_seconds,
                incident_type,
                exit_note,
            ),
        )
        return int(cursor.lastrowid)


def test_current_period_summaries_use_only_closed_sessions(db):
    emp_svc = EmployeeService()
    emp_id = _make_employee(emp_svc)

    _insert_session(
        employee_id=emp_id,
        clock_in="2026-04-13 09:00:00",
        clock_out="2026-04-13 11:00:00",
        total_seconds=7200,
    )
    _insert_session(
        employee_id=emp_id,
        clock_in="2026-04-13 14:00:00",
        clock_out="2026-04-13 17:00:00",
        total_seconds=10800,
    )
    _insert_session(
        employee_id=emp_id,
        clock_in="2026-04-01 10:00:00",
        clock_out="2026-04-01 13:00:00",
        total_seconds=10800,
    )
    _insert_session(
        employee_id=emp_id,
        clock_in="2026-04-13 18:00:00",
        is_active=True,
    )

    summaries = AttendanceReportService().get_current_period_summaries(
        [emp_id],
        today=date(2026, 4, 13),
    )
    summary = summaries[emp_id]

    assert summary.today.total_seconds == 18000
    assert summary.today.shift_count == 2
    assert summary.week.total_seconds == 18000
    assert summary.month.total_seconds == 28800
    assert summary.month.shift_count == 3
    assert summary.month.average_seconds == 9600


def test_daily_summary_splits_overnight_sessions_by_overlap(db):
    emp_svc = EmployeeService()
    emp_id = _make_employee(emp_svc)

    _insert_session(
        employee_id=emp_id,
        clock_in="2026-04-12 23:00:00",
        clock_out="2026-04-13 01:00:00",
        total_seconds=7200,
    )

    summary = AttendanceReportService().get_employee_summary(
        emp_id,
        date_from=date(2026, 4, 13),
        date_to=date(2026, 4, 13),
    )

    assert summary.total_seconds == 3600
    assert summary.shift_count == 0


def test_session_reports_detect_long_shifts_and_previous_day_open_sessions(db):
    emp_svc = EmployeeService()
    emp_id = _make_employee(emp_svc)

    long_id = _insert_session(
        employee_id=emp_id,
        clock_in="2026-04-13 01:00:00",
        clock_out="2026-04-13 12:30:00",
        total_seconds=41400,
    )
    open_id = _insert_session(
        employee_id=emp_id,
        clock_in="2026-04-12 09:00:00",
        is_active=True,
    )

    service = AttendanceReportService()
    reports = service.list_session_reports(
        now=datetime(2026, 4, 13, 12, 0, 0),
    )
    by_id = {report.id: report for report in reports}

    assert by_id[long_id].excess_threshold_hours == 10
    assert by_id[long_id].has_incident is True
    assert by_id[open_id].is_open_from_previous_day is True
    assert by_id[open_id].excess_threshold_hours == 12
    assert by_id[open_id].severity == "critical"

    previous_open = service.list_session_reports(
        incident_filter=AttendanceReportService.INCIDENT_FILTER_PREVIOUS_OPEN,
        now=datetime(2026, 4, 13, 12, 0, 0),
    )
    assert [report.id for report in previous_open] == [open_id]

    excess_12 = service.list_session_reports(
        incident_filter=AttendanceReportService.INCIDENT_FILTER_EXCESS_12,
        now=datetime(2026, 4, 13, 12, 0, 0),
    )
    assert [report.id for report in excess_12] == [open_id]


def test_session_reports_include_exit_incident_context(db):
    emp_svc = EmployeeService()
    emp_id = _make_employee(emp_svc)

    session_id = _insert_session(
        employee_id=emp_id,
        clock_in="2026-04-13 09:00:00",
        clock_out="2026-04-13 11:00:00",
        total_seconds=7200,
        incident_type="olvido",
        exit_note="Olvido de cierre a tiempo",
    )

    report = next(
        report
        for report in AttendanceReportService().list_session_reports()
        if report.id == session_id
    )

    assert "Olvido" in report.incident_labels
    assert "Salida: Olvido de cierre a tiempo" == report.notes_label
