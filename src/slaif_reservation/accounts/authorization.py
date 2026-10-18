"""Application capability constants and checks for the selected A16 target.

This module is the additive grant foundation (orders 048-a through 050-a):
it names the ten documented application permissions in the ``reservations``
namespace and provides the shared checks that an active, authenticated,
non-service-account human explicitly holds one (or any) of them, evaluated
through Django's normal permission machinery (groups combined additively
with individual ``user_permissions``; trusted active superusers keep Django
permission semantics).

``has_reservation_permission`` gates a single capability;
``has_any_reservation_permission`` gates a route or landing against several;
``is_management_user`` names management-dashboard admission (any of the nine
management capabilities). There is no process-global permission cache here:
every call evaluates the given user instance, so a fresh principal observes
current grants.
"""

from __future__ import annotations

from typing import Any

#: Namespace (app label) of the documented application permissions.
RESERVATIONS_APP_LABEL = "reservations"

#: The ten A16 application permission codenames, in documented order.
RESERVATIONS_PERMISSIONS: tuple[str, ...] = (
    "book_assets",
    "view_all_reservations",
    "cancel_others_reservations",
    "release_others_reservations",
    "view_booking_policies",
    "manage_booking_policies",
    "view_maintenance_blackouts",
    "manage_maintenance_blackouts",
    "view_audit_history",
    "export_audit_history",
)

#: Baseline booking capability preserved for existing humans by the one-time
#: upgrade grant (order 048-a, accounts 0005 data migration).
BOOKING_BASELINE_PERMISSION = "book_assets"

#: The nine management/read-all capabilities granted by the explicit
#: ``grant_management_access`` setup command (all ten except the baseline
#: booking capability, which is separate).
MANAGEMENT_PERMISSIONS: tuple[str, ...] = tuple(
    codename for codename in RESERVATIONS_PERMISSIONS if codename != BOOKING_BASELINE_PERMISSION
)


def permission_label(codename: str) -> str:
    """Django permission string (``reservations.<codename>``) for a codename."""
    return f"{RESERVATIONS_APP_LABEL}.{codename}"


def has_reservation_permission(user: Any, codename: str) -> bool:
    """Whether an active non-service-account human holds one capability.

    The check requires an active, authenticated, non-service-account user and
    then defers to Django's permission machinery (``user.has_perm``), so
    grants combine additively across all of the user's groups and individual
    permissions, and trusted active human superusers retain Django's
    permission semantics. Staff status alone confers no capability, and an
    inactive, unauthenticated or service-account user never holds one, even
    when a permission record is attached.

    The supplied ``user`` instance is evaluated as-is (fresh per-request
    principals observe current grants); nothing here is cached across calls.
    """
    if codename not in RESERVATIONS_PERMISSIONS:
        raise ValueError(f"Unknown reservations permission: {codename!r}")
    if not getattr(user, "is_authenticated", False):
        return False
    if not getattr(user, "is_active", False):
        return False
    if getattr(user, "is_service_account", False):
        return False
    return bool(user.has_perm(permission_label(codename)))


def has_any_reservation_permission(user: Any, codenames: tuple[str, ...] | list[str]) -> bool:
    """Whether an active non-service-account human holds at least one named capability.

    Same human-eligibility gate as :func:`has_reservation_permission`, then a
    union across every named codename through Django's permission machinery.
    Every codename must be one of the ten documented capabilities; an empty
    or unknown codename list never admits (fail closed). Nothing is cached
    across calls.
    """
    if not codenames:
        return False
    for codename in codenames:
        if codename not in RESERVATIONS_PERMISSIONS:
            raise ValueError(f"Unknown reservations permission: {codename!r}")
    if not getattr(user, "is_authenticated", False):
        return False
    if not getattr(user, "is_active", False):
        return False
    if getattr(user, "is_service_account", False):
        return False
    return any(bool(user.has_perm(permission_label(codename))) for codename in codenames)


def is_management_user(user: Any) -> bool:
    """Management-dashboard admission: any of the nine management capabilities.

    Staff status alone confers nothing; an active non-service-account human
    holding at least one of ``MANAGEMENT_PERMISSIONS`` (through groups or
    individual grants, or superuser semantics) is admitted to the management
    dashboard. Individual routes still check their own narrower capability
    set.
    """
    return has_any_reservation_permission(user, MANAGEMENT_PERMISSIONS)
