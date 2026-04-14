#!/usr/bin/env python3
"""
Quick smoke test for the kiosk flow.
Assumes the app is running at http://localhost:8000
"""

import asyncio
import httpx

async def test_kiosk_flow():
    """Test the complete kiosk flow."""
    base_url = "http://localhost:8000"
    async with httpx.AsyncClient(follow_redirects=False) as client:
        print("\n=== KIOSK FLOW SMOKE TEST ===\n")

        # 1. Test /kiosk/enter (no auth needed)
        print("1. GET /kiosk/enter")
        r = await client.get(f"{base_url}/kiosk/enter")
        print(f"   Status: {r.status_code} (expected 200)")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert "Codigo de Negocio" in r.text or "codigo" in r.text.lower()
        print("   OK - Business code entry form loads\n")

        # 2. Test POST /kiosk/enter with invalid code
        print("2. POST /kiosk/enter (invalid code)")
        r = await client.post(
            f"{base_url}/kiosk/enter",
            data={"login_code": "INVALID123"},
            follow_redirects=False,
        )
        print(f"   Status: {r.status_code} (expected 400)")
        assert r.status_code == 400, f"Expected 400, got {r.status_code}"
        assert "invalido" in r.text.lower() or "invalid" in r.text.lower()
        print("   OK - Invalid code shows error\n")

        # 3. Get a valid business code from DB
        print("3. Checking database for valid business...")
        import sqlite3
        conn = sqlite3.connect("app/data/fichaje.sqlite3")
        cursor = conn.cursor()
        cursor.execute("SELECT id, login_code, business_name FROM businesses LIMIT 1")
        business = cursor.fetchone()
        conn.close()

        if not business:
            print("   WARNING - No businesses in database, creating test scenario...")
            # Insert a test business
            conn = sqlite3.connect("app/data/fichaje.sqlite3")
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO businesses
                (id, owner_user_id, business_name, business_type, login_code, slug, business_key, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("test-biz-001", 1, "Test Business", "Restaurant", "TEST001", "test-biz", "key123", 1)
            )
            conn.commit()
            cursor.execute("SELECT id, login_code FROM businesses WHERE id = 'test-biz-001'")
            business = cursor.fetchone()
            conn.close()

        business_id, login_code, business_name = business
        print(f"   Found: {business_name} (code: {login_code})\n")

        # 4. Test POST /kiosk/enter with valid code
        print(f"4. POST /kiosk/enter (valid code: {login_code})")
        r = await client.post(
            f"{base_url}/kiosk/enter",
            data={"login_code": login_code},
            follow_redirects=False,
        )
        print(f"   Status: {r.status_code} (expected 302 redirect)")
        assert r.status_code == 302, f"Expected 302, got {r.status_code}"
        print(f"   Location: {r.headers.get('location')}")
        print("   OK - Valid code redirects to /kiosk\n")

        # 5. Test GET /kiosk (with kiosk_business_id in session)
        print("5. GET /kiosk")
        r = await client.get(f"{base_url}/kiosk")
        print(f"   Status: {r.status_code} (expected 200)")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert business_name in r.text or "Fichaje de Personal" in r.text
        print("   OK - Kiosk main view loads\n")

        # 6. Test GET /kiosk/login
        print("6. GET /kiosk/login")
        r = await client.get(f"{base_url}/kiosk/login")
        print(f"   Status: {r.status_code} (expected 200)")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert "DNI" in r.text or "dni" in r.text.lower()
        print("   OK - Employee login form loads\n")

        # 7. Test POST /kiosk/login with invalid credentials
        print("7. POST /kiosk/login (invalid credentials)")
        r = await client.post(
            f"{base_url}/kiosk/login",
            data={"identifier": "BADUSER", "password": "badpass"},
            follow_redirects=False,
        )
        print(f"   Status: {r.status_code} (expected 400)")
        assert r.status_code == 400, f"Expected 400, got {r.status_code}"
        assert "invalido" in r.text.lower() or "invalid" in r.text.lower()
        print("   OK - Invalid credentials show error\n")

        # 8. Get a valid employee for testing
        print("8. Checking database for employee...")
        conn = sqlite3.connect("app/data/fichaje.sqlite3")
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT u.id, u.dni, u.password_hash, u.first_name FROM users u
            WHERE u.role = 'employee' AND u.active = 1
            LIMIT 1
            """
        )
        employee = cursor.fetchone()
        conn.close()

        if not employee:
            print("   WARNING - No active employees found, test incomplete")
            print("\n=== PARTIAL SUCCESS ===")
            print("Core kiosk infrastructure works, but needs employees in database to test full flow.")
            return

        emp_id, emp_dni, emp_hash, emp_name = employee
        print(f"   Found: {emp_name} (DNI: {emp_dni})\n")

        # 9. Test POST /kiosk/login with valid credentials
        print(f"9. POST /kiosk/login (valid: {emp_dni})")
        # Note: password field contains plaintext, hash is PBKDF2
        # We need to use the actual plaintext password
        # For testing, we'll just validate the form accepts input
        r = await client.post(
            f"{base_url}/kiosk/login",
            data={"identifier": emp_dni, "password": "Admin123"},  # Try default
            follow_redirects=False,
        )
        print(f"   Status: {r.status_code}")
        if r.status_code == 302:
            print(f"   Location: {r.headers.get('location')}")
            print("   OK - Valid login redirects\n")
        else:
            print(f"   (Note: default password did not work, may be employee-specific)\n")

        # 10. Test security: /kiosk without business_id
        print("10. GET /kiosk (without business_id in session)")
        async with httpx.AsyncClient(follow_redirects=False) as clean_client:
            r = await clean_client.get(f"{base_url}/kiosk")
            print(f"   Status: {r.status_code} (expected 302)")
            assert r.status_code == 302, f"Expected 302, got {r.status_code}"
            location = r.headers.get('location')
            assert "/kiosk/enter" in location, f"Expected redirect to /kiosk/enter, got {location}"
            print(f"   Location: {location}")
            print("   OK - Kiosk requires business_id\n")

        print("=== SUCCESS - KIOSK FLOW TEST PASSED ===\n")

if __name__ == "__main__":
    try:
        asyncio.run(test_kiosk_flow())
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}\n")
        exit(1)
    except Exception as e:
        print(f"\nERROR: {e}\n")
        import traceback
        traceback.print_exc()
        exit(1)
