from fastapi.testclient import TestClient

from app.database.connection import get_connection
from app.services.employee_service import EmployeeService


def _app():
    from app.main import app

    return app


def _create_employee(
    *,
    first_name: str = "Ana",
    last_name: str = "Lopez",
    dni: str = "12345678A",
    password: str = "segura123",
) -> int:
    return EmployeeService().create_employee(
        first_name=first_name,
        last_name=last_name,
        dni=dni,
        password=password,
        role="employee",
    )


def _insert_session(
    *,
    employee_id: int,
    clock_in: str,
    clock_out: str | None = None,
    is_active: bool = False,
    total_seconds: int | None = None,
) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO attendance_sessions
                (user_id, clock_in_time, clock_out_time, is_active, total_seconds)
            VALUES (?, ?, ?, ?, ?)
            """,
            (employee_id, clock_in, clock_out, int(is_active), total_seconds),
        )
        return int(cursor.lastrowid)


def test_admin_login_reaches_dashboard(db):
    with TestClient(_app()) as client:
        response = client.post(
            "/login",
            data={"identifier": "admin", "password": "Admin123"},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/dashboard"
        assert client.get("/dashboard").status_code == 200


def test_employee_login_reaches_own_flow_and_can_punch(db):
    employee_id = _create_employee()

    with TestClient(_app()) as client:
        response = client.post(
            "/login",
            data={"identifier": "12345678A", "password": "segura123"},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/me"

        portal = client.get("/me")
        assert portal.status_code == 200
        assert "Ana Lopez" in portal.text

        punch = client.post("/me/punch", data={}, follow_redirects=False)
        assert punch.status_code == 303
        assert punch.headers["location"] == "/me"

    with get_connection() as connection:
        active = connection.execute(
            """
            SELECT COUNT(*)
            FROM attendance_sessions
            WHERE user_id = ? AND is_active = 1
            """,
            (employee_id,),
        ).fetchone()[0]

    assert active == 1


def test_employee_admin_route_redirects_to_employee_flow(db):
    _create_employee()

    with TestClient(_app()) as client:
        client.post(
            "/login",
            data={"identifier": "12345678A", "password": "segura123"},
            follow_redirects=False,
        )
        response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/me"


def test_session_filters_accept_blank_values_and_filter_results(db):
    ana_id = _create_employee(first_name="Ana", last_name="Lopez", dni="12345678A")
    luis_id = _create_employee(first_name="Luis", last_name="Martin", dni="87654321B")
    _insert_session(
        employee_id=ana_id,
        clock_in="2026-04-13 09:00:00",
        clock_out="2026-04-13 17:00:00",
        is_active=False,
        total_seconds=28800,
    )
    _insert_session(
        employee_id=luis_id,
        clock_in="2026-04-14 09:00:00",
        is_active=True,
    )

    with TestClient(_app()) as client:
        client.post(
            "/login",
            data={"identifier": "admin", "password": "Admin123"},
            follow_redirects=False,
        )

        blank = client.get(
            "/sessions?date_from=&date_to=&employee_id=&is_active=&incident_filter=all"
        )
        assert blank.status_code == 200

        filtered = client.get(
            "/sessions"
            "?date_from=2026-04-13"
            "&date_to=2026-04-13"
            f"&employee_id={ana_id}"
            "&is_active=0"
            "&incident_filter=all"
        )

    assert filtered.status_code == 200
    assert "Ana Lopez" in filtered.text
    assert "87654321B" not in filtered.text
