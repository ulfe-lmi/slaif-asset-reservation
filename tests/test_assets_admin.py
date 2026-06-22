from __future__ import annotations

import pytest
from django.contrib import admin

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
