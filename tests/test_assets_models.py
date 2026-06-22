from __future__ import annotations

import uuid

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from slaif_reservation.assets.models import Asset, AssetTag
from slaif_reservation.assets.validators import validate_capabilities


def machine(**overrides: object) -> Asset:
    values = {
        "slug": "machine-a",
        "name": "Machine A",
        "kind": Asset.KIND_MACHINE,
        "active": True,
        "reservable": False,
    }
    values.update(overrides)
    return Asset.objects.create(**values)


@pytest.mark.django_db
def test_asset_tag_and_asset_use_uuid_identity() -> None:
    tag = AssetTag.objects.create(slug="a100", name="A100")
    asset = machine()

    assert isinstance(tag.id, uuid.UUID)
    assert isinstance(asset.id, uuid.UUID)
    assert asset.timezone == "Europe/Ljubljana"


@pytest.mark.django_db
def test_child_asset_hierarchy_is_valid() -> None:
    parent = machine()
    gpu = Asset(
        parent=parent,
        slug="machine-a-gpu-0",
        name="Machine A GPU 0",
        kind=Asset.KIND_GPU,
        active=True,
        reservable=True,
    )

    gpu.full_clean()
    gpu.save()

    assert gpu.parent == parent


@pytest.mark.django_db
def test_parent_hierarchy_validation_rejects_invalid_shapes() -> None:
    parent = machine()
    child = Asset.objects.create(
        parent=parent,
        slug="machine-a-gpu-0",
        name="Machine A GPU 0",
        kind=Asset.KIND_GPU,
        active=True,
        reservable=True,
    )

    parent.parent = parent
    with pytest.raises(ValidationError, match="cannot parent itself"):
        parent.full_clean()

    machine_with_parent = Asset(
        parent=parent,
        slug="machine-b",
        name="Machine B",
        kind=Asset.KIND_MACHINE,
    )
    with pytest.raises(ValidationError, match="Machine assets cannot have a parent"):
        machine_with_parent.full_clean()

    grandchild = Asset(
        parent=child,
        slug="machine-a-gpu-0-slice",
        name="Machine A GPU 0 slice",
        kind=Asset.KIND_OTHER,
    )
    with pytest.raises(ValidationError, match="parent must be a machine"):
        grandchild.full_clean()


@pytest.mark.django_db
def test_inactive_assets_cannot_be_reservable() -> None:
    asset = Asset(
        slug="inactive-gpu",
        name="Inactive GPU",
        kind=Asset.KIND_GPU,
        active=False,
        reservable=True,
    )

    with pytest.raises(ValidationError, match="Inactive assets cannot be reservable"):
        asset.full_clean()

    with pytest.raises(IntegrityError), transaction.atomic():
        Asset.objects.create(
            slug="inactive-db",
            name="Inactive DB",
            kind=Asset.KIND_GPU,
            active=False,
            reservable=True,
        )


@pytest.mark.django_db
def test_legacy_provenance_pair_is_unique_when_present() -> None:
    Asset.objects.create(
        slug="legacy-a",
        name="Legacy A",
        kind=Asset.KIND_GPU,
        legacy_source="smartscheduling",
        legacy_id="resource-a",
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        Asset.objects.create(
            slug="legacy-b",
            name="Legacy B",
            kind=Asset.KIND_GPU,
            legacy_source="smartscheduling",
            legacy_id="resource-a",
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "values",
    [
        {"legacy_source": "smartscheduling", "legacy_id": None},
        {"legacy_source": None, "legacy_id": "resource-a"},
        {"legacy_source": "", "legacy_id": ""},
        {"legacy_source": "   ", "legacy_id": "resource-a"},
        {"legacy_source": "smartscheduling", "legacy_id": "   "},
    ],
)
def test_legacy_provenance_requires_meaningful_paired_values(
    values: dict[str, str | None],
) -> None:
    asset = Asset(slug="legacy-invalid", name="Legacy Invalid", kind=Asset.KIND_GPU, **values)

    with pytest.raises(ValidationError, match="Legacy source and legacy ID"):
        asset.full_clean()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "values",
    [
        {"legacy_source": "", "legacy_id": ""},
        {"legacy_source": "   ", "legacy_id": "resource-a"},
        {"legacy_source": "smartscheduling", "legacy_id": "   "},
    ],
)
def test_legacy_provenance_meaningfulness_is_database_enforced(
    values: dict[str, str],
) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        Asset.objects.create(
            slug="legacy-db-invalid",
            name="Legacy DB Invalid",
            kind=Asset.KIND_GPU,
            **values,
        )


@pytest.mark.parametrize(
    "capabilities",
    [
        [],
        {"vendor": ""},
        {"memory_gib": True},
        {"memory_gib": 0},
        {"device_uuid": "GPU-secret"},
        {"unexpected": "value"},
    ],
)
def test_capability_validation_rejects_unsafe_or_unknown_values(capabilities: object) -> None:
    with pytest.raises(ValidationError):
        validate_capabilities(capabilities)


def test_capability_validation_allows_known_normalized_values() -> None:
    validate_capabilities(
        {
            "vendor": "NVIDIA",
            "model": "A100-SXM4-80GB",
            "memory_gib": 80,
            "accelerator_family": "ampere",
        }
    )
    validate_capabilities({})


@pytest.mark.django_db
def test_timezone_and_booking_mode_fail_closed() -> None:
    bad_timezone = Asset(
        slug="bad-tz",
        name="Bad timezone",
        kind=Asset.KIND_GPU,
        timezone="Not/AZone",
    )
    with pytest.raises(ValidationError, match="Timezone must resolve"):
        bad_timezone.full_clean()

    bad_booking = Asset(
        slug="bad-booking",
        name="Bad booking",
        kind=Asset.KIND_GPU,
        booking_mode="shared",
    )
    with pytest.raises(ValidationError, match="Unsupported booking mode"):
        bad_booking.full_clean()
