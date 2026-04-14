from app.core.flow_debug import flow_log, mask_identifier
from app.database.connection import get_connection
from app.models.employee import Employee


class EmployeeRepository:
    """
    Repository for the canonical `users` table.

    The legacy `employees` table is no longer written to from here.
    It exists in the schema only for migration of old databases (handled
    once at startup by schema.initialize_database).
    """

    _SELECT_COLUMNS = """
        id, first_name, last_name, dni, password_hash, role, active,
        last_business_id, created_at
    """

    def __init__(self, business_id: str | None = None) -> None:
        self.business_id = business_id

    def get_by_identifier(self, identifier: str) -> Employee | None:
        return self.get_by_dni(identifier)

    def get_by_username(self, username: str) -> Employee | None:
        """Backward-compatible alias. Normal users now authenticate by DNI."""
        return self.get_by_dni(username)

    def get_by_dni(self, dni: str) -> Employee | None:
        clean_dni = dni.strip()
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self._SELECT_COLUMNS}
                FROM users
                WHERE LOWER(dni) = LOWER(?)
                """,
                (clean_dni,),
            ).fetchone()
        flow_log(
            "repository.employee.by_dni",
            identifier=mask_identifier(clean_dni),
            found=bool(row),
        )
        return Employee.from_row(row) if row else None

    def get_by_id(self, employee_id: int) -> Employee | None:
        join = ""
        clauses = ["u.id = ?"]
        params: list = [employee_id]
        if self.business_id:
            join = "JOIN business_members bm ON bm.user_id = u.id"
            clauses.append("bm.business_id = ?")
            params.append(self.business_id)

        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self._qualify_select_columns()}
                FROM users u
                {join}
                WHERE {" AND ".join(clauses)}
                """,
                params,
            ).fetchone()
        flow_log(
            "repository.employee.by_id",
            employee_id=employee_id,
            business_id=self.business_id,
            found=bool(row),
        )
        return Employee.from_row(row) if row else None

    def get_by_full_name(self, first_name: str, last_name: str) -> Employee | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self._SELECT_COLUMNS}
                FROM users
                WHERE LOWER(TRIM(first_name)) = LOWER(TRIM(?))
                  AND LOWER(TRIM(last_name)) = LOWER(TRIM(?))
                """,
                (first_name, last_name),
            ).fetchone()
        return Employee.from_row(row) if row else None

    def list_all(self) -> list[Employee]:
        join, where, params = self._business_scope_sql()
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT {self._qualify_select_columns()}
                FROM users u
                {join}
                {where}
                ORDER BY u.active DESC, u.first_name COLLATE NOCASE, u.last_name COLLATE NOCASE
                """,
                params,
            ).fetchall()
        flow_log(
            "repository.employee.list_all",
            business_id=self.business_id,
            count=len(rows),
        )
        return [Employee.from_row(row) for row in rows]

    def list_active(self) -> list[Employee]:
        join, where, params = self._business_scope_sql(extra_clauses=["u.active = 1"])
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT {self._qualify_select_columns()}
                FROM users u
                {join}
                {where}
                ORDER BY u.first_name COLLATE NOCASE, u.last_name COLLATE NOCASE
                """,
                params,
            ).fetchall()
        flow_log(
            "repository.employee.list_active",
            business_id=self.business_id,
            count=len(rows),
        )
        return [Employee.from_row(row) for row in rows]

    def list_active_clockable(self) -> list[Employee]:
        join, where, params = self._business_scope_sql(
            extra_clauses=["u.active = 1", "u.role = 'employee'"]
        )
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT {self._qualify_select_columns()}
                FROM users u
                {join}
                {where}
                ORDER BY u.first_name COLLATE NOCASE, u.last_name COLLATE NOCASE
                """,
                params,
            ).fetchall()
        flow_log(
            "repository.employee.list_active_clockable",
            business_id=self.business_id,
            count=len(rows),
        )
        return [Employee.from_row(row) for row in rows]

    def create(
        self,
        *,
        first_name: str,
        last_name: str,
        dni: str | None = None,
        password_hash: str,
        role: str = "employee",
        active: bool = True,
        username: str | None = None,
        business_id: str | None = None,
    ) -> int:
        clean_dni = (dni or username or "").strip()
        member_business_id = business_id or self.business_id
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO users
                    (first_name, last_name, dni, password_hash, role, active)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    first_name,
                    last_name,
                    clean_dni,
                    password_hash,
                    role,
                    int(active),
                ),
            )
            user_id = int(cursor.lastrowid)
            if member_business_id:
                member_role = "admin" if role == "admin" else "employee"
                connection.execute(
                    """
                    INSERT OR IGNORE INTO business_members
                        (business_id, user_id, member_role)
                    VALUES (?, ?, ?)
                    """,
                    (member_business_id, user_id, member_role),
                )
            return user_id

    def toggle_active(self, employee_id: int) -> bool:
        """Flip the active flag for an employee. Returns the new active state."""
        with get_connection() as connection:
            connection.execute(
                "UPDATE users SET active = 1 - active WHERE id = ?",
                (employee_id,),
            )
            row = connection.execute(
                "SELECT active FROM users WHERE id = ?",
                (employee_id,),
            ).fetchone()
        return bool(row["active"]) if row else False

    def set_active(self, employee_id: int, *, active: bool) -> None:
        with get_connection() as connection:
            connection.execute(
                "UPDATE users SET active = ? WHERE id = ?",
                (int(active), employee_id),
            )

    def update(
        self,
        employee_id: int,
        *,
        first_name: str,
        last_name: str,
        dni: str,
        role: str,
        active: bool,
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE users
                SET first_name = ?,
                    last_name = ?,
                    dni = ?,
                    role = ?,
                    active = ?
                WHERE id = ?
                """,
                (first_name, last_name, dni, role, int(active), employee_id),
            )

    def set_password_hash(self, employee_id: int, password_hash: str) -> None:
        with get_connection() as connection:
            connection.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (password_hash, employee_id),
            )

    def count_active_admins(self) -> int:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'admin' AND active = 1"
            ).fetchone()
        return int(row[0]) if row else 0

    def _business_scope_sql(
        self,
        *,
        extra_clauses: list[str] | None = None,
    ) -> tuple[str, str, list]:
        join = ""
        clauses = list(extra_clauses or [])
        params: list = []
        if self.business_id:
            join = "JOIN business_members bm ON bm.user_id = u.id"
            clauses.append("bm.business_id = ?")
            params.append(self.business_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return join, where, params

    def _qualify_select_columns(self) -> str:
        return """
            u.id, u.first_name, u.last_name, u.dni, u.password_hash, u.role,
            u.active, u.last_business_id, u.created_at
        """
