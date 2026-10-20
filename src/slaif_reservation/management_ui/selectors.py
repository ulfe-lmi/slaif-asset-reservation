from __future__ import annotations

import uuid
from typing import Any

from django.db.models import Q, QuerySet
from django.utils import timezone

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.reservations.models import (
    MaintenanceBlackout,
    Reservation,
    ReservationLifecycle,
    ReservationPolicy,
)
from slaif_reservation.reservations.services import resolve_effective_policy
from slaif_reservation.reservations.time_utils import require_aware_utc


def policy_queryset() -> QuerySet[ReservationPolicy]:
    return ReservationPolicy.objects.select_related("asset", "asset__parent").order_by(
        "-active", "asset__slug", "name"
    )


def blackout_queryset() -> QuerySet[MaintenanceBlackout]:
    return MaintenanceBlackout.objects.select_related(
        "asset",
        "asset__parent",
        "created_by",
        "deactivated_by",
    ).order_by("-start_at", "-created_at")


def reservation_queryset(params: Any | None = None) -> QuerySet[Reservation]:
    queryset = Reservation.objects.select_related(
        "asset",
        "asset__parent",
        "requested_by_user",
        "cancelled_by",
    ).order_by("-start_at", "-created_at")
    if not params:
        return queryset
    if asset_id := params.get("asset"):
        queryset = queryset.filter(asset=asset_id)
    if status := params.get("status"):
        queryset = queryset.filter(status=status)
    if q := str(params.get("q", "")).strip():
        queryset = queryset.filter(
            Q(requested_by_user__email__icontains=q)
            | Q(requested_by_user__display_name__icontains=q)
            | Q(asset__slug__icontains=q)
            | Q(asset__name__icontains=q)
        )
    if lifecycle := params.get("lifecycle"):
        now = require_aware_utc(timezone.now(), field_name="now")
        if lifecycle == ReservationLifecycle.ACTIVE:
            queryset = queryset.filter(
                status=Reservation.STATUS_CONFIRMED,
                start_at__lte=now,
                effective_end_at__gt=now,
            )
        elif lifecycle == ReservationLifecycle.UPCOMING:
            queryset = queryset.filter(status=Reservation.STATUS_CONFIRMED, start_at__gt=now)
        elif lifecycle == ReservationLifecycle.COMPLETED:
            queryset = queryset.filter(
                status=Reservation.STATUS_CONFIRMED,
                effective_end_at__lte=now,
            )
        elif lifecycle == ReservationLifecycle.CANCELLED:
            queryset = queryset.filter(status=Reservation.STATUS_CANCELLED)
        elif lifecycle == ReservationLifecycle.RELEASED:
            queryset = queryset.filter(status=Reservation.STATUS_RELEASED)
    if from_at := params.get("from"):
        queryset = queryset.filter(start_at__gte=from_at)
    if to_at := params.get("to"):
        queryset = queryset.filter(start_at__lt=to_at)
    return queryset


#: Hard cap on calendar intervals rendered for one fixed window/asset.
#: Overflow is stated plainly and linked to the filtered All reservations
#: list so nothing is silently omitted.
CALENDAR_MAX_INTERVALS = 100


def reservation_calendar_query(
    asset: Asset, window_start: Any, window_end: Any
) -> QuerySet[Reservation]:
    """Intervals that occupy ``asset`` inside the half-open instant window.

    Only confirmed rows and released consumed rows can block an asset
    (cancelled rows never block), so exactly those two statuses are
    rendered; a released row contributes ``[start_at, effective_end_at)``,
    never its original end. The overlap test is the shared half-open form:
    ``start_at < window_end`` AND ``effective_end_at > window_start`` in
    aware time.
    """
    return (
        Reservation.objects.select_related("requested_by_user")
        .filter(
            asset=asset,
            status__in=[Reservation.STATUS_CONFIRMED, Reservation.STATUS_RELEASED],
            start_at__lt=window_end,
            effective_end_at__gt=window_start,
        )
        .order_by("start_at", "id")
    )


def audit_queryset(params: Any | None = None) -> QuerySet[AuditEvent]:
    queryset = AuditEvent.objects.select_related("actor_user").order_by("-occurred_at", "-id")
    if not params:
        return queryset
    if action := params.get("action"):
        queryset = queryset.filter(action=action)
    if target_type := params.get("target_type"):
        queryset = queryset.filter(target_type=target_type)
    if source := params.get("source"):
        queryset = queryset.filter(source=source)
    if correlation_id := params.get("correlation_id"):
        queryset = queryset.filter(correlation_id=correlation_id)
    if actor := params.get("actor"):
        actor_query = Q(actor_user__display_name__icontains=actor) | Q(
            actor_user__email__icontains=actor
        )
        try:
            actor_query |= Q(actor_user_id=uuid.UUID(str(actor)))
        except ValueError:
            pass
        queryset = queryset.filter(actor_query)
    if occurred_from := params.get("occurred_from"):
        queryset = queryset.filter(occurred_at__gte=occurred_from)
    if occurred_to := params.get("occurred_to"):
        queryset = queryset.filter(occurred_at__lte=occurred_to)
    return queryset


def effective_policy_context(asset: Asset | None) -> dict[str, Any]:
    if asset is None:
        return {"asset": None, "policy": None, "state": ""}
    try:
        policy = resolve_effective_policy(asset)
    except Exception:
        return {"asset": asset, "policy": None, "state": "missing_or_ambiguous"}
    if policy.asset_id == asset.id:
        state = "exact asset"
    elif asset.parent_id and policy.asset_id == asset.parent_id:
        state = "parent machine"
    else:
        state = "global"
    return {"asset": asset, "policy": policy, "state": state}


def management_user_queryset() -> QuerySet[User]:
    return User.objects.order_by("email")
