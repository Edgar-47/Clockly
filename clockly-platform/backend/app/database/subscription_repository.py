from app.database.connection import get_connection
from app.models.subscription import Subscription


class SubscriptionRepository:
    # All plan columns are fetched via JOIN so Subscription.plan is always populated.
    _SELECT_WITH_PLAN = """
        s.id, s.business_id, s.plan_id, s.status,
        COALESCE(s.billing_cycle, 'monthly') AS billing_cycle,
        COALESCE(s.price, p.price_monthly) AS price,
        COALESCE(s.currency, 'EUR') AS currency,
        s.current_period_start, s.current_period_end, s.renewal_date,
        s.cancel_at, s.cancelled_at, s.trial_ends_at, s.paused_at,
        COALESCE(s.payment_status, 'none') AS payment_status,
        s.notes,
        s.stripe_customer_id, s.stripe_subscription_id,
        s.created_at, s.updated_at,
        p.code AS plan_code, p.name AS plan_name,
        p.max_employees, p.max_admins,
        p.has_kiosk, p.has_advanced_reports, p.has_geolocation, p.has_multi_location,
        p.has_exports_basic, p.has_exports_advanced,
        p.has_filters_advanced, p.has_incident_management,
        p.has_admin_closures, p.has_implementation_support,
        p.has_priority_support, p.has_custom_branding,
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
        billing_cycle: str = "monthly",
    ) -> Subscription:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO subscriptions (business_id, plan_id, status, billing_cycle)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (business_id) DO UPDATE SET
                    plan_id = EXCLUDED.plan_id,
                    status = EXCLUDED.status,
                    billing_cycle = EXCLUDED.billing_cycle,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (business_id, plan_id, status, billing_cycle),
            )
        subscription = self.get_for_business(business_id)
        if subscription is None:
            raise RuntimeError("No se pudo crear la suscripción.")
        return subscription

    def update_plan(
        self,
        *,
        business_id: str,
        plan_id: int,
        status: str = "active",
        billing_cycle: str | None = None,
    ) -> Subscription:
        """Change the plan (and optionally status) of an existing subscription."""
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE subscriptions
                SET plan_id = %s,
                    status = %s,
                    billing_cycle = COALESCE(%s, billing_cycle),
                    updated_at = CURRENT_TIMESTAMP
                WHERE business_id = %s
                """,
                (plan_id, status, billing_cycle, business_id),
            )
        subscription = self.get_for_business(business_id)
        if subscription is None:
            raise RuntimeError("No se pudo actualizar la suscripción.")
        return subscription
