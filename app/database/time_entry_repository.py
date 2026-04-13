from app.database.connection import get_connection
from app.models.time_entry import TimeEntry


class TimeEntryRepository:
    def __init__(self, business_id: str | None = None) -> None:
        self.business_id = business_id

    def create(
        self,
        *,
        employee_id: int,
        entry_type: str,
        timestamp: str,
        notes: str | None = None,
    ) -> int:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO time_entries
                    (business_id, employee_id, entry_type, timestamp, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (self.business_id, employee_id, entry_type, timestamp, notes),
            )
            return int(cursor.lastrowid)

    def get_last_for_employee(self, employee_id: int) -> TimeEntry | None:
        clauses = ["employee_id = ?"]
        params: list = [employee_id]
        if self.business_id:
            clauses.append("business_id = ?")
            params.append(self.business_id)

        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id, business_id, employee_id, entry_type, timestamp, notes
                FROM time_entries
                WHERE """ + " AND ".join(clauses) + """
                ORDER BY timestamp DESC, id DESC
                LIMIT 1
                """,
                params,
            ).fetchone()
        return TimeEntry.from_row(row) if row else None

    def get_latest_for_employees(
        self,
        employee_ids: list[int],
    ) -> dict[int, TimeEntry]:
        if not employee_ids:
            return {}

        placeholders = ",".join("?" for _ in employee_ids)
        where_clauses = [f"employee_id IN ({placeholders})"]
        params: list = list(employee_ids)
        if self.business_id:
            where_clauses.append("business_id = ?")
            params.append(self.business_id)
        query = f"""
            SELECT te.id, te.business_id, te.employee_id, te.entry_type, te.timestamp, te.notes
            FROM time_entries te
            JOIN (
                SELECT employee_id, MAX(timestamp || printf('%012d', id)) AS sort_key
                FROM time_entries
                WHERE {" AND ".join(where_clauses)}
                GROUP BY employee_id
            ) latest
              ON latest.employee_id = te.employee_id
             AND latest.sort_key = te.timestamp || printf('%012d', te.id)
        """

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()

        return {row["employee_id"]: TimeEntry.from_row(row) for row in rows}

    def list_with_employee_names(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        employee_id: int | None = None,
    ) -> list[dict]:
        """
        Return time entries joined with employee name.
        All date parameters are YYYY-MM-DD strings (inclusive).
        """
        clauses: list[str] = []
        params: list = []

        if date_from:
            clauses.append("te.timestamp >= ?")
            params.append(date_from + " 00:00:00")

        if date_to:
            clauses.append("te.timestamp <= ?")
            params.append(date_to + " 23:59:59")

        if employee_id is not None:
            clauses.append("te.employee_id = ?")
            params.append(employee_id)

        if self.business_id:
            clauses.append("te.business_id = ?")
            params.append(self.business_id)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        query = f"""
            SELECT
                te.id,
                te.business_id,
                te.employee_id,
                TRIM(COALESCE(u.first_name, '') || ' ' || COALESCE(u.last_name, ''))
                    AS employee_name,
                u.dni AS username,
                te.entry_type,
                te.timestamp,
                te.notes
            FROM time_entries te
            JOIN users u ON u.id = te.employee_id
            {where}
            ORDER BY te.timestamp DESC, te.id DESC
        """

        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()

        return [dict(row) for row in rows]
