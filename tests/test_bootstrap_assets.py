from __future__ import annotations

from copy import deepcopy
from datetime import timedelta
from io import StringIO
from pathlib import Path

import pytest
import yaml
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.bootstrap import BootstrapAssetError, load_bootstrap_plan
from slaif_reservation.assets.models import Asset
from slaif_reservation.reservations.exceptions import ReservationDomainError
from slaif_reservation.reservations.services import create_reservation

BOOTSTRAP_INPUT = Path("data/bootstrap/assets.yaml")
SCHEMA = Path("data/bootstrap/assets.schema.json")
EXPECTED = {
    "atlas": ("Atlas", "machine", None, "AI & Data Lab", True, False),
    "atlas-gpu": ("Atlas GPU", "gpu", "atlas", "AI & Data Lab", True, True),
    "atlas-cpu-pool": ("Atlas CPU pool", "cpu_pool", "atlas", "AI & Data Lab", True, True),
    "aurora-microscope": ("Aurora", "other", None, "Microscopy Room", True, True),
    "forge-printer": ("Forge", "other", None, "Prototype Workshop", True, True),
    "cutline-laser": ("Cutline", "other", None, "Prototype Workshop", True, True),
    "vector-mill": ("Vector", "other", None, "Prototype Workshop", True, True),
    "climatebox-chamber": ("ClimateBox", "other", None, "Environmental Test Lab", True, True),
    "scopebench": ("ScopeBench", "other", None, "Electronics Lab", True, True),
    "robocell": ("RoboCell", "other", None, "Robotics Cell", True, True),
    "thermocam-kit": ("ThermoCam", "other", None, "Field Equipment Store", True, True),
    "simworks-license": ("SimWorks", "service", None, "Shared Digital Services", True, True),
    "precision-support": ("Precision", "service", None, "Shared Digital Services", True, True),
    "calibra-reference-kit": ("Calibra", "other", None, "Electronics Lab", False, False),
}


def _load_document() -> dict:
    return yaml.safe_load(BOOTSTRAP_INPUT.read_text(encoding="utf-8"))


def _write_document(tmp_path: Path, document: dict) -> Path:
    path = tmp_path / "assets.yaml"
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    path.with_name("assets.schema.json").write_text(SCHEMA.read_text(), encoding="utf-8")
    return path


def test_demo_is_exact_generic_inventory_without_site_provenance() -> None:
    plan = load_bootstrap_plan(BOOTSTRAP_INPUT)
    assert plan.planned_count == 14
    assert {
        r.slug: (r.name, r.kind, r.parent_slug, r.location, r.active, r.reservable)
        for r in plan.records
    } == EXPECTED
    assert {r.kind for r in plan.records} == {kind for kind, _ in Asset.KIND_CHOICES}
    assert all(r.timezone == "UTC" and r.description for r in plan.records)
    assert all(r.verification_required for r in plan.records)
    document = _load_document()
    assert set(document) == {"schema_version", "defaults", "assets"}
    assert document["schema_version"] == 2
    allowed = {"slug", "name", "kind", "parent", "description", "location", "active", "reservable"}
    assert all(set(asset) <= allowed for asset in document["assets"])
    # The exact identities above plus a field allowlist prevent migration or
    # hardware-identification data from becoming part of the product demo again.
    text = BOOTSTRAP_INPUT.read_text().lower()
    assert not any(
        word in text
        for word in ("smartscheduling", "lmi", "hostname", "legacy", "account", "physical_locator")
    )


def test_malformed_yaml_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "assets.yaml"
    path.write_text("assets: [", encoding="utf-8")
    with pytest.raises(BootstrapAssetError, match="Invalid YAML"):
        load_bootstrap_plan(path)


@pytest.mark.django_db
@pytest.mark.parametrize("apply_mode", [False, True])
@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda d: d.__setitem__("schema_version", 1), "schema validation failed"),
        (lambda d: d.pop("assets"), "schema validation failed"),
        (lambda d: d["assets"][1].__setitem__("kind", "printer"), "schema validation failed"),
        (lambda d: d["assets"][1].__setitem__("slug", "a" * 121), "schema validation failed"),
        (lambda d: d["assets"][1].__setitem__("name", "A" * 181), "schema validation failed"),
        (lambda d: d["assets"][1].__setitem__("legacy", {}), "schema validation failed"),
        (lambda d: d["assets"].append(deepcopy(d["assets"][0])), "duplicate asset slug"),
        (lambda d: d["assets"][1].__setitem__("parent", "missing"), "Unknown parent"),
        (lambda d: d["assets"][1].__setitem__("parent", "atlas-gpu"), "cannot parent itself"),
        (lambda d: d["assets"][0].__setitem__("parent", "atlas-gpu"), "cycle"),
        (
            lambda d: d["assets"][0].__setitem__("parent", "aurora-microscope"),
            "Machine assets cannot",
        ),
        (
            lambda d: d["assets"][1].__setitem__("parent", "aurora-microscope"),
            "parent must be a machine",
        ),
        (lambda d: d["assets"][1].__setitem__("kind", "machine"), "Machine assets cannot"),
        (lambda d: d["defaults"].__setitem__("timezone", "Not/AZone"), "Timezone must resolve"),
        (lambda d: d["assets"][1].__setitem__("timezone", "Not/AZone"), "Timezone must resolve"),
        (
            lambda d: d["assets"][1].__setitem__("active", False),
            "Inactive assets cannot be reservable",
        ),
    ],
)
def test_invalid_input_fails_before_writes(
    tmp_path: Path, mutator, message: str, apply_mode: bool
) -> None:
    existing = Asset.objects.create(slug="operator-asset", name="Operator maintained", kind="other")
    document = _load_document()
    mutator(document)
    path = _write_document(tmp_path, document)
    with pytest.raises(CommandError, match=message):
        call_command("import_bootstrap_assets", input=str(path), apply=apply_mode)
    assert Asset.objects.count() == 1
    existing.refresh_from_db()
    assert existing.name == "Operator maintained"


@pytest.mark.django_db
@pytest.mark.parametrize("reverse_input", [False, True])
def test_apply_is_order_independent_and_idempotent(tmp_path: Path, reverse_input: bool) -> None:
    document = _load_document()
    if reverse_input:
        document["assets"].reverse()
    path = _write_document(tmp_path, document)
    first = StringIO()
    call_command("import_bootstrap_assets", input=str(path), apply=True, stdout=first)
    assert "created=14" in first.getvalue()
    assert {
        a.slug: (
            a.name,
            a.kind,
            a.parent.slug if a.parent else None,
            a.location,
            a.active,
            a.reservable,
        )
        for a in Asset.objects.select_related("parent")
    } == EXPECTED
    assert all(
        a.legacy_source is None
        and a.legacy_id is None
        and a.legacy_metadata == {}
        and a.physical_locator == ""
        and a.capabilities == {}
        for a in Asset.objects.all()
    )
    identities = dict(Asset.objects.values_list("slug", "id"))
    second = StringIO()
    call_command("import_bootstrap_assets", input=str(path), apply=True, stdout=second)
    assert "created=0" in second.getvalue()
    assert "unchanged=14" in second.getvalue()
    assert dict(Asset.objects.values_list("slug", "id")) == identities


@pytest.mark.django_db
def test_repeated_apply_preserves_configured_booking_access(tmp_path: Path) -> None:
    """Operator-configured booking ACL is bootstrap data the importer never owns.

    The generic bootstrap format has no booking fields; existing matching
    records are reused without writes, so a repeated apply must preserve
    the operator's ``booking_restricted`` / allowed groups exactly.
    """
    from django.contrib.auth.models import Group

    path = _write_document(tmp_path, _load_document())
    first = StringIO()
    call_command("import_bootstrap_assets", input=str(path), apply=True, stdout=first)
    assert "created=14" in first.getvalue()

    target = Asset.objects.get(slug="atlas-gpu")
    group = Group.objects.create(name="bootstrap-booking-group")
    target.booking_restricted = True
    target.save(update_fields=["booking_restricted", "updated_at"])
    target.allowed_booking_groups.add(group)

    second = StringIO()
    call_command("import_bootstrap_assets", input=str(path), apply=True, stdout=second)
    assert "created=0" in second.getvalue()
    assert "unchanged=14" in second.getvalue()

    target.refresh_from_db()
    assert target.booking_restricted is True
    assert list(target.allowed_booking_groups.values_list("id", flat=True)) == [group.id]


@pytest.mark.django_db
def test_default_dry_run_writes_nothing() -> None:
    output = StringIO()
    call_command("import_bootstrap_assets", input=str(BOOTSTRAP_INPUT), stdout=output)
    assert Asset.objects.count() == 0
    assert "mode=dry-run" in output.getvalue()
    assert "planned=14" in output.getvalue()
    assert "created=14" in output.getvalue()


@pytest.mark.django_db
def test_import_conflict_preserves_existing_records() -> None:
    existing = Asset.objects.create(slug="atlas", name="Operator maintained", kind="machine")
    with pytest.raises(CommandError, match="conflicts"):
        call_command("import_bootstrap_assets", input=str(BOOTSTRAP_INPUT), apply=True)
    assert Asset.objects.count() == 1
    existing.refresh_from_db()
    assert existing.name == "Operator maintained"


@pytest.mark.django_db
def test_apply_rolls_back_after_mid_import_failure(monkeypatch) -> None:
    original = Asset.save
    calls = 0

    def fail_second_save(self, *args, **kwargs):
        nonlocal calls
        calls += 1
        original(self, *args, **kwargs)
        if calls == 2:
            raise BootstrapAssetError("Injected import failure")

    monkeypatch.setattr(Asset, "save", fail_second_save)
    with pytest.raises(CommandError, match="Injected import failure"):
        call_command("import_bootstrap_assets", input=str(BOOTSTRAP_INPUT), apply=True)
    assert calls == 2
    assert Asset.objects.count() == 0


@pytest.mark.django_db
def test_timezone_and_verification_override_are_preserved(tmp_path: Path) -> None:
    document = _load_document()
    document["assets"][1]["timezone"] = "Europe/Paris"
    document["assets"][1]["verification_required"] = False
    path = _write_document(tmp_path, document)
    call_command("import_bootstrap_assets", input=str(path), apply=True)
    asset = Asset.objects.get(slug="atlas-gpu")
    assert asset.timezone == "Europe/Paris"
    assert asset.verification_required is False


@pytest.mark.django_db
@pytest.mark.parametrize("slug", list(EXPECTED))
def test_demo_booking_uses_existing_default_policy_and_asset_rules(slug: str) -> None:
    call_command("import_bootstrap_assets", input=str(BOOTSTRAP_INPUT), apply=True)
    call_command("initialize_default_policy")
    member = User.objects.create_user(email="demo-check@example.test", password="not-a-secret")
    # A16: the demo member books a demo reservation, so it carries the
    # explicit baseline booking capability (real Permission row).
    member.user_permissions.add(
        Permission.objects.get(codename="book_assets", content_type__app_label="reservations")
    )
    asset = Asset.objects.get(slug=slug)
    kwargs = dict(
        asset=asset,
        requested_by_user=member,
        start_at=timezone.now() + timedelta(hours=1),
        end_at=timezone.now() + timedelta(hours=2),
        purpose="Demo reservation",
        source="web",
    )
    if not asset.active or not asset.reservable:
        with pytest.raises(ReservationDomainError) as error:
            create_reservation(**kwargs)
        assert error.value.code == (
            "asset_inactive" if not asset.active else "asset_not_reservable"
        )
    else:
        result = create_reservation(**kwargs)
        assert result.reservation.asset_id == asset.id
