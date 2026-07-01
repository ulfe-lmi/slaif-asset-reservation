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
        queryset = queryset.filter(asset_id=asset_id)
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
    return queryset


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
        try:
            queryset = queryset.filter(correlation_id=uuid.UUID(str(correlation_id)))
        except ValueError:
            queryset = queryset.none()
    if actor := params.get("actor"):
        queryset = queryset.filter(Q(actor_user__display_name__icontains=actor))
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
