from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from slaif_reservation.audit.models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = [
        "occurred_at",
        "action",
        "target_type",
        "target_id",
        "actor_user",
        "source",
        "correlation_id",
    ]
    list_filter = ["action", "source", "target_type"]
    search_fields = ["target_type", "target_id", "correlation_id"]
    readonly_fields = [
        "id",
        "occurred_at",
        "actor_user",
        "action",
        "target_type",
        "target_id",
        "correlation_id",
        "source",
        "metadata",
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet[AuditEvent]:
        return super().get_queryset(request).select_related("actor_user")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: AuditEvent | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: AuditEvent | None = None) -> bool:
        return False

    def get_actions(self, request: HttpRequest) -> dict[str, Any]:
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions
