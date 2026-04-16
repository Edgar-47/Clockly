from fastapi.testclient import TestClient


def _app():
    from app.main import app

    return app


def _login(client: TestClient, identifier: str = "admin", password: str = "Admin123"):
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": identifier, "password": password},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    return payload, {"Authorization": f"Bearer {payload['access_token']}"}


def _create_business(client: TestClient, headers: dict) -> tuple[dict, dict]:
    response = client.post(
        "/api/v1/businesses",
        headers=headers,
        json={
            "business_name": "API Cafe",
            "business_type": "cafeteria",
            "login_code": "API-CAFE",
            "plan_code": "pro",
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    auth = payload["auth"]
    return payload["business"], {"Authorization": f"Bearer {auth['access_token']}"}


def test_api_login_me_and_business_switch(db):
    with TestClient(_app()) as client:
        login_payload, headers = _login(client)
        assert login_payload["user"]["global_role"] == "admin"
        assert "access_token" in login_payload

        business, headers = _create_business(client, headers)

        me = client.get("/api/v1/auth/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["active_business_id"] == business["id"]

        listed = client.get("/api/v1/businesses", headers=headers)
        assert listed.status_code == 200
        assert listed.json()["items"][0]["id"] == business["id"]

        switched = client.post(
            "/api/v1/businesses/switch",
            headers=headers,
            json={"business_id": business["id"]},
        )
        assert switched.status_code == 200
        assert switched.json()["auth"]["active_business_id"] == business["id"]


def test_api_employee_crud_and_business_scope(db):
    with TestClient(_app()) as client:
        _, headers = _login(client)
        _, headers = _create_business(client, headers)

        created = client.post(
            "/api/v1/employees",
            headers=headers,
            json={
                "first_name": "Ana",
                "last_name": "Movil",
                "dni": "APIEMP001",
                "password": "clave123",
                "role": "employee",
            },
        )
        assert created.status_code == 200, created.text
        employee_id = created.json()["employee"]["id"]

        listed = client.get("/api/v1/employees", headers=headers)
        assert listed.status_code == 200
        assert any(item["id"] == employee_id for item in listed.json()["items"])

        deleted = client.delete(f"/api/v1/employees/{employee_id}", headers=headers)
        assert deleted.status_code == 200

        listed_after = client.get("/api/v1/employees", headers=headers)
        assert all(item["id"] != employee_id for item in listed_after.json()["items"])


def test_api_employee_can_clock_in_out_and_read_history(db):
    with TestClient(_app()) as client:
        _, admin_headers = _login(client)
        _, admin_headers = _create_business(client, admin_headers)

        created = client.post(
            "/api/v1/employees",
            headers=admin_headers,
            json={
                "first_name": "Luis",
                "last_name": "Flutter",
                "dni": "FLUTTER001",
                "password": "clave123",
                "role": "employee",
            },
        )
        assert created.status_code == 200, created.text

        _, employee_headers = _login(client, "FLUTTER001", "clave123")

        clock_in = client.post(
            "/api/v1/attendance/clock-in",
            headers=employee_headers,
            json={},
        )
        assert clock_in.status_code == 200, clock_in.text
        assert clock_in.json()["session"]["is_active"] is True

        status = client.get("/api/v1/attendance", headers=employee_headers)
        assert status.status_code == 200
        assert status.json()["items"][0]["is_clocked_in"] is True

        clock_out = client.post(
            "/api/v1/attendance/clock-out",
            headers=employee_headers,
            json={"exit_note": "Fin de turno desde API"},
        )
        assert clock_out.status_code == 200, clock_out.text
        assert clock_out.json()["session"]["is_active"] is False

        history = client.get("/api/v1/attendance/history", headers=employee_headers)
        assert history.status_code == 200
        assert len(history.json()["items"]) >= 1
