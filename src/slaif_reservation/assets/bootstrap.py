from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from django.core.exceptions import ValidationError
from django.db import transaction
from jsonschema import Draft202012Validator, FormatChecker
from yaml import YAMLError

from slaif_reservation.assets.models import Asset


class BootstrapAssetError(ValueError):
    """Raised when bootstrap inventory cannot be safely imported."""


@dataclass(frozen=True)
class AssetImportRecord:
    slug: str
    name: str
    kind: str
    parent_slug: str | None
    active: bool
    reservable: bool
    description: str
    timezone: str
    legacy_source: str | None
    legacy_id: str | None
    legacy_metadata: dict[str, Any]
    verification_required: bool = True
    booking_mode: str = Asset.BOOKING_EXCLUSIVE
    capabilities: dict[str, Any] = field(default_factory=dict)
    location: str = ""
    physical_locator: str = ""

    @property
    def legacy_pair(self) -> tuple[str, str] | None:
        if self.legacy_source and self.legacy_id:
            return (self.legacy_source, self.legacy_id)
        return None


@dataclass(frozen=True)
class ExcludedLegacyRecord:
    legacy_id: str
    display_name: str
    reason: str


@dataclass(frozen=True)
class BootstrapPlan:
    records: tuple[AssetImportRecord, ...]
    excluded: tuple[ExcludedLegacyRecord, ...]

    @property
    def planned_count(self) -> int:
        return len(self.records)


@dataclass(frozen=True)
class ImportCounts:
    planned: int
    created: int
    unchanged: int
    excluded: int
    conflicted: int

    def as_dict(self) -> dict[str, int]:
        return {
            "planned": self.planned,
            "created": self.created,
            "unchanged": self.unchanged,
            "excluded": self.excluded,
            "conflicted": self.conflicted,
        }


def load_bootstrap_document(input_path: Path, schema_path: Path | None = None) -> dict[str, Any]:
    try:
        raw_document = yaml.safe_load(input_path.read_text(encoding="utf-8"))
    except YAMLError as exc:
        raise BootstrapAssetError(f"Invalid YAML: {exc}") from exc

    if not isinstance(raw_document, dict):
        raise BootstrapAssetError("Bootstrap inventory must be a YAML mapping.")

    schema = _load_schema(schema_path or input_path.with_name("assets.schema.json"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(raw_document), key=lambda error: list(error.path))
    if errors:
        first_error = errors[0]
        location = ".".join(str(item) for item in first_error.path) or "<root>"
        raise BootstrapAssetError(f"Bootstrap inventory schema validation failed at {location}.")

    return raw_document


def build_bootstrap_plan(document: dict[str, Any]) -> BootstrapPlan:
    semantic_errors = _semantic_errors(document)
    if semantic_errors:
        raise BootstrapAssetError("; ".join(semantic_errors))

    defaults = document["defaults"]
    source = document["source"]
    records: list[AssetImportRecord] = []

    for machine in document["machines"]:
        machine_slug = machine["slug"]
        machine_active = bool(machine["active"])
        records.append(
            AssetImportRecord(
                slug=machine_slug,
                name=machine["name"],
                kind=Asset.KIND_MACHINE,
                parent_slug=None,
                active=machine_active,
                reservable=False,
                description=(
                    "Imported machine parent from sanitized bootstrap inventory. "
                    "Hardware identity is unverified."
                ),
                timezone=defaults["timezone"],
                legacy_source=None,
                legacy_id=None,
                legacy_metadata={
                    "source_system": source["system"],
                    "source_account": source["account"],
                    "source_observed_at": source["observed_at"],
                    "source_classification": source["classification"],
                    "source_machine_slug": machine_slug,
                    "source_machine_name": machine["name"],
                    "verification_required": True,
                    "availability_note": defaults["availability"],
                },
            )
        )

        for child in machine["assets"]:
            legacy = child["legacy"]
            records.append(
                AssetImportRecord(
                    slug=child["slug"],
                    name=child["name"],
                    kind=child["kind"],
                    parent_slug=machine_slug,
                    active=bool(child["active"]),
                    reservable=bool(child["reservable"]),
                    description=(
                        "Unverified legacy hardware display: "
                        f"{child['hardware_display_unverified']}"
                    ),
                    timezone=defaults["timezone"],
                    legacy_source=legacy["system"],
                    legacy_id=legacy["resource_id"],
                    legacy_metadata={
                        "source_system": source["system"],
                        "source_account": source["account"],
                        "source_observed_at": source["observed_at"],
                        "source_classification": source["classification"],
                        "source_machine_slug": machine_slug,
                        "public_display_order": legacy["public_display_order"],
                        "ordinal_hint_unverified": child["ordinal_hint_unverified"],
                        "original_public_hardware_display": child["hardware_display_unverified"],
                        "source_note": child.get("note", ""),
                        "verification_required": True,
                    },
                )
            )

    excluded = tuple(
        ExcludedLegacyRecord(
            legacy_id=record["legacy_resource_id"],
            display_name=record["display_name"],
            reason=record["reason"],
        )
        for record in document["excluded_legacy_records"]
    )
    plan = BootstrapPlan(records=tuple(records), excluded=excluded)
    validate_bootstrap_plan(plan)
    return plan


def load_bootstrap_plan(input_path: Path, schema_path: Path | None = None) -> BootstrapPlan:
    return build_bootstrap_plan(load_bootstrap_document(input_path, schema_path))


def validate_bootstrap_plan(plan: BootstrapPlan) -> None:
    planned_assets: dict[str, Asset] = {}
    for record in plan.records:
        parent = planned_assets.get(record.parent_slug) if record.parent_slug else None
        asset = _asset_from_record(record, parent)
        try:
            asset.full_clean(
                exclude={"parent"},
                validate_unique=False,
                validate_constraints=False,
            )
        except ValidationError as exc:
            raise BootstrapAssetError(
                f"Planned asset {record.slug} failed validation: {_format_validation_error(exc)}"
            ) from exc
        planned_assets[record.slug] = asset


def preview_bootstrap_import(plan: BootstrapPlan) -> ImportCounts:
    validate_bootstrap_plan(plan)
    created, unchanged, conflicted = _classify_existing_records(plan)
    return ImportCounts(
        planned=plan.planned_count,
        created=created,
        unchanged=unchanged,
        excluded=len(plan.excluded),
        conflicted=conflicted,
    )


def apply_bootstrap_import(plan: BootstrapPlan) -> ImportCounts:
    validate_bootstrap_plan(plan)
    counts = preview_bootstrap_import(plan)
    if counts.conflicted:
        return counts

    with transaction.atomic():
        counts = preview_bootstrap_import(plan)
        if counts.conflicted:
            transaction.set_rollback(True)
            return counts

        created = 0
        created_by_slug: dict[str, Asset] = {}
        for record in plan.records:
            existing = Asset.objects.filter(slug=record.slug).first()
            if existing is not None:
                created_by_slug[record.slug] = existing
                continue

            parent = created_by_slug.get(record.parent_slug) if record.parent_slug else None
            asset = _asset_from_record(record, parent)
            asset.full_clean()
            asset.save()
            created_by_slug[record.slug] = asset
            created += 1

    return ImportCounts(
        planned=plan.planned_count,
        created=created,
        unchanged=counts.unchanged,
        excluded=len(plan.excluded),
        conflicted=0,
    )


def _load_schema(path: Path) -> dict[str, Any]:
    try:
        schema = yaml.safe_load(path.read_text(encoding="utf-8"))
    except YAMLError as exc:
        raise BootstrapAssetError(f"Invalid bootstrap schema file: {exc}") from exc
    if not isinstance(schema, dict):
        raise BootstrapAssetError("Bootstrap schema must be a mapping.")
    return schema


def _semantic_errors(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    machines = document["machines"]
    machine_slugs = [machine["slug"] for machine in machines]
    asset_slugs = [asset["slug"] for machine in machines for asset in machine["assets"]]
    all_slugs = machine_slugs + asset_slugs
    legacy_ids = [
        asset["legacy"]["resource_id"] for machine in machines for asset in machine["assets"]
    ]
    source_system = document["source"]["system"]

    errors.extend(_duplicates("duplicate machine slug", machine_slugs))
    errors.extend(_duplicates("duplicate asset slug", all_slugs))
    errors.extend(_duplicates("duplicate legacy ID", legacy_ids))

    for machine in machines:
        for asset in machine["assets"]:
            legacy_system = asset["legacy"]["system"]
            if legacy_system != source_system:
                errors.append(
                    f"inconsistent source mapping for {asset['slug']}: "
                    f"{legacy_system} != {source_system}"
                )

    excluded_ids = [record["legacy_resource_id"] for record in document["excluded_legacy_records"]]
    errors.extend(_duplicates("duplicate excluded legacy ID", excluded_ids))
    for duplicate in sorted(set(legacy_ids) & set(excluded_ids)):
        errors.append(f"duplicate legacy ID also excluded: {duplicate}")

    return errors


def _duplicates(label: str, values: list[str]) -> list[str]:
    counts = Counter(values)
    return [f"{label}: {value}" for value, count in sorted(counts.items()) if count > 1]


def _asset_from_record(record: AssetImportRecord, parent: Asset | None) -> Asset:
    return Asset(
        parent=parent,
        slug=record.slug,
        name=record.name,
        kind=record.kind,
        booking_mode=record.booking_mode,
        description=record.description,
        location=record.location,
        timezone=record.timezone,
        active=record.active,
        reservable=record.reservable,
        capabilities=record.capabilities,
        verification_required=record.verification_required,
        physical_locator=record.physical_locator,
        legacy_source=record.legacy_source,
        legacy_id=record.legacy_id,
        legacy_metadata=record.legacy_metadata,
    )


def _format_validation_error(exc: ValidationError) -> str:
    if hasattr(exc, "message_dict"):
        parts = []
        for field_name, messages in exc.message_dict.items():
            parts.append(f"{field_name}: {', '.join(str(message) for message in messages)}")
        return "; ".join(parts)
    return ", ".join(str(message) for message in exc.messages)


def _classify_existing_records(plan: BootstrapPlan) -> tuple[int, int, int]:
    created = 0
    unchanged = 0
    conflicted = 0
    plan_by_slug = {record.slug: record for record in plan.records}
    plan_by_legacy = {record.legacy_pair: record for record in plan.records if record.legacy_pair}

    existing_by_slug = Asset.objects.filter(slug__in=plan_by_slug).select_related("parent")
    for asset in existing_by_slug:
        record = plan_by_slug[asset.slug]
        if _asset_matches_record(asset, record):
            unchanged += 1
        else:
            conflicted += 1

    existing_slugs = {asset.slug for asset in existing_by_slug}

    legacy_conditions = list(plan_by_legacy)
    for legacy_source, legacy_id in legacy_conditions:
        existing = Asset.objects.filter(legacy_source=legacy_source, legacy_id=legacy_id).first()
        if (
            existing is not None
            and existing.slug != plan_by_legacy[(legacy_source, legacy_id)].slug
        ):
            conflicted += 1

    created = len(plan.records) - len(existing_slugs)
    return created, unchanged, conflicted


def _asset_matches_record(asset: Asset, record: AssetImportRecord) -> bool:
    parent_slug = asset.parent.slug if asset.parent else None
    if parent_slug != record.parent_slug:
        return False

    expected = {
        "name": record.name,
        "kind": record.kind,
        "booking_mode": record.booking_mode,
        "description": record.description,
        "location": record.location,
        "timezone": record.timezone,
        "active": record.active,
        "reservable": record.reservable,
        "capabilities": record.capabilities,
        "verification_required": record.verification_required,
        "physical_locator": record.physical_locator,
        "legacy_source": record.legacy_source,
        "legacy_id": record.legacy_id,
        "legacy_metadata": record.legacy_metadata,
    }
    for field_name, expected_value in expected.items():
        if getattr(asset, field_name) != expected_value:
            return False

    try:
        asset.full_clean()
    except ValidationError:
        return False
    return True
