from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from slaif_reservation.assets.models import Asset, AssetTag


@admin.register(AssetTag)
class AssetTagAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ["slug", "name", "created_at", "updated_at"]
    search_fields = ["slug", "name", "description"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = [
        "slug",
        "name",
        "kind",
        "parent",
        "active",
        "reservable",
        "verification_required",
        "booking_mode",
    ]
    list_filter = ["kind", "active", "reservable", "verification_required", "booking_mode", "tags"]
    search_fields = ["name", "slug", "legacy_id"]
    autocomplete_fields = ["parent", "tags"]
    filter_horizontal = ["tags"]
    readonly_fields = ["legacy_source", "legacy_id", "legacy_metadata", "created_at", "updated_at"]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "parent",
                    "slug",
                    "name",
                    "kind",
                    "booking_mode",
                    "description",
                    "location",
                    "timezone",
                ]
            },
        ),
        (
            "State",
            {
                "fields": [
                    "active",
                    "reservable",
                    "verification_required",
                ]
            },
        ),
        (
            "Capabilities and tags",
            {
                "fields": [
                    "capabilities",
                    "tags",
                ]
            },
        ),
        (
            "Internal operations",
            {
                "fields": [
                    "physical_locator",
                    "legacy_source",
                    "legacy_id",
                    "legacy_metadata",
                ]
            },
        ),
        ("Timestamps", {"fields": ["created_at", "updated_at"]}),
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Asset]:
        return super().get_queryset(request).select_related("parent").prefetch_related("tags")

    def has_delete_permission(self, request: HttpRequest, obj: Asset | None = None) -> bool:
        return False

    def get_actions(self, request: HttpRequest) -> dict[str, Any]:
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions
