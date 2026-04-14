from __future__ import annotations

from datetime import date

from app.database.connection import get_connection
from app.database.sql import normalize_row
from app.models.employee_schedule import EmployeeSchedule
from app.models.schedule_day import ScheduleDay
from app.models.work_schedule import WorkSchedule


class WorkScheduleRepository:

    def __init__(self, business_id: str | None = None) -> None:
        self.business_id = business_id

    # ------------------------------------------------------------------
    # WorkSchedule reads
    # ------------------------------------------------------------------

    def get_by_id(self, schedule_id: int) -> WorkSchedule | None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM work_schedules WHERE id = %s",
                (schedule_id,),
            ).fetchone()
        return WorkSchedule.from_row(row) if row else None

    def list_all(self) -> list[WorkSchedule]:
        clauses = ["1=1"]
        params: list = []
        if self.business_id is not None:
            clauses.append("(business_id = %s OR business_id IS NULL)")
            params.append(self.business_id)
        with get_connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM work_schedules WHERE {' AND '.join(clauses)} ORDER BY name",
                params,
            ).fetchall()
        return [WorkSchedule.from_row(r) for r in rows]

    def list_active(self) -> list[WorkSchedule]:
        clauses = ["is_active IS TRUE"]
        params: list = []
        if self.business_id is not None:
            clauses.append("(business_id = %s OR business_id IS NULL)")
            params.append(self.business_id)
        with get_connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM work_schedules WHERE {' AND '.join(clauses)} ORDER BY name",
                params,
            ).fetchall()
        return [WorkSchedule.from_row(r) for r in rows]

    # ------------------------------------------------------------------
    # WorkSchedule writes
    # ------------------------------------------------------------------

    def create_schedule(
        self,
        *,
        name: str,
        description: str | None = None,
        weekly_hours_target: float | None = None,
    ) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO work_schedules (business_id, name, description, weekly_hours_target)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (self.business_id, name.strip(), description, weekly_hours_target),
            )
            return int(cursor.fetchone()["id"])

    def update_schedule(
        self,
        schedule_id: int,
        *,
        name: str,
        description: str | None = None,
        weekly_hours_target: float | None = None,
        is_active: bool = True,
    ) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE work_schedules
                SET name = %s,
                    description = %s,
                    weekly_hours_target = %s,
                    is_active = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (name.strip(), description, weekly_hours_target, is_active, schedule_id),
            )

    def delete_schedule(self, schedule_id: int) -> None:
        """Soft-delete: mark as inactive instead of hard delete."""
        with get_connection() as conn:
            conn.execute(
                "UPDATE work_schedules SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (schedule_id,),
            )

    # ------------------------------------------------------------------
    # ScheduleDay reads / writes
    # ------------------------------------------------------------------

    def get_days(self, schedule_id: int) -> list[ScheduleDay]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM schedule_days WHERE schedule_id = %s ORDER BY day_of_week",
                (schedule_id,),
            ).fetchall()
        return [ScheduleDay.from_row(r) for r in rows]

    def replace_days(
        self,
        schedule_id: int,
        days: list[dict],
    ) -> None:
        """
        Replace all schedule_days for a schedule atomically.
        Each dict in `days` must have:
          day_of_week, start_time, end_time,
          break_minutes, late_tolerance_minutes, early_leave_tolerance_minutes
        """
        with get_connection() as conn:
            conn.execute("DELETE FROM schedule_days WHERE schedule_id = %s", (schedule_id,))
            for day in days:
                conn.execute(
                    """
                    INSERT INTO schedule_days
                        (schedule_id, day_of_week, start_time, end_time,
                         break_minutes, late_tolerance_minutes, early_leave_tolerance_minutes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        schedule_id,
                        int(day["day_of_week"]),
                        day["start_time"],
                        day["end_time"],
                        int(day.get("break_minutes", 0)),
                        int(day.get("late_tolerance_minutes", 0)),
                        int(day.get("early_leave_tolerance_minutes", 0)),
                    ),
                )

    # ------------------------------------------------------------------
    # EmployeeSchedule reads / writes
    # ------------------------------------------------------------------

    def get_active_assignment(
        self,
        user_id: int,
        reference_date: date | None = None,
    ) -> EmployeeSchedule | None:
        """Return the currently effective assignment for an employee."""
        ref = reference_date or date.today()
        clauses = [
            "user_id = %s",
            "is_active IS TRUE",
            "effective_from <= %s",
            "(effective_to IS NULL OR effective_to >= %s)",
        ]
        params: list = [user_id, ref, ref]
        if self.business_id is not None:
            clauses.append("(business_id = %s OR business_id IS NULL)")
            params.append(self.business_id)

        with get_connection() as conn:
            row = conn.execute(
                f"""
                SELECT es.*,
                       ws.name AS schedule_name,
                       TRIM(COALESCE(u.first_name,'') || ' ' || COALESCE(u.last_name,'')) AS employee_name
                FROM employee_schedules es
                JOIN work_schedules ws ON ws.id = es.schedule_id
                JOIN users u ON u.id = es.user_id
                WHERE {' AND '.join(clauses)}
                ORDER BY effective_from DESC
                LIMIT 1
                """,
                params,
            ).fetchone()
        return EmployeeSchedule.from_row(normalize_row(row)) if row else None

    def list_assignments_for_user(self, user_id: int) -> list[EmployeeSchedule]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT es.*,
                       ws.name AS schedule_name,
                       TRIM(COALESCE(u.first_name,'') || ' ' || COALESCE(u.last_name,'')) AS employee_name
                FROM employee_schedules es
                JOIN work_schedules ws ON ws.id = es.schedule_id
                JOIN users u ON u.id = es.user_id
                WHERE es.user_id = %s
                ORDER BY es.effective_from DESC
                """,
                (user_id,),
            ).fetchall()
        return [EmployeeSchedule.from_row(normalize_row(r)) for r in rows]

    def list_assignments_for_schedule(self, schedule_id: int) -> list[EmployeeSchedule]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT es.*,
                       ws.name AS schedule_name,
                       TRIM(COALESCE(u.first_name,'') || ' ' || COALESCE(u.last_name,'')) AS employee_name
                FROM employee_schedules es
                JOIN work_schedules ws ON ws.id = es.schedule_id
                JOIN users u ON u.id = es.user_id
                WHERE es.schedule_id = %s AND es.is_active IS TRUE
                ORDER BY employee_name
                """,
                (schedule_id,),
            ).fetchall()
        return [EmployeeSchedule.from_row(normalize_row(r)) for r in rows]

    def create_assignment(
        self,
        *,
        user_id: int,
        schedule_id: int,
        effective_from: date,
        effective_to: date | None = None,
    ) -> int:
        """
        Deactivate any existing open assignment for this user before creating new one.
        """
        with get_connection() as conn:
            # Close previous open assignments
            conn.execute(
                """
                UPDATE employee_schedules
                SET is_active = FALSE,
                    effective_to = %s
                WHERE user_id = %s
                  AND is_active IS TRUE
                  AND (effective_to IS NULL OR effective_to > %s)
                  AND (business_id = %s OR (%s IS NULL AND business_id IS NULL))
                """,
                (effective_from, user_id, effective_from, self.business_id, self.business_id),
            )
            cursor = conn.execute(
                """
                INSERT INTO employee_schedules
                    (user_id, schedule_id, business_id, effective_from, effective_to, is_active)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                RETURNING id
                """,
                (user_id, schedule_id, self.business_id, effective_from, effective_to),
            )
            return int(cursor.fetchone()["id"])

    def deactivate_assignment(self, assignment_id: int) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE employee_schedules SET is_active = FALSE WHERE id = %s",
                (assignment_id,),
            )

    def list_all_active_assignments(self) -> list[EmployeeSchedule]:
        """All currently active assignments (for compliance checks)."""
        ref = date.today()
        clauses = [
            "es.is_active IS TRUE",
            "es.effective_from <= %s",
            "(es.effective_to IS NULL OR es.effective_to >= %s)",
        ]
        params: list = [ref, ref]
        if self.business_id is not None:
            clauses.append("(es.business_id = %s OR es.business_id IS NULL)")
            params.append(self.business_id)

        with get_connection() as conn:
            rows = conn.execute(
                f"""
                SELECT es.*,
                       ws.name AS schedule_name,
                       TRIM(COALESCE(u.first_name,'') || ' ' || COALESCE(u.last_name,'')) AS employee_name
                FROM employee_schedules es
                JOIN work_schedules ws ON ws.id = es.schedule_id
                JOIN users u ON u.id = es.user_id
                WHERE {' AND '.join(clauses)}
                ORDER BY employee_name
                """,
                params,
            ).fetchall()
        return [EmployeeSchedule.from_row(normalize_row(r)) for r in rows]
