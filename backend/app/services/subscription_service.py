from __future__ import annotations

from dataclasses import dataclass

from app.database.business_user_repository import ADMIN_LIKE_ROLES, BusinessUserRepository
from app.database.plan_repository import PlanRepository
from app.database.saas_employee_repository import SaaSEmployeeRepository
from app.database.subscription_repository import SubscriptionRepository
from app.models.plan import Plan, _feature_attr_map
from app.models.plan_constants import PlanCode, PlanFeature, SubscriptionStatus
from app.models.subscription import Subscription


class PlanLimitError(ValueError):
    """Raised when a business tries to exceed a subscription limit."""


class FeatureNotAvailableError(ValueError):
    """Raised when the current plan does not include a requested feature."""


@dataclass(frozen=True)
class UsageSummary:
    plan: Plan
    subscription: Subscription
    employee_count: int
    admin_count: int

    @property
    def employee_slots_remaining(self) -> int:
        return max(self.plan.max_employees - self.employee_count, 0)

    @property
    def admin_slots_remaining(self) -> int:
        return max(self.plan.max_admins - self.admin_count, 0)

    @property
    def employee_usage_pct(self) -> int:
        """0–100 integer percentage for progress bars."""
        if self.plan.max_employees == 0:
            return 100
        return min(100, round(self.employee_count / self.plan.max_employees * 100))

    @property
    def is_at_employee_limit(self) -> bool:
        return self.employee_count >= self.plan.max_employees

    @property
    def is_near_employee_limit(self) -> bool:
        """True when 80 % or more of the employee slots are used."""
        return self.employee_usage_pct >= 80

    def has_feature(self, feature: str) -> bool:
        """Non-raising feature check — use in templates and conditional logic."""
        return self.plan.has_feature(feature)


class SubscriptionService:
    DEFAULT_PLAN_CODE = PlanCode.FREE

    def __init__(
        self,
        *,
        plan_repository: PlanRepository | None = None,
        subscription_repository: SubscriptionRepository | None = None,
        business_user_repository: BusinessUserRepository | None = None,
        employee_repository: SaaSEmployeeRepository | None = None,
    ) -> None:
        self.plan_repository = plan_repository or PlanRepository()
        self.subscription_repository = subscription_repository or SubscriptionRepository()
        self.business_user_repository = business_user_repository or BusinessUserRepository()
        self.employee_repository = employee_repository or SaaSEmployeeRepository()

    # ------------------------------------------------------------------
    # Core helpers
    # ------------------------------------------------------------------

    def ensure_default_subscription(
        self,
        *,
        business_id: str,
        plan_code: str | None = None,
    ) -> Subscription:
        effective_code = plan_code or self.DEFAULT_PLAN_CODE

        plan = self.plan_repository.get_by_code(effective_code)
        if plan is None or not plan.is_active:
            raise ValueError("Plan no disponible.")
        existing = self.subscription_repository.get_for_business(business_id)
        if existing:
            return existing
        return self.subscription_repository.create_default(
            business_id=business_id,
            plan_id=plan.id,
            status=SubscriptionStatus.ACTIVE,
        )

    def get_usage_summary(self, business_id: str) -> UsageSummary:
        subscription = self.subscription_repository.get_for_business(business_id)
        if subscription is None:
            subscription = self.ensure_default_subscription(business_id=business_id)
        plan = subscription.plan or self.plan_repository.get_by_id(subscription.plan_id)
        if plan is None:
            raise ValueError("El negocio no tiene un plan válido.")

        employee_count = self.employee_repository.count_active_for_business(business_id)
        admin_count = self.business_user_repository.count_active_by_roles(
            business_id=business_id,
            roles=ADMIN_LIKE_ROLES,
        )
        return UsageSummary(
            plan=plan,
            subscription=subscription,
            employee_count=employee_count,
            admin_count=admin_count,
        )

    def get_plan_for_business(self, business_id: str) -> Plan:
        """Convenience: return just the Plan object, no usage counts."""
        usage = self.get_usage_summary(business_id)
        return usage.plan

    # ------------------------------------------------------------------
    # Limit assertions — raise PlanLimitError if exceeded
    # ------------------------------------------------------------------

    def assert_can_create_employee(self, business_id: str) -> None:
        usage = self.get_usage_summary(business_id)
        if usage.employee_count >= usage.plan.max_employees:
            raise PlanLimitError(
                f"Tu plan {usage.plan.name} permite hasta {usage.plan.max_employees} empleados activos."
            )

    def assert_can_create_admin(self, business_id: str) -> None:
        usage = self.get_usage_summary(business_id)
        if usage.admin_count >= usage.plan.max_admins:
            raise PlanLimitError(
                f"Tu plan {usage.plan.name} permite hasta {usage.plan.max_admins} "
                f"administradores o managers activos."
            )

    # ------------------------------------------------------------------
    # Feature access — two flavours: asserting and boolean
    # ------------------------------------------------------------------

    def assert_feature(self, business_id: str, feature: str) -> None:
        """Raise FeatureNotAvailableError if the plan does not include *feature*."""
        attr = _feature_attr_map().get(feature)
        if not attr:
            raise FeatureNotAvailableError("Funcionalidad no reconocida.")
        plan = self.get_plan_for_business(business_id)
        if not getattr(plan, attr, False):
            raise FeatureNotAvailableError(
                f"Esta función no está incluida en tu plan {plan.name}. "
                f"Actualiza a Pro para acceder."
            )

    def has_feature(self, business_id: str, feature: str) -> bool:
        """Non-raising feature check — safe to call from templates via context."""
        try:
            plan = self.get_plan_for_business(business_id)
            return plan.has_feature(feature)
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Plan upgrade
    # ------------------------------------------------------------------

    def upgrade_plan(self, business_id: str, target_plan_code: str) -> Subscription:
        """
        Switch a business to a different plan.
        In production this would be gated behind a Stripe checkout; here it
        updates the subscription directly for testing / manual administration.
        """
        target_plan = self.plan_repository.get_by_code(target_plan_code)
        if target_plan is None or not target_plan.is_active:
            raise ValueError(f"El plan '{target_plan_code}' no está disponible.")

        existing = self.subscription_repository.get_for_business(business_id)
        if existing and existing.plan and existing.plan.code == target_plan_code:
            raise ValueError("El negocio ya tiene este plan activo.")

        return self.subscription_repository.update_plan(
            business_id=business_id,
            plan_id=target_plan.id,
            status=SubscriptionStatus.ACTIVE,
        )

    def get_upgrade_options(self, business_id: str) -> list[Plan]:
        """Return plans that represent an upgrade from the current one."""
        current_plan = self.get_plan_for_business(business_id)
        all_plans = self.plan_repository.list_active()
        return [
            p for p in all_plans
            if p.price_monthly > current_plan.price_monthly
        ]
