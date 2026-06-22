from __future__ import annotations

from io import StringIO
from pathlib import Path

import pytest
import yaml
from django.core.management import call_command
from django.core.management.base import CommandError

from slaif_reservation.assets.bootstrap import BootstrapAssetError, load_bootstrap_plan
from slaif_reservation.assets.models import Asset

BOOTSTRAP_INPUT = Path("data/bootstrap/assets.yaml")


def test_bootstrap_file_is_schema_valid_and_plans_expected_counts() -> None:
    plan = load_bootstrap_plan(BOOTSTRAP_INPUT)

    assert plan.planned_count == 47
    assert len([record for record in plan.records if record.kind == Asset.KIND_MACHINE]) == 17
    assert len([record for record in plan.records if record.kind == Asset.KIND_GPU]) == 30
    assert [excluded.legacy_id for excluded in plan.excluded] == ["chatgptpro"]


def test_malformed_yaml_is_rejected(tmp_path: Path) -> None:
    bad_yaml = tmp_path / "assets.yaml"
    bad_yaml.write_text("machines: [", encoding="utf-8")

    with pytest.raises(BootstrapAssetError, match="Invalid YAML"):
        load_bootstrap_plan(bad_yaml)


def test_schema_invalid_bootstrap_is_rejected(tmp_path: Path) -> None:
    document = _load_document()
    document.pop("machines")
    path = _write_document(tmp_path, document)

    with pytest.raises(BootstrapAssetError, match="schema validation failed"):
        load_bootstrap_plan(path, Path("data/bootstrap/assets.schema.json"))


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (
            lambda document: document["machines"].__setitem__(1, document["machines"][0]),
            "duplicate machine slug",
        ),
        (
            lambda document: document["machines"][1]["assets"][0].__setitem__(
                "slug", document["machines"][0]["assets"][0]["slug"]
            ),
            "duplicate asset slug",
        ),
        (
            lambda document: document["machines"][1]["assets"][0]["legacy"].__setitem__(
                "resource_id", document["machines"][0]["assets"][0]["legacy"]["resource_id"]
            ),
            "duplicate legacy ID",
        ),
    ],
)
def test_semantic_duplicates_are_rejected(tmp_path: Path, mutator, message: str) -> None:
    document = _load_document()
    mutator(document)
    path = _write_document(tmp_path, document)

    with pytest.raises(BootstrapAssetError, match=message):
        load_bootstrap_plan(path, Path("data/bootstrap/assets.schema.json"))


@pytest.mark.django_db
def test_import_command_default_dry_run_writes_zero_rows() -> None:
    output = StringIO()

    call_command("import_bootstrap_assets", input=str(BOOTSTRAP_INPUT), stdout=output)

    assert Asset.objects.count() == 0
    assert "mode=dry-run" in output.getvalue()
    assert "planned=47" in output.getvalue()
    assert "created=47" in output.getvalue()
    assert "excluded=1" in output.getvalue()


@pytest.mark.django_db
def test_import_apply_creates_exact_inventory_and_second_apply_is_idempotent() -> None:
    first_output = StringIO()
    call_command(
        "import_bootstrap_assets",
        input=str(BOOTSTRAP_INPUT),
        apply=True,
        stdout=first_output,
    )

    assert "mode=apply" in first_output.getvalue()
    assert "created=47" in first_output.getvalue()
    assert Asset.objects.count() == 47
    assert Asset.objects.filter(kind=Asset.KIND_MACHINE).count() == 17
    assert Asset.objects.filter(kind=Asset.KIND_GPU).count() == 30

    second_output = StringIO()
    call_command(
        "import_bootstrap_assets",
        input=str(BOOTSTRAP_INPUT),
        apply=True,
        stdout=second_output,
    )

    assert Asset.objects.count() == 47
    assert "created=0" in second_output.getvalue()
    assert "unchanged=47" in second_output.getvalue()


@pytest.mark.django_db
def test_import_preserves_explicit_neumann_mapping_without_inference() -> None:
    call_command("import_bootstrap_assets", input=str(BOOTSTRAP_INPUT), apply=True)

    asset = Asset.objects.get(legacy_source="smartscheduling", legacy_id="neumanngpu4")

    assert asset.slug == "neumann-gpu-0"
    assert asset.legacy_metadata["ordinal_hint_unverified"] == 0
    assert "Explicit legacy mapping" in asset.legacy_metadata["source_note"]


@pytest.mark.django_db
def test_import_excludes_chatgptpro_and_preserves_disabled_askljof() -> None:
    call_command("import_bootstrap_assets", input=str(BOOTSTRAP_INPUT), apply=True)

    assert not Asset.objects.filter(legacy_id="chatgptpro").exists()
    askljof = Asset.objects.get(slug="askljof-gpu")
    assert askljof.active is False
    assert askljof.reservable is False


@pytest.mark.django_db
def test_import_does_not_invent_private_or_verified_hardware_identity() -> None:
    call_command("import_bootstrap_assets", input=str(BOOTSTRAP_INPUT), apply=True)

    imported = Asset.objects.exclude(kind=Asset.KIND_MACHINE)
    assert all(asset.capabilities == {} for asset in imported)
    assert all(asset.physical_locator == "" for asset in imported)
    for asset in imported:
        serialized_metadata = str(asset.legacy_metadata).lower()
        assert "gpu_uuid" not in serialized_metadata
        assert "cuda" not in serialized_metadata
        assert "hostname" not in serialized_metadata


@pytest.mark.django_db
def test_import_conflict_fails_closed_and_leaves_database_unchanged() -> None:
    Asset.objects.create(slug="gpx1", name="Admin maintained", kind=Asset.KIND_MACHINE)

    with pytest.raises(CommandError, match="conflicts"):
        call_command("import_bootstrap_assets", input=str(BOOTSTRAP_INPUT), apply=True)

    assert Asset.objects.count() == 1
    assert Asset.objects.get(slug="gpx1").name == "Admin maintained"


def _load_document() -> dict[str, object]:
    with BOOTSTRAP_INPUT.open(encoding="utf-8") as file:
        document = yaml.safe_load(file)
    assert isinstance(document, dict)
    return document


def _write_document(tmp_path: Path, document: dict[str, object]) -> Path:
    path = tmp_path / "assets.yaml"
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    return path
