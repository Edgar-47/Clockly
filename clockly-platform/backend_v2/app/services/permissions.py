from app.models.enums import UserRole


ROLE_PERMISSIONS: dict[UserRole, set[str]] = {
    UserRole.OWNER: {
        "employees:read",
        "employees:write",
        "attendance:read",
        "attendance:write",
        "attendance:manage",
        "metrics:read",
        "tickets:read",
        "tickets:write",
        "exports:read",
    },
    UserRole.ADMIN: {
        "employees:read",
        "employees:write",
        "attendance:read",
        "attendance:write",
        "attendance:manage",
        "metrics:read",
        "tickets:read",
        "tickets:write",
        "exports:read",
    },
    UserRole.MANAGER: {
        "employees:read",
        "attendance:read",
        "attendance:write",
        "attendance:manage",
        "metrics:read",
        "tickets:read",
        "tickets:write",
    },
    UserRole.EMPLOYEE: {
        "attendance:read",
        "attendance:write",
        "tickets:read",
        "tickets:write",
    },
}


def permissions_for_role(role: UserRole) -> list[str]:
    return sorted(ROLE_PERMISSIONS.get(role, set()))


def role_has_permission(role: UserRole, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())

