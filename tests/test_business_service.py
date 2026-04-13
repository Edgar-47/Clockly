import pytest

from app.database.connection import get_connection
from app.services.business_service import BusinessService
from app.services.employee_service import EmployeeService
from app.services.time_clock_service import TimeClockService


def _admin_id() -> int:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id FROM users WHERE dni = 'admin'"
        ).fetchone()
    return int(row["id"])


def test_admin_requires_onboarding_until_business_exists(db):
    svc = BusinessService()
    admin_id = _admin_id()

    assert svc.requires_onboarding(admin_id) is True

    svc.create_business(
        owner_user_id=admin_id,
        business_name="Restaurante Central",
        business_type="restaurante",
        login_code="CENTRAL",
    )

    assert svc.requires_onboarding(admin_id) is False


def test_create_business_generates_id_and_membership(db):
    svc = BusinessService()
    admin_id = _admin_id()

    business = svc.create_business(
        owner_user_id=admin_id,
        business_name="Cafe Norte",
        business_type="cafeteria",
        login_code="cafe-norte",
    )

    assert business.id
    assert business.short_id
    assert business.owner_user_id == admin_id
    assert business.business_type == "cafeteria"
    assert business.login_code == "CAFE-NORTE"

    businesses = svc.list_businesses_for_user(admin_id)
    assert [b.id for b in businesses] == [business.id]

    with get_connection() as connection:
        member = connection.execute(
            """
            SELECT member_role
            FROM business_members
            WHERE business_id = ? AND user_id = ?
            """,
            (business.id, admin_id),
        ).fetchone()
        user = connection.execute(
            "SELECT last_business_id FROM users WHERE id = ?",
            (admin_id,),
        ).fetchone()

    assert member["member_role"] == "owner"
    assert user["last_business_id"] == business.id


def test_login_code_must_be_unique_for_active_businesses(db):
    svc = BusinessService()
    admin_id = _admin_id()

    svc.create_business(
        owner_user_id=admin_id,
        business_name="Bar Uno",
        business_type="bar",
        login_code="MISMO",
    )

    with pytest.raises(ValueError, match="codigo"):
        svc.create_business(
            owner_user_id=admin_id,
            business_name="Bar Dos",
            business_type="bar",
            login_code="mismo",
        )


def test_business_context_scopes_created_employees_and_sessions(db):
    business_svc = BusinessService()
    admin_id = _admin_id()
    first = business_svc.create_business(
        owner_user_id=admin_id,
        business_name="Tienda Centro",
        business_type="tienda",
        login_code="CENTRO",
    )
    second = business_svc.create_business(
        owner_user_id=admin_id,
        business_name="Tienda Norte",
        business_type="tienda",
        login_code="NORTE",
    )

    first_employee_svc = EmployeeService(business_id=first.id)
    second_employee_svc = EmployeeService(business_id=second.id)

    first_emp = first_employee_svc.create_employee(
        first_name="Ana",
        last_name="Lopez",
        dni="11111111A",
        password="clave123",
    )
    second_emp = second_employee_svc.create_employee(
        first_name="Luis",
        last_name="Perez",
        dni="22222222B",
        password="clave123",
    )

    first_names = [employee.full_name for employee in first_employee_svc.list_employees()]
    second_names = [employee.full_name for employee in second_employee_svc.list_employees()]

    assert "Ana Lopez" in first_names
    assert "Luis Perez" not in first_names
    assert "Luis Perez" in second_names
    assert "Ana Lopez" not in second_names

    clock = TimeClockService(business_id=first.id)
    session = clock.start_session_for_employee(first_emp)

    assert session.business_id == first.id

    with pytest.raises(ValueError, match="inactivo|no valido"):
        TimeClockService(business_id=second.id).start_session_for_employee(first_emp)
