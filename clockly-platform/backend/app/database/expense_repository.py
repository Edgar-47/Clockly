"""
app/database/expense_repository.py

Data-access layer for the expenses module.
All queries are scoped to business_id for multi-tenant isolation.
"""
from __future__ import annotations

from app.database.connection import get_connection
from app.models.expense import Expense, ExpenseAttachment


class ExpenseRepository:
    _SELECT_EXPENSE = """
        e.id, e.business_id, e.user_id, e.title, e.description,
        e.amount, e.currency, e.category, e.expense_date, e.status,
        e.reference_number, e.admin_notes, e.reviewed_by, e.reviewed_at,
        e.reimbursed_at, e.created_at, e.updated_at,
        TRIM(u.first_name || ' ' || u.last_name) AS employee_name,
        TRIM(rv.first_name || ' ' || rv.last_name) AS reviewer_name
    """

    _FROM_EXPENSE = """
        FROM expenses e
        JOIN users u ON u.id = e.user_id
        LEFT JOIN users rv ON rv.id = e.reviewed_by
    """

    def __init__(self, business_id: str | None = None) -> None:
        self.business_id = business_id

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def create(
        self,
        *,
        user_id: int,
        title: str,
        amount: float,
        expense_date: str,
        description: str | None = None,
        category: str = "otros",
        currency: str = "EUR",
        reference_number: str | None = None,
    ) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO expenses
                    (business_id, user_id, title, description, amount, currency,
                     category, expense_date, status, reference_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pendiente', %s)
                RETURNING id
                """,
                (
                    self.business_id, user_id, title, description, amount,
                    currency, category, expense_date, reference_number,
                ),
            )
            return int(cursor.fetchone()["id"])

    def update_status(
        self,
        expense_id: int,
        *,
        status: str,
        reviewed_by: int | None = None,
        admin_notes: str | None = None,
        reimbursed_at: str | None = None,
    ) -> bool:
        clauses = ["status = %s", "reviewed_at = CURRENT_TIMESTAMP", "updated_at = CURRENT_TIMESTAMP"]
        params: list = [status]

        if reviewed_by is not None:
            clauses.append("reviewed_by = %s")
            params.append(reviewed_by)
        if admin_notes is not None:
            clauses.append("admin_notes = %s")
            params.append(admin_notes)
        if reimbursed_at is not None:
            clauses.append("reimbursed_at = %s")
            params.append(reimbursed_at)

        where = ["id = %s"]
        params.append(expense_id)
        if self.business_id:
            where.append("business_id = %s")
            params.append(self.business_id)

        with get_connection() as conn:
            result = conn.execute(
                f"UPDATE expenses SET {', '.join(clauses)} WHERE {' AND '.join(where)}",
                params,
            )
            return result.rowcount > 0

    def update_admin_notes(self, expense_id: int, admin_notes: str | None) -> bool:
        where = ["id = %s"]
        params: list = [admin_notes, expense_id]
        if self.business_id:
            where.append("business_id = %s")
            params.append(self.business_id)
        with get_connection() as conn:
            result = conn.execute(
                f"UPDATE expenses SET admin_notes = %s, updated_at = CURRENT_TIMESTAMP WHERE {' AND '.join(where)}",
                params,
            )
            return result.rowcount > 0

    def delete(self, expense_id: int) -> bool:
        where = ["id = %s"]
        params: list = [expense_id]
        if self.business_id:
            where.append("business_id = %s")
            params.append(self.business_id)
        with get_connection() as conn:
            result = conn.execute(
                f"DELETE FROM expenses WHERE {' AND '.join(where)}",
                params,
            )
            return result.rowcount > 0

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_by_id(self, expense_id: int) -> Expense | None:
        where = ["e.id = %s"]
        params: list = [expense_id]
        if self.business_id:
            where.append("e.business_id = %s")
            params.append(self.business_id)

        with get_connection() as conn:
            row = conn.execute(
                f"SELECT {self._SELECT_EXPENSE} {self._FROM_EXPENSE} WHERE {' AND '.join(where)}",
                params,
            ).fetchone()
        return Expense.from_row(row) if row else None

    def list_by_user(
        self,
        user_id: int,
        *,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Expense]:
        where = ["e.user_id = %s"]
        params: list = [user_id]
        if self.business_id:
            where.append("e.business_id = %s")
            params.append(self.business_id)
        if status:
            where.append("e.status = %s")
            params.append(status)
        params.extend([limit, offset])

        with get_connection() as conn:
            rows = conn.execute(
                f"""
                SELECT {self._SELECT_EXPENSE} {self._FROM_EXPENSE}
                WHERE {' AND '.join(where)}
                ORDER BY e.created_at DESC
                LIMIT %s OFFSET %s
                """,
                params,
            ).fetchall()
        return [Expense.from_row(r) for r in rows]

    def list_all(
        self,
        *,
        status: str | None = None,
        user_id: int | None = None,
        search: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        amount_min: float | None = None,
        amount_max: float | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[Expense]:
        where: list[str] = []
        params: list = []

        if self.business_id:
            where.append("e.business_id = %s")
            params.append(self.business_id)
        if status:
            where.append("e.status = %s")
            params.append(status)
        if user_id:
            where.append("e.user_id = %s")
            params.append(user_id)
        if search:
            where.append("LOWER(e.title) LIKE LOWER(%s)")
            params.append(f"%{search}%")
        if date_from:
            where.append("e.expense_date >= %s")
            params.append(date_from)
        if date_to:
            where.append("e.expense_date <= %s")
            params.append(date_to)
        if amount_min is not None:
            where.append("e.amount >= %s")
            params.append(amount_min)
        if amount_max is not None:
            where.append("e.amount <= %s")
            params.append(amount_max)

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        params.extend([limit, offset])

        with get_connection() as conn:
            rows = conn.execute(
                f"""
                SELECT {self._SELECT_EXPENSE} {self._FROM_EXPENSE}
                {where_sql}
                ORDER BY
                    CASE e.status WHEN 'pendiente' THEN 0 ELSE 1 END,
                    e.created_at DESC
                LIMIT %s OFFSET %s
                """,
                params,
            ).fetchall()
        return [Expense.from_row(r) for r in rows]

    def count_by_status(self) -> dict[str, int]:
        where = "WHERE e.business_id = %s" if self.business_id else ""
        params = [self.business_id] if self.business_id else []
        with get_connection() as conn:
            rows = conn.execute(
                f"""
                SELECT e.status, COUNT(*) AS cnt
                FROM expenses e
                {where}
                GROUP BY e.status
                """,
                params,
            ).fetchall()
        return {r["status"]: r["cnt"] for r in rows}

    def total_amount_by_status(self, status: str) -> float:
        where = ["e.status = %s"]
        params: list = [status]
        if self.business_id:
            where.append("e.business_id = %s")
            params.append(self.business_id)
        with get_connection() as conn:
            row = conn.execute(
                f"SELECT COALESCE(SUM(e.amount), 0) AS total FROM expenses e WHERE {' AND '.join(where)}",
                params,
            ).fetchone()
        return float(row["total"]) if row else 0.0

    def total_by_user(self, user_id: int) -> float:
        where = ["e.user_id = %s", "e.status != 'rechazado'"]
        params: list = [user_id]
        if self.business_id:
            where.append("e.business_id = %s")
            params.append(self.business_id)
        with get_connection() as conn:
            row = conn.execute(
                f"SELECT COALESCE(SUM(e.amount), 0) AS total FROM expenses e WHERE {' AND '.join(where)}",
                params,
            ).fetchone()
        return float(row["total"]) if row else 0.0

    # ------------------------------------------------------------------
    # Attachment operations
    # ------------------------------------------------------------------

    def add_attachment(
        self,
        *,
        expense_id: int,
        file_name: str,
        file_path: str,
        file_size: int | None = None,
        mime_type: str | None = None,
    ) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO expense_attachments
                    (expense_id, file_name, file_path, file_size, mime_type)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (expense_id, file_name, file_path, file_size, mime_type),
            )
            return int(cursor.fetchone()["id"])

    def get_attachments(self, expense_id: int) -> list[ExpenseAttachment]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, expense_id, file_name, file_path, file_size, mime_type, created_at
                FROM expense_attachments
                WHERE expense_id = %s
                ORDER BY created_at ASC
                """,
                (expense_id,),
            ).fetchall()
        return [ExpenseAttachment.from_row(r) for r in rows]

    def delete_attachment(self, attachment_id: int) -> bool:
        with get_connection() as conn:
            result = conn.execute(
                "DELETE FROM expense_attachments WHERE id = %s",
                (attachment_id,),
            )
            return result.rowcount > 0
