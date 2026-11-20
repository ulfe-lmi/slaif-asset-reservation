from __future__ import annotations

import pytest
from django.contrib import admin
from django.contrib.auth.models import Group

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.admin import AssetAdmin
from slaif_reservation.assets.models import Asset, AssetTag


def test_asset_and_tag_are_registered_in_admin() -> None:
    assert Asset in admin.site._registry
    assert AssetTag in admin.site._registry


def test_asset_admin_search_filters_readonly_and_delete_policy(rf) -> None:
    model_admin = admin.site._registry[Asset]
    assert isinstance(model_admin, AssetAdmin)
    assert "legacy_id" in model_admin.search_fields
    assert {"kind", "active", "reservable", "verification_required", "booking_mode"}.issubset(
        set(model_admin.list_filter)
    )
    assert {"legacy_source", "legacy_id", "legacy_metadata"}.issubset(
        set(model_admin.readonly_fields)
    )

    request = rf.get("/admin/assets/asset/")
    assert model_admin.has_delete_permission(request) is False
    assert "delete_selected" not in model_admin.get_actions(request)


@pytest.mark.django_db
def test_asset_admin_queryset_uses_parent_and_tags(rf) -> None:
    request = rf.get("/admin/assets/asset/")
    queryset = admin.site._registry[Asset].get_queryset(request)

    assert queryset.query.select_related


def test_asset_admin_excluded_groups_field_is_independent_and_wired() -> None:
    """SAR-057 admin surface: the deny-list field is editable in the same
    "Booking access" fieldset as the allow-list, uses the same
    filter-horizontal widget and carries its own rendered help,
    independently of ``booking_restricted``."""
    model_admin = admin.site._registry[Asset]
    assert "excluded_booking_groups" in AssetAdmin.form.base_fields
    assert "booking_restricted" in AssetAdmin.form.base_fields
    assert set(model_admin.filter_horizontal) == {
        "tags",
        "allowed_booking_groups",
        "excluded_booking_groups",
    }
    # Landed in the "Booking access" fieldset, right after the allow-list.
    booking_set = next(
        (options for title, options in model_admin.fieldsets if title == "Booking access"),
        None,
    )
    assert booking_set is not None
    assert list(booking_set["fields"]) == [
        "booking_restricted",
        "allowed_booking_groups",
        "excluded_booking_groups",
    ]

    # The ModelForm wires the rendered help id for accessibility.
    form = AssetAdmin.form()
    widget = form.fields["excluded_booking_groups"].widget
    assert widget.attrs.get("aria-describedby") == "id_excluded_booking_groups_helptext"


@pytest.mark.django_db
def test_asset_admin_save_sets_exclusions_independently_of_restriction(
    client,
) -> None:
    """SAR-057 admin save: an operator can configure exclusions on an
    UNRESTRICTED asset (booking_restricted stays False) and the allow-list
    is untouched; the form round-trips through the real change URL."""
    admin = User.objects.create_superuser(
        email="denylist-admin@example.com", password="not-a-secret"
    )
    client.force_login(admin)
    asset = Asset.objects.create(
        slug="denylist-admin-asset",
        name="Denylist Admin Asset",
        kind=Asset.KIND_GPU,
        active=True,
        reservable=True,
    )
    allow_group = Group.objects.create(name="denylist-allow")
    exclude_group = Group.objects.create(name="denylist-exclude")
    asset.allowed_booking_groups.add(allow_group)

    response = client.post(
        f"/admin/assets/asset/{asset.id}/change/",
        {
            "slug": "denylist-admin-asset",
            "name": "Denylist Admin Asset",
            "kind": Asset.KIND_GPU,
            "booking_mode": Asset.BOOKING_EXCLUSIVE,
            "timezone": "Europe/Ljubljana",
            "active": "on",
            "reservable": "on",
            "verification_required": "on",
            # booking_restricted deliberately NOT posted: stays False.
            "allowed_booking_groups": [allow_group.id],
            "excluded_booking_groups": [exclude_group.id],
            "capabilities": "{}",
            "_save": "Save",
        },
        follow=True,
    )
    assert response.status_code == 200
    asset.refresh_from_db()
    assert asset.booking_restricted is False
    assert list(asset.allowed_booking_groups.values_list("id", flat=True)) == [allow_group.id]
    assert list(asset.excluded_booking_groups.values_list("id", flat=True)) == [exclude_group.id]
