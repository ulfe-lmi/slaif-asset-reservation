from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.db.models import QuerySet
from django.http import HttpRequest

from slaif_reservation.accounts.models import ApiToken, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):  # type: ignore[type-arg]
    ordering = ["email"]
    list_display = ["email", "display_name", "is_staff", "is_service_account", "is_active"]
    search_fields = ["email", "display_name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("display_name", "timezone", "is_service_account")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_superuser"),
            },
        ),
    )
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ApiToken)
class ApiTokenAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = [
        "id",
        "owner",
        "name",
        "display_prefix",
        "scopes",
        "created_at",
        "expires_at",
        "revoked_at",
        "last_used_at",
    ]
    list_filter = ["revoked_at", "expires_at", "created_at"]
    search_fields = ["owner__email", "name", "id"]
    readonly_fields = [
        "id",
        "owner",
        "name",
        "display_prefix",
        "scopes",
        "created_at",
        "expires_at",
        "revoked_at",
        "revoked_by",
        "last_used_at",
    ]
    exclude = ["verifier"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[ApiToken]:
        return super().get_queryset(request).select_related("owner", "revoked_by")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: ApiToken | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: ApiToken | None = None) -> bool:
        return False

    def get_actions(self, request: HttpRequest) -> dict[str, Any]:
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions
