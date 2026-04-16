from dataclasses import dataclass

from app.database.business_user_repository import ADMIN_LIKE_ROLES, BusinessUserRepository
from app.database.plan_repository import PlanRepository
from app.database.saas_employee_repository import SaaSEmployeeRepository
from app.database.subscription_repository import SubscriptionRepository
from app.models.plan import Plan
from app.models.subscription import Subscription


class PlanLimitError(ValueError):
    """Raised when a business exceeds a subscription limit."""


class FeatureNotAvailableError(ValueError):
    """Raised when a plan does not include a requested feature."""


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


class SubscriptionService:
    DEFAULT_PLAN_CODE = "basic"

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

    def ensure_default_subscription(
        self,
        *,
        business_id: str,
        plan_code: str | None = None,
    ) -> Subscription:
        plan = self.plan_repository.get_by_code(plan_code or self.DEFAULT_PLAN_CODE)
        if plan is None or not plan.is_active:
            raise ValueError("Plan no disponible.")
        existing = self.subscription_repository.get_for_business(business_id)
        if existing:
            return existing
        return self.subscription_repository.create_default(
            business_id=business_id,
            plan_id=plan.id,
            status="active",
        )

    def get_usage_summary(self, business_id: str) -> UsageSummary:
        subscription = self.subscription_repository.get_for_business(business_id)
        if subscription is None:
            subscription = self.ensure_default_subscription(business_id=business_id)
        if subscription.plan is None:
            plan = self.plan_repository.get_by_id(subscription.plan_id)
        else:
            plan = subscription.plan
        if plan is None:
            raise ValueError("El negocio no tiene un plan valido.")

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
                f"Tu plan {usage.plan.name} permite hasta {usage.plan.max_admins} usuarios administradores o managers activos."
            )

    def assert_feature(self, business_id: str, feature: str) -> None:
        usage = self.get_usage_summary(business_id)
        feature_attr = {
            "kiosk": "has_kiosk",
            "advanced_reports": "has_advanced_reports",
            "geolocation": "has_geolocation",
            "multi_location": "has_multi_location",
        }.get(feature)
        if not feature_attr:
            raise FeatureNotAvailableError("Funcionalidad no reconocida.")
        if not getattr(usage.plan, feature_attr):
            raise FeatureNotAvailableError(
                f"Tu plan {usage.plan.name} no incluye esta funcionalidad."
            )
