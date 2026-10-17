"""One authoritative booking-eligibility check (order 049-a, SAR-049).

A new reservation requires BOTH:

1. the global application capability ``reservations.book_assets``
   (checked through the 048-a helper ``has_reservation_permission``,
   which already enforces active, authenticated, non-service-account
   human semantics and combines grants additively across all groups and
   individual permissions; trusted active superusers retain Django's
   permission semantics), and
2. exact-asset eligibility: unrestricted assets pass; group-restricted
   assets require membership in at least one of the asset's allowed
   existing groups (restricted with an empty allow-list fails closed).

Only the booked asset is ever checked: there is no parent-to-child
access inheritance, no explicit deny and no group-name constants.  The
predicate is stateless and evaluates the supplied user instance as-is,
so fresh per-request (or row-locked) principals observe current grants;
nothing is cached across calls.  Owner lifecycle operations
(list/inspect/cancel/release of already accepted reservations) never
pass through this check.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from slaif_reservation.accounts.authorization import (
    BOOKING_BASELINE_PERMISSION,
    has_reservation_permission,
)

from .models import Asset

#: Member-safe states; no group names or account metadata may leak through
#: any surface that renders them.
STATE_ELIGIBLE = "eligible"
STATE_NO_BOOKING_PERMISSION = "no_booking_permission"
STATE_NO_ALLOWED_GROUP = "no_allowed_group"


def user_group_ids(user: Any) -> frozenset[int]:
    """Current group memberships of the given user instance (no cache)."""
    return frozenset(user.groups.values_list("id", flat=True))


def _has_allowed_group(allowed_group_ids: frozenset[int], user_ids: frozenset[int]) -> bool:
    return bool(allowed_group_ids & user_ids)


def user_can_book_asset(user: Any, asset: Asset | None) -> bool:
    """Whether an active human may create a NEW reservation for this asset.

    ``asset=None`` evaluates the global capability only (used by the bearer
    preflight before the asset's existence is known, preserving the
    existing missing-asset 404 callback).  The check reads the current
    permission rows and group memberships of ``user`` on every call.
    """
    if not has_reservation_permission(user, BOOKING_BASELINE_PERMISSION):
        return False
    if asset is None or not asset.booking_restricted:
        return True
    allowed = frozenset(asset.allowed_booking_groups.values_list("id", flat=True))
    return _has_allowed_group(allowed, user_group_ids(user))


def batch_asset_booking_states(
    user: Any,
    assets: Iterable[Asset],
    *,
    group_ids: frozenset[int] | None = None,
) -> dict[Any, str]:
    """Member-safe booking states for many assets (one membership query).

    One of ``STATE_ELIGIBLE``, ``STATE_NO_BOOKING_PERMISSION`` or
    ``STATE_NO_ALLOWED_GROUP`` per asset; surfaces may render these states
    without disclosing group names or account metadata.  Intended for
    browsable lists: prefetch ``allowed_booking_groups`` on the asset
    queryset first, then pass it through here.  ``.all()`` on each
    prefetched M2M then reads from the prefetch cache, keeping the
    per-row cost flat.
    """
    has_book = has_reservation_permission(user, BOOKING_BASELINE_PERMISSION)
    ids = group_ids if group_ids is not None else user_group_ids(user)
    states: dict[Any, str] = {}
    for asset in assets:
        if not has_book:
            state = STATE_NO_BOOKING_PERMISSION
        elif not asset.booking_restricted:
            state = STATE_ELIGIBLE
        else:
            allowed = frozenset(group.id for group in asset.allowed_booking_groups.all())
            state = STATE_ELIGIBLE if _has_allowed_group(allowed, ids) else STATE_NO_ALLOWED_GROUP
        states[asset.id] = state
    return states
