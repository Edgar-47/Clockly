from app.database.connection import get_connection
from app.models.subscription import Subscription


class SubscriptionRepository:
    _SELECT_WITH_PLAN = """
        s.id, s.business_id, s.plan_id, s.status, s.current_period_start,
        s.current_period_end, s.stripe_customer_id, s.stripe_subscription_id,
        s.created_at, s.updated_at,
        p.code AS plan_code, p.name AS plan_name, p.max_employees, p.max_admins,
        p.has_kiosk, p.has_advanced_reports, p.has_geolocation, p.has_multi_location,
        p.price_monthly, p.price_yearly, p.is_active AS plan_is_active
    """

    def get_for_business(self, business_id: str) -> Subscription | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self._SELECT_WITH_PLAN}
                FROM subscriptions s
                JOIN plans p ON p.id = s.plan_id
                WHERE s.business_id = %s
                LIMIT 1
                """,
                (business_id,),
            ).fetchone()
        return Subscription.from_row(row) if row else None

    def create_default(
        self,
        *,
        business_id: str,
        plan_id: int,
        status: str = "active",
    ) -> Subscription:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO subscriptions (business_id, plan_id, status)
                VALUES (%s, %s, %s)
                ON CONFLICT (business_id) DO UPDATE SET
                    plan_id = EXCLUDED.plan_id,
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (business_id, plan_id, status),
            )
        subscription = self.get_for_business(business_id)
        if subscription is None:
            raise RuntimeError("No se pudo crear la suscripcion.")
        return subscription
