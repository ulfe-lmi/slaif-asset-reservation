from __future__ import annotations

from typing import Any

from django import forms
from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from slaif_reservation.assets.models import Asset, AssetTag


class AssetTagAdminForm(forms.ModelForm):  # type: ignore[type-arg]
    class Meta:
        model = AssetTag
        fields = ["slug", "name", "description"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        _wire(
            self,
            {
                "name": _("Display name of the tag, shown in the member and staff asset lists."),
                "slug": _(
                    "Stable identifier, generated from the name. Used in "
                    "filters; change it only together with any saved links."
                ),
                "description": _("Optional description, visible to staff only."),
            },
        )


def _wire(form: Any, help_by_field: dict[str, Any]) -> None:
    for name, help_text in help_by_field.items():
        field = form.fields.get(name)
        if field is None:
            continue
        field.help_text = help_text
        # The admin fieldset renders the help block as
        # ``<div class="help" id="<auto_id>_helptext">``; wire the control
        # to that same id.
        field.widget.attrs["aria-describedby"] = f"id_{name}_helptext"


class AssetAdminForm(forms.ModelForm):  # type: ignore[type-arg]
    class Meta:
        model = Asset
        fields = [
            "parent",
            "slug",
            "name",
            "kind",
            "booking_mode",
            "description",
            "location",
            "timezone",
            "active",
            "reservable",
            "verification_required",
            "booking_restricted",
            "allowed_booking_groups",
            "capabilities",
            "tags",
            "physical_locator",
        ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        _wire(
            self,
            {
                "parent": _(
                    "The machine this asset belongs to. Only a machine can "
                    "be the parent of a child asset, and a machine itself "
                    "never has a parent, so leave this empty for machines."
                ),
                "slug": _(
                    "Stable label used for display and search (lists, "
                    "filters and search boxes). It must stay unique. The "
                    "current detail and API routes address assets by UUID, "
                    "so changing the slug does not change those URLs; it "
                    "changes what searches and filters match."
                ),
                "name": _("Human-readable name shown to members and staff."),
                "kind": _(
                    "What kind of resource this is. Only a machine can take "
                    "children; a machine itself cannot have a parent. "
                    "Booking rules apply per policy."
                ),
                "booking_mode": _(
                    "How the asset is shared. Only 'Exclusive' is supported: "
                    "a new booking must not overlap an existing one."
                ),
                "description": _(
                    "Shown to members on the asset page. Plain text; keep "
                    "technical claims to verified inventory."
                ),
                "location": _(
                    "Internal room or location label for staff. Not shown to "
                    "members and not part of the API."
                ),
                "timezone": _(
                    "Stored display metadata, shown as 'Asset timezone' on "
                    "the asset page. It does not drive booking or "
                    "availability: availability is shown in each member's "
                    "own profile timezone."
                ),
                "active": _(
                    "Inactive assets are hidden from members and cannot be "
                    "booked. An asset can only be reservable while active."
                ),
                "reservable": _("Only reservable assets offer the reserve action to members."),
                "booking_restricted": _(
                    "Whether only specific approved groups may book this asset. "
                    "Unrestricted: any user holding the booking permission "
                    "(reservations.book_assets) may book it. Restricted: only "
                    "users who belong to at least one allowed group below; a "
                    "restricted asset with no allowed groups denies everyone. "
                    "Only this exact asset is checked - the parent machine's "
                    "setting never applies to it and vice versa."
                ),
                "allowed_booking_groups": _(
                    "Existing permission groups whose members may book this "
                    "asset while it is restricted. Membership in ANY ONE "
                    "selected group is enough; group grants and individual "
                    "permissions combine additively. Selecting groups here "
                    "grants no other access, and members still need the global "
                    "reservations.book_assets permission. These group names are "
                    "operator configuration, not authorization constants. The "
                    "list is ignored while the asset is unrestricted."
                ),
                "verification_required": _(
                    "Displays 'unverified' to members until verified. A "
                    "display flag — no verification workflow is enforced yet."
                ),
                "capabilities": _(
                    "Verified normalized capabilities as a JSON object "
                    "(strings, numbers, booleans, lists and nested objects). "
                    "Shown to members as 'Normalized capabilities'."
                ),
                "tags": _("Labels used to filter in the member and staff asset lists."),
                "physical_locator": _(
                    "Internal physical location for operators. Never shown "
                    "to members or in the API."
                ),
            },
        )


@admin.register(AssetTag)
class AssetTagAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    form = AssetTagAdminForm
    list_display = ["slug", "name", "created_at", "updated_at"]
    search_fields = ["slug", "name", "description"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    form = AssetAdminForm

    @property
    def media(self) -> forms.Media:
        # Binds the rendered help of the generated dual-select list boxes
        # (allowed_booking_groups, tags) via the narrow local helper.
        return super().media + forms.Media(js=["web/admin-form-guidance.js"])

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
    list_filter = [
        "kind",
        "active",
        "reservable",
        "booking_restricted",
        "verification_required",
        "booking_mode",
        "tags",
    ]
    search_fields = ["name", "slug", "legacy_id"]
    autocomplete_fields = ["parent", "tags"]
    filter_horizontal = ["tags", "allowed_booking_groups"]
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
            "Booking access",
            {
                "fields": [
                    "booking_restricted",
                    "allowed_booking_groups",
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

    def formfield_for_foreignkey(self, db_field: Any, request: HttpRequest, **kwargs: Any) -> Any:
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "parent" and field is not None:
            widget = field.widget
            # The admin wraps FK widgets (e.g. autocomplete); the rendered
            # control is the inner widget, so bind help to it.
            if hasattr(widget, "widget"):
                widget = widget.widget
            widget.attrs["aria-describedby"] = "id_parent_helptext"
        return field

    def get_queryset(self, request: HttpRequest) -> QuerySet[Asset]:
        return super().get_queryset(request).select_related("parent").prefetch_related("tags")

    def has_delete_permission(self, request: HttpRequest, obj: Asset | None = None) -> bool:
        return False

    def get_actions(self, request: HttpRequest) -> dict[str, Any]:
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions
