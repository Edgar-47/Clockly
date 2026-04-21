from dataclasses import dataclass

from app.database.business_user_repository import BusinessUserRepository


class AuthorizationError(PermissionError):
    """Raised when a user is authenticated but lacks a business permission."""


ROLE_PERMISSIONS: dict[str, set[str]] = {
    "owner": {
        "business:view",
        "business:update",
        "billing:manage",
        "subscription:view",
        "users:manage_admins",
        "employees:manage",
        "attendance:manage",
        "reports:view",
        "kiosk:use",
    },
    "admin": {
        "business:view",
        "subscription:view",
        "employees:manage",
        "attendance:manage",
        "reports:view",
        "kiosk:use",
    },
    "manager": {
        "business:view",
        "employees:view",
        "attendance:manage",
        "reports:view",
    },
    "employee": {
        "attendance:self",
    },
    "kiosk_device": {
        "kiosk:use",
    },
}


@dataclass(frozen=True)
class BusinessPrincipal:
    user_id: int
    business_id: str
    role: str

    def can(self, permission: str) -> bool:
        return permission in ROLE_PERMISSIONS.get(self.role, set())


class AuthorizationService:
    def __init__(self, business_user_repository: BusinessUserRepository | None = None) -> None:
        self.business_user_repository = business_user_repository or BusinessUserRepository()

    def principal_for(self, *, user_id: int, business_id: str) -> BusinessPrincipal:
        role = self.business_user_repository.get_active_role(
            business_id=business_id,
            user_id=user_id,
        )
        if not role:
            raise AuthorizationError("No tienes acceso a este negocio.")
        return BusinessPrincipal(user_id=user_id, business_id=business_id, role=role)

    def require_permission(
        self,
        *,
        user_id: int,
        business_id: str,
        permission: str,
    ) -> BusinessPrincipal:
        principal = self.principal_for(user_id=user_id, business_id=business_id)
        if not principal.can(permission):
            raise AuthorizationError("No tienes permisos para realizar esta accion.")
        return principal

    def can_manage_role(self, *, actor_role: str, target_role: str) -> bool:
        if actor_role == "owner":
            return target_role in {"admin", "manager", "employee"}
        if actor_role == "admin":
            return target_role == "employee"
        return False
