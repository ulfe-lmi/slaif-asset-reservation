from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from django.db.models import Q, QuerySet

from slaif_reservation.assets.models import Asset


class AssetFilterError(ValueError):
    pass


@dataclass(frozen=True)
class AssetFilters:
    kind: str | None = None
    parent: uuid.UUID | None = None
    tag: str | None = None
    active: bool | None = None
    reservable: bool | None = None
    search: str | None = None


def parse_asset_filters(params: Any) -> AssetFilters:
    kind = _optional(params, "kind")
    if kind and kind not in {choice for choice, _label in Asset.KIND_CHOICES}:
        raise AssetFilterError("Invalid asset kind filter.")

    parent = None
    raw_parent = _optional(params, "parent")
    if raw_parent:
        try:
            parent = uuid.UUID(raw_parent)
        except ValueError as exc:
            raise AssetFilterError("Invalid parent filter.") from exc

    tag = _optional(params, "tag")
    active = _optional_bool(params, "active")
    reservable = _optional_bool(params, "reservable")
    search = _optional(params, "q") or _optional(params, "search")

    return AssetFilters(
        kind=kind,
        parent=parent,
        tag=tag,
        active=active,
        reservable=reservable,
        search=search,
    )


def asset_inventory_queryset(filters: AssetFilters | None = None) -> QuerySet[Asset]:
    queryset = Asset.objects.select_related("parent").prefetch_related("tags").order_by("slug")
    if filters is None:
        return queryset

    if filters.kind:
        queryset = queryset.filter(kind=filters.kind)
    if filters.parent:
        queryset = queryset.filter(parent_id=filters.parent)
    if filters.tag:
        queryset = queryset.filter(tags__slug=filters.tag)
    if filters.active is not None:
        queryset = queryset.filter(active=filters.active)
    if filters.reservable is not None:
        queryset = queryset.filter(reservable=filters.reservable)
    if filters.search:
        queryset = queryset.filter(
            Q(name__icontains=filters.search)
            | Q(slug__icontains=filters.search)
            | Q(description__icontains=filters.search)
        )
    return queryset.distinct()


def get_asset_for_inventory(asset_id: uuid.UUID) -> Asset:
    return asset_inventory_queryset().get(id=asset_id)


def _optional(params: Any, key: str) -> str | None:
    value = params.get(key)
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _optional_bool(params: Any, key: str) -> bool | None:
    value = _optional(params, key)
    if value is None:
        return None
    normalized = value.lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise AssetFilterError(f"Invalid {key} filter.")
