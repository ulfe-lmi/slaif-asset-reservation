from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, QuerySet
from django.utils import timezone

from slaif_reservation.assets.models import Asset, AssetTag
from slaif_reservation.assets.selectors import AssetFilterError, AssetFilters, parse_asset_filters
from slaif_reservation.reservations.models import Reservation
from slaif_reservation.reservations.time_utils import require_aware_utc


@dataclass(frozen=True)
class MemberAssetContext:
    filters: AssetFilters
    assets: QuerySet[Asset]
    parents: QuerySet[Asset]
    tags: QuerySet[AssetTag]


def parse_member_asset_filters(params: Any) -> AssetFilters:
    filters = parse_asset_filters(params)
    if filters.active is False:
        raise AssetFilterError("Inactive assets are not visible in the member inventory.")
    return AssetFilters(
        kind=filters.kind,
        parent=filters.parent,
        tag=filters.tag,
        active=True,
        reservable=filters.reservable,
        search=filters.search,
    )


def member_asset_queryset(filters: AssetFilters | None = None) -> QuerySet[Asset]:
    queryset = (
        Asset.objects.filter(active=True)
        .select_related("parent")
        .prefetch_related("tags")
        .order_by("slug")
    )
    if filters is None:
        return queryset
    if filters.kind:
        queryset = queryset.filter(kind=filters.kind)
    if filters.parent:
        queryset = queryset.filter(parent_id=filters.parent)
    if filters.tag:
        queryset = queryset.filter(tags__slug=filters.tag)
    if filters.reservable is not None:
        queryset = queryset.filter(reservable=filters.reservable)
    if filters.search:
        queryset = queryset.filter(
            Q(name__icontains=filters.search)
            | Q(slug__icontains=filters.search)
            | Q(description__icontains=filters.search)
        )
    return queryset.distinct()


def member_asset_context(filters: AssetFilters) -> MemberAssetContext:
    return MemberAssetContext(
        filters=filters,
        assets=member_asset_queryset(filters),
        parents=Asset.objects.filter(kind=Asset.KIND_MACHINE, active=True).order_by("slug"),
        tags=AssetTag.objects.filter(assets__active=True).distinct().order_by("slug"),
    )


def get_member_asset(asset_id: uuid.UUID) -> Asset:
    return member_asset_queryset().get(id=asset_id)


def get_owned_reservation(reservation_id: uuid.UUID, user: Any) -> Reservation:
    try:
        return owned_reservations_queryset(user).get(id=reservation_id)
    except ObjectDoesNotExist:
        raise


def owned_reservations_queryset(user: Any) -> QuerySet[Reservation]:
    return (
        Reservation.objects.filter(requested_by_user=user)
        .select_related("asset", "asset__parent", "cancelled_by")
        .order_by("-start_at", "-created_at")
    )


def dashboard_reservations(user: Any) -> dict[str, QuerySet[Reservation]]:
    now = require_aware_utc(timezone.now(), field_name="now")
    own = owned_reservations_queryset(user)
    return {
        "active": own.filter(
            status=Reservation.STATUS_CONFIRMED,
            start_at__lte=now,
            effective_end_at__gt=now,
        )[:1],
        "upcoming": own.filter(status=Reservation.STATUS_CONFIRMED, start_at__gt=now)[:5],
    }
