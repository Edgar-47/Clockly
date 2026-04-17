from fastapi.testclient import TestClient

from app.database.connection import get_connection
from app.services.auth_service import AuthService
from app.services.superadmin_bootstrap_service import SuperadminBootstrapService


def _app():
    from app.main import app

    return app


def _bootstrap_superadmin() -> str:
    email = "owner.internal@example.com"
    SuperadminBootstrapService().create_or_update_superadmin(
        email=email,
        full_name="Owner Internal",
        password="SuperSecure123",
    )
    return email


def test_default_admin_is_not_platform_superadmin(db):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT role, platform_role
            FROM users
            WHERE LOWER(dni) = LOWER(%s)
            """,
            ("admin",),
        ).fetchone()

    assert row["role"] == "admin"
    assert row["platform_role"] is None


def test_legacy_default_admin_platform_role_is_demoted(db):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET platform_role = 'superadmin'
            WHERE LOWER(dni) = LOWER(%s)
            """,
            ("admin",),
        )

    from app.database.schema import initialize_database

    initialize_database()

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT role, platform_role
            FROM users
            WHERE LOWER(dni) = LOWER(%s)
            """,
            ("admin",),
        ).fetchone()

    assert row["role"] == "admin"
    assert row["platform_role"] is None


def test_superadmin_bootstrap_does_not_enable_normal_login(db):
    email = _bootstrap_superadmin()

    with get_connection() as connection:
        row = connection.execute(
            "SELECT role, platform_role FROM users WHERE LOWER(email) = LOWER(%s)",
            (email,),
        ).fetchone()

    assert row["role"] == "admin"
    assert row["platform_role"] == "superadmin"

    auth = AuthService()
    try:
        auth.login(email, "SuperSecure123")
    except ValueError as exc:
        assert "incorrectos" in str(exc)
    else:
        raise AssertionError("Superadmin must not authenticate through normal login")


def test_superadmin_panel_uses_separate_login(db):
    email = _bootstrap_superadmin()

    with TestClient(_app()) as client:
        protected = client.get("/superadmin/dashboard", follow_redirects=False)
        assert protected.status_code == 302
        assert protected.headers["location"] == "/superadmin/login"

        normal_admin = client.post(
            "/login",
            data={"identifier": "admin", "password": "Admin123"},
            follow_redirects=False,
        )
        assert normal_admin.status_code == 303
        assert normal_admin.headers["location"] == "/dashboard"

        still_blocked = client.get("/superadmin/dashboard", follow_redirects=False)
        assert still_blocked.status_code == 302
        assert still_blocked.headers["location"] == "/superadmin/login"

        login = client.post(
            "/superadmin/login",
            data={"identifier": email, "password": "SuperSecure123"},
            follow_redirects=False,
        )
        assert login.status_code == 303
        assert login.headers["location"] == "/superadmin/dashboard"

        dashboard = client.get("/superadmin/dashboard")
        assert dashboard.status_code == 200
        assert "Dashboard global" in dashboard.text
