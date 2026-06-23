from __future__ import annotations

from typing import Any, cast

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from slaif_reservation.reservations.models import Reservation, ReservationPolicy


class NoDeleteAdminMixin:
    def has_delete_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def get_actions(self, request: HttpRequest) -> dict[str, Any]:
        actions = cast(dict[str, Any], super().get_actions(request))  # type: ignore[misc]
        actions.pop("delete_selected", None)
        return actions


class ReadOnlyAdminMixin(NoDeleteAdminMixin):
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False


@admin.register(ReservationPolicy)
class ReservationPolicyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = [
        "name",
        "asset",
        "active",
        "min_duration_minutes",
        "max_duration_minutes",
        "booking_horizon_days",
        "min_lead_minutes",
        "purpose_required",
    ]
    list_filter = ["active", "purpose_required", "asset"]
    search_fields = ["name", "asset__slug", "asset__name"]
    readonly_fields = [
        "id",
        "name",
        "asset",
        "active",
        "min_duration_minutes",
        "max_duration_minutes",
        "booking_horizon_days",
        "min_lead_minutes",
        "cancellation_cutoff_minutes",
        "max_upcoming_per_principal",
        "max_concurrent_per_principal",
        "purpose_required",
        "created_at",
        "updated_at",
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet[ReservationPolicy]:
        return super().get_queryset(request).select_related("asset")


@admin.register(Reservation)
class ReservationAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = [
        "id",
        "asset",
        "requested_by_user",
        "status",
        "source",
        "start_at",
        "end_at",
        "effective_end_at",
    ]
    list_filter = ["status", "source", "asset"]
    search_fields = ["id", "asset__slug", "asset__name", "requested_by_user__email"]
    readonly_fields = [
        "id",
        "asset",
        "requested_by_user",
        "source",
        "status",
        "start_at",
        "end_at",
        "effective_end_at",
        "purpose",
        "released_at",
        "cancelled_at",
        "cancelled_by",
        "cancellation_reason",
        "created_at",
        "updated_at",
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Reservation]:
        return (
            super()
            .get_queryset(request)
            .select_related("asset", "requested_by_user", "cancelled_by")
        )
