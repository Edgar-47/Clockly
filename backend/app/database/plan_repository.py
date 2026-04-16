from app.database.connection import get_connection
from app.models.plan import Plan


class PlanRepository:
    _SELECT = """
        id, code, name, max_employees, max_admins, has_kiosk,
        has_advanced_reports, has_geolocation, has_multi_location,
        price_monthly, price_yearly, is_active
    """

    def get_by_code(self, code: str) -> Plan | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self._SELECT}
                FROM plans
                WHERE code = %s
                LIMIT 1
                """,
                (code.strip().lower(),),
            ).fetchone()
        return Plan.from_row(row) if row else None

    def get_by_id(self, plan_id: int) -> Plan | None:
        with get_connection() as connection:
            row = connection.execute(
                f"SELECT {self._SELECT} FROM plans WHERE id = %s",
                (plan_id,),
            ).fetchone()
        return Plan.from_row(row) if row else None

    def list_active(self) -> list[Plan]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT {self._SELECT}
                FROM plans
                WHERE is_active IS TRUE
                ORDER BY price_monthly, id
                """
            ).fetchall()
        return [Plan.from_row(row) for row in rows]
