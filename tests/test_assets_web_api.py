from __future__ import annotations

import pytest
from django.core.management import call_command
from django.urls import reverse

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset, AssetTag

BOOTSTRAP_INPUT = "data/bootstrap/assets.yaml"


@pytest.fixture
def staff_user() -> User:
    return User.objects.create_user(
        email="staff-assets@example.com",
        password="not-a-secret",
        is_staff=True,
    )


@pytest.fixture
def ordinary_user() -> User:
    return User.objects.create_user(email="member-assets@example.com", password="not-a-secret")


@pytest.fixture
def imported_assets() -> None:
    call_command("import_bootstrap_assets", input=BOOTSTRAP_INPUT, apply=True)
    # Keep the privacy checks meaningful after replacing the legacy inventory.
    asset = Asset.objects.get(slug="atlas-gpu")
    asset.legacy_source = "synthetic-migration"
    asset.legacy_id = "private-legacy-sentinel"
    asset.physical_locator = "synthetic-private-locator"
    asset.save()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("path_factory", "expected_status"),
    [
        (lambda: "/assets/", 302),
        (
            lambda: reverse("web:asset-detail", args=[Asset.objects.get(slug="atlas-gpu").id]),
            302,
        ),
        (lambda: "/api/v1/assets/", 403),
        (lambda: f"/api/v1/assets/{Asset.objects.get(slug='atlas-gpu').id}/", 403),
    ],
)
def test_asset_inventory_denies_anonymous_users(
    client,
    imported_assets,
    path_factory,
    expected_status: int,
) -> None:
    response = client.get(path_factory())

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("path_factory", "expected_status"),
    [
        (lambda: "/assets/", 200),
        (
            lambda: reverse("web:asset-detail", args=[Asset.objects.get(slug="atlas-gpu").id]),
            200,
        ),
        (lambda: "/api/v1/assets/", 403),
        (lambda: f"/api/v1/assets/{Asset.objects.get(slug='atlas-gpu').id}/", 403),
    ],
)
def test_asset_inventory_denies_non_staff_users(
    client,
    imported_assets,
    ordinary_user: User,
    path_factory,
    expected_status: int,
) -> None:
    client.force_login(ordinary_user)

    response = client.get(path_factory())

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path_factory",
    [
        lambda: "/assets/",
        lambda: reverse("web:asset-detail", args=[Asset.objects.get(slug="atlas-gpu").id]),
        lambda: "/api/v1/assets/",
        lambda: f"/api/v1/assets/{Asset.objects.get(slug='atlas-gpu').id}/",
    ],
)
def test_asset_inventory_allows_staff_users(
    client,
    imported_assets,
    staff_user: User,
    path_factory,
) -> None:
    client.force_login(staff_user)

    response = client.get(path_factory())

    assert response.status_code == 200


@pytest.mark.django_db
def test_staff_web_inventory_list_detail_and_filters(
    client,
    imported_assets,
    staff_user: User,
) -> None:
    client.force_login(staff_user)
    atlas = Asset.objects.get(slug="atlas")

    list_response = client.get(
        "/assets/",
        {"kind": Asset.KIND_GPU, "parent": str(atlas.id), "q": "Atlas"},
    )
    assert list_response.status_code == 200
    assert b"Atlas GPU" in list_response.content
    assert b"Aurora" not in list_response.content

    detail_response = client.get(
        reverse("web:asset-detail", args=[Asset.objects.get(slug="atlas-gpu").id])
    )
    assert detail_response.status_code == 200
    assert b"unverified" in detail_response.content
    assert b"private-legacy-sentinel" not in detail_response.content


@pytest.mark.django_db
def test_staff_api_lists_safe_fields_with_filters_and_pagination(
    client, imported_assets, staff_user: User
) -> None:
    tag = AssetTag.objects.create(slug="accelerator", name="Accelerator")
    atlas_gpu = Asset.objects.get(slug="atlas-gpu")
    atlas_gpu.tags.add(tag)
    client.force_login(staff_user)

    response = client.get(
        "/api/v1/assets/",
        {
            "kind": Asset.KIND_GPU,
            "tag": "accelerator",
            "active": "true",
            "reservable": "true",
            "limit": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert len(payload["results"]) == 1
    result = payload["results"][0]
    assert result["slug"] == "atlas-gpu"
    assert result["parent"]["slug"] == "atlas"
    assert result["tags"] == [{"slug": "accelerator", "name": "Accelerator"}]
    assert result["capabilities"] == {}
    forbidden_fields = {"physical_locator", "legacy_source", "legacy_id", "legacy_metadata"}
    assert forbidden_fields.isdisjoint(result)


@pytest.mark.django_db
def test_staff_api_detail_uses_uuid_and_hides_internal_provenance(
    client, imported_assets, staff_user: User
) -> None:
    asset = Asset.objects.get(slug="atlas-gpu")
    asset.legacy_source = "synthetic-migration"
    asset.legacy_id = "private-legacy-sentinel"
    asset.save()
    client.force_login(staff_user)

    response = client.get(f"/api/v1/assets/{asset.id}/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(asset.id)
    assert payload["slug"] == "atlas-gpu"
    assert "private-legacy-sentinel" not in response.content.decode()
    assert "physical_locator" not in payload


@pytest.mark.django_db
def test_staff_api_invalid_filter_returns_400_without_stack_details(
    client, imported_assets, staff_user: User
) -> None:
    client.force_login(staff_user)

    response = client.get("/api/v1/assets/", {"kind": "reservation"})

    assert response.status_code == 400
    assert "Traceback" not in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "params",
    [
        {"parent": "not-a-uuid"},
        {"active": "maybe"},
        {"reservable": "maybe"},
    ],
)
def test_staff_api_invalid_filter_variants_return_400(
    client,
    imported_assets,
    staff_user: User,
    params: dict[str, str],
) -> None:
    client.force_login(staff_user)

    response = client.get("/api/v1/assets/", params)

    assert response.status_code == 400
    assert "Traceback" not in response.content.decode()


@pytest.mark.django_db
def test_staff_api_missing_detail_returns_404(client, imported_assets, staff_user: User) -> None:
    client.force_login(staff_user)

    response = client.get("/api/v1/assets/00000000-0000-0000-0000-000000000001/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_staff_api_pagination_is_bounded(client, imported_assets, staff_user: User) -> None:
    client.force_login(staff_user)

    response = client.get("/api/v1/assets/", {"limit": 2, "offset": 1})

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 14
    assert len(payload["results"]) == 2
    assert "limit=2" in payload["next"]
    assert "offset=3" in payload["next"]
    assert "limit=2" in payload["previous"]


@pytest.mark.django_db
def test_api_root_reports_asset_endpoint(client) -> None:
    response = client.get("/api/v1/")

    assert response.status_code == 200
    assert response.json()["endpoints"] == {
        "assets": "/api/v1/assets/",
        "availability": "/api/v1/assets/{asset_id}/availability/",
        "me": "/api/v1/me/",
        "reservations": "/api/v1/reservations/",
    }
