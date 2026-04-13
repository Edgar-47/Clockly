from app.database.connection import get_connection
from app.models.employee import Employee


class EmployeeRepository:
    _SELECT_COLUMNS = """
        id, first_name, last_name, dni, password_hash, role, active, created_at
    """

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
        return Employee.from_row(row) if row else None

    def get_by_id(self, employee_id: int) -> Employee | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self._SELECT_COLUMNS}
                FROM users
                WHERE id = ?
                """,
                (employee_id,),
            ).fetchone()
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
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT {self._SELECT_COLUMNS}
                FROM users
                ORDER BY active DESC, first_name COLLATE NOCASE, last_name COLLATE NOCASE
                """
            ).fetchall()
        return [Employee.from_row(row) for row in rows]

    def list_active(self) -> list[Employee]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT {self._SELECT_COLUMNS}
                FROM users
                WHERE active = 1
                ORDER BY first_name COLLATE NOCASE, last_name COLLATE NOCASE
                """
            ).fetchall()
        return [Employee.from_row(row) for row in rows]

    def list_active_clockable(self) -> list[Employee]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT {self._SELECT_COLUMNS}
                FROM users
                WHERE active = 1 AND role = 'employee'
                ORDER BY first_name COLLATE NOCASE, last_name COLLATE NOCASE
                """
            ).fetchall()
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
    ) -> int:
        clean_dni = (dni or username or "").strip()
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
            self._sync_legacy_employee(connection, user_id)
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
            self._sync_legacy_employee(connection, employee_id)
        return bool(row["active"]) if row else False

    def set_active(self, employee_id: int, *, active: bool) -> None:
        with get_connection() as connection:
            connection.execute(
                "UPDATE users SET active = ? WHERE id = ?",
                (int(active), employee_id),
            )
            self._sync_legacy_employee(connection, employee_id)

    def _sync_legacy_employee(self, connection, user_id: int) -> None:
        row = connection.execute(
            """
            SELECT id, first_name, last_name, dni, password_hash, role, active, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
        if not row:
            return

        name = f"{row['first_name']} {row['last_name']}".strip()
        connection.execute(
            """
            INSERT OR IGNORE INTO employees
                (id, first_name, last_name, name, username, password_hash, role, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP))
            """,
            (
                row["id"],
                row["first_name"],
                row["last_name"],
                name,
                row["dni"],
                row["password_hash"],
                row["role"],
                row["active"],
                row["created_at"],
            ),
        )
        connection.execute(
            """
            UPDATE employees
            SET first_name = ?,
                last_name = ?,
                name = ?,
                username = ?,
                password_hash = ?,
                role = ?,
                active = ?
            WHERE id = ?
            """,
            (
                row["first_name"],
                row["last_name"],
                name,
                row["dni"],
                row["password_hash"],
                row["role"],
                row["active"],
                row["id"],
            ),
        )
