"""
Plan codes, feature keys, and subscription states as typed constants.
Import these throughout the codebase instead of using raw strings.
"""

from __future__ import annotations

from enum import StrEnum


class PlanCode(StrEnum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class PlanFeature(StrEnum):
    # Infrastructure
    KIOSK = "kiosk"
    GEOLOCATION = "geolocation"
    MULTI_LOCATION = "multi_location"

    # Reporting
    ADVANCED_REPORTS = "advanced_reports"
    EXPORTS_BASIC = "exports_basic"
    EXPORTS_ADVANCED = "exports_advanced"

    # Operations
    FILTERS_ADVANCED = "filters_advanced"
    INCIDENT_MANAGEMENT = "incident_management"
    ADMIN_CLOSURES = "admin_closures"

    # Implementation
    IMPLEMENTATION_SUPPORT = "implementation_support"
    PRIORITY_SUPPORT = "priority_support"
    CUSTOM_BRANDING = "custom_branding"


class SubscriptionStatus(StrEnum):
    TRIAL = "trial"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    CANCELED = "canceled"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    INCOMPLETE = "incomplete"


class PlatformRole(StrEnum):
    SUPERADMIN = "superadmin"
    INTERNAL_ADMIN = "internal_admin"


class BusinessRole(StrEnum):
    OWNER = "owner"
    COMPANY_ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    KIOSK_DEVICE = "kiosk_device"


PLATFORM_ADMIN_ROLES = {
    PlatformRole.SUPERADMIN,
    PlatformRole.INTERNAL_ADMIN,
    PlatformRole.SUPERADMIN.value,
    PlatformRole.INTERNAL_ADMIN.value,
}
