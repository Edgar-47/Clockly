from fastapi.testclient import TestClient

from app.database.connection import get_connection
from app.services.business_service import BusinessService
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
    business_id: str | None = None,
) -> int:
    return EmployeeService(business_id=business_id).create_employee(
        first_name=first_name,
        last_name=last_name,
        dni=dni,
        password=password,
        role="employee",
    )


def _admin_id() -> int:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id FROM users WHERE LOWER(dni) = LOWER(%s)",
            ("admin",),
        ).fetchone()
    return int(row["id"])


def _create_test_business(owner_id: int, name: str = "Test Business") -> object:
    return BusinessService().create_business(
        owner_user_id=owner_id,
        business_name=name,
        business_type="cafeteria",
        login_code=name.upper().replace(" ", "-"),
        plan_code="pro",
    )


def _insert_session(
    *,
    employee_id: int,
    clock_in: str,
    clock_out: str | None = None,
    is_active: bool = False,
    total_seconds: int | None = None,
    business_id: str | None = None,
) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO attendance_sessions
                (user_id, clock_in_time, clock_out_time, is_active, total_seconds, business_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (employee_id, clock_in, clock_out, is_active, total_seconds, business_id),
        )
        return int(cursor.fetchone()["id"])


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


def test_business_scoped_admin_login_reaches_dashboard_even_if_global_role_is_employee(db):
    owner_id = _admin_id()
    business = BusinessService().create_business(
        owner_user_id=owner_id,
        business_name="Scoped Admin Cafe",
        business_type="cafeteria",
        login_code="SCOPED-ADMIN",
        plan_code="pro",
    )
    scoped_admin_id = EmployeeService(business_id=business.id).create_employee(
        first_name="Bea",
        last_name="Admin",
        dni="BIZADMIN001",
        password="clave123",
        role="admin",
        actor_user_id=owner_id,
    )
    with get_connection() as connection:
        connection.execute(
            "UPDATE users SET role = 'employee' WHERE id = %s",
            (scoped_admin_id,),
        )

    with TestClient(_app()) as client:
        response = client.post(
            "/login",
            data={"identifier": "BIZADMIN001", "password": "clave123"},
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
            SELECT COUNT(*) AS count
            FROM attendance_sessions
            WHERE user_id = %s AND is_active IS TRUE
            """,
            (employee_id,),
        ).fetchone()["count"]

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
    # Sessions must be scoped to a business; the /sessions route requires an
    # active business context and filters by business_id.
    owner_id = _admin_id()
    business = _create_test_business(owner_id, "Filter Test Bar")

    ana_id = _create_employee(
        first_name="Ana", last_name="Lopez", dni="12345678A", business_id=business.id
    )
    luis_id = _create_employee(
        first_name="Luis", last_name="Martin", dni="87654321B", business_id=business.id
    )
    _insert_session(
        employee_id=ana_id,
        clock_in="2026-04-13 09:00:00",
        clock_out="2026-04-13 17:00:00",
        is_active=False,
        total_seconds=28800,
        business_id=business.id,
    )
    _insert_session(
        employee_id=luis_id,
        clock_in="2026-04-14 09:00:00",
        is_active=True,
        business_id=business.id,
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


def test_kiosk_business_switch_resets_context_and_scopes_data(db):
    owner_id = _admin_id()
    business_service = BusinessService()
    first = business_service.create_business(
        owner_user_id=owner_id,
        business_name="Kiosk Norte",
        business_type="cafeteria",
        login_code="KIOSK-NORTE",
        plan_code="pro",
    )
    second = business_service.create_business(
        owner_user_id=owner_id,
        business_name="Kiosk Sur",
        business_type="bar",
        login_code="KIOSK-SUR",
        plan_code="pro",
    )

    EmployeeService(business_id=first.id).create_employee(
        first_name="Ana",
        last_name="Norte",
        dni="NORTE001",
        password="clave123",
    )
    EmployeeService(business_id=second.id).create_employee(
        first_name="Luis",
        last_name="Sur",
        dni="SUR001",
        password="clave123",
    )

    with TestClient(_app()) as client:
        response = client.post(
            "/kiosk/enter",
            data={"login_code": "KIOSK-NORTE"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/kiosk"

        kiosk = client.get("/kiosk")
        assert kiosk.status_code == 200
        assert "Kiosk Norte" in kiosk.text
        assert "Ana" in kiosk.text
        assert "Luis" not in kiosk.text

        login = client.post(
            "/kiosk/login",
            data={"identifier": "NORTE001", "password": "clave123"},
            follow_redirects=False,
        )
        assert login.status_code == 303
        assert login.headers["location"] == "/kiosk/me"

        change = client.post("/kiosk/change", follow_redirects=False)
        assert change.status_code == 303
        assert change.headers["location"] == "/kiosk/enter"

        no_context = client.get("/kiosk", follow_redirects=False)
        assert no_context.status_code == 302
        assert no_context.headers["location"] == "/kiosk/enter"

        response = client.post(
            "/kiosk/enter",
            data={"login_code": "KIOSK-SUR"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/kiosk"

        kiosk = client.get("/kiosk")
        assert kiosk.status_code == 200
        assert "Kiosk Sur" in kiosk.text
        assert "Luis" in kiosk.text
        assert "Ana" not in kiosk.text

        stale_employee = client.get("/kiosk/me", follow_redirects=False)
        assert stale_employee.status_code == 302
        assert stale_employee.headers["location"] == "/kiosk/login"


def test_kiosk_invalid_new_business_code_drops_previous_context(db):
    owner_id = _admin_id()
    business = BusinessService().create_business(
        owner_user_id=owner_id,
        business_name="Kiosk Codigo",
        business_type="tienda",
        login_code="KIOSK-CODIGO",
        plan_code="pro",
    )
    EmployeeService(business_id=business.id).create_employee(
        first_name="Marta",
        last_name="Codigo",
        dni="COD001",
        password="clave123",
    )

    with TestClient(_app()) as client:
        response = client.post(
            "/kiosk/enter",
            data={"login_code": "KIOSK-CODIGO"},
            follow_redirects=False,
        )
        assert response.status_code == 303

        response = client.post(
            "/kiosk/enter",
            data={"login_code": "NO-EXISTE"},
            follow_redirects=False,
        )
        assert response.status_code == 400
        assert "no encontrado" in response.text

        no_context = client.get("/kiosk", follow_redirects=False)
        assert no_context.status_code == 302
        assert no_context.headers["location"] == "/kiosk/enter"
