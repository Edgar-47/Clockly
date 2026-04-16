from app.database.connection import get_connection
from app.models.saas_employee import SaaSEmployee


class SaaSEmployeeRepository:
    _SELECT = """
        id, business_id, user_id, internal_code, pin_code, first_name, last_name,
        email, phone, role_title, is_active, created_at, updated_at
    """

    def create_for_user(
        self,
        *,
        business_id: str,
        user_id: int,
        internal_code: str,
        password_hash: str,
        first_name: str,
        last_name: str,
        email: str | None = None,
        phone: str | None = None,
        role_title: str | None = None,
        pin_code: str | None = None,
        is_active: bool = True,
    ) -> SaaSEmployee:
        full_name = f"{first_name} {last_name}".strip()
        with get_connection() as connection:
            row = connection.execute(
                """
                INSERT INTO employees (
                    business_id, user_id, internal_code, pin_code,
                    first_name, last_name, name, username, password_hash,
                    role, email, phone, role_title, active, is_active
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                        'employee', %s, %s, %s, %s, %s)
                RETURNING id, business_id, user_id, internal_code, pin_code,
                          first_name, last_name, email, phone, role_title,
                          is_active, created_at, updated_at
                """,
                (
                    business_id,
                    user_id,
                    internal_code,
                    pin_code,
                    first_name,
                    last_name,
                    full_name,
                    f"{business_id}:{internal_code}",
                    password_hash,
                    email,
                    phone,
                    role_title,
                    is_active,
                    is_active,
                ),
            ).fetchone()
        return SaaSEmployee.from_row(row)

    def count_active_for_business(self, business_id: str) -> int:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM business_users bu
                JOIN users u ON u.id = bu.user_id
                WHERE bu.business_id = %s
                  AND bu.role = 'employee'
                  AND bu.status = 'active'
                  AND u.active IS TRUE
                """,
                (business_id,),
            ).fetchone()
        return int(row["count"]) if row else 0

    def get_by_user_id(self, *, business_id: str, user_id: int) -> SaaSEmployee | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self._SELECT}
                FROM employees
                WHERE business_id = %s AND user_id = %s
                LIMIT 1
                """,
                (business_id, user_id),
            ).fetchone()
        return SaaSEmployee.from_row(row) if row else None
