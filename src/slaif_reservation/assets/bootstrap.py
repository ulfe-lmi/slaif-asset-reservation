from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
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
    location: str
    timezone: str
    verification_required: bool = True


@dataclass(frozen=True)
class BootstrapPlan:
    records: tuple[AssetImportRecord, ...]

    @property
    def planned_count(self) -> int:
        return len(self.records)


@dataclass(frozen=True)
class ImportCounts:
    planned: int
    created: int
    unchanged: int
    conflicted: int

    def as_dict(self) -> dict[str, int]:
        return {
            "planned": self.planned,
            "created": self.created,
            "unchanged": self.unchanged,
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
    records = tuple(
        AssetImportRecord(
            slug=asset["slug"],
            name=asset["name"],
            kind=asset["kind"],
            parent_slug=asset.get("parent"),
            active=asset["active"],
            reservable=asset["reservable"],
            description=asset.get("description", ""),
            location=asset.get("location", ""),
            timezone=asset.get("timezone", document["defaults"]["timezone"]),
            verification_required=asset.get("verification_required", True),
        )
        for asset in _ordered_assets(document["assets"])
    )
    plan = BootstrapPlan(records=records)
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


def _ordered_assets(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(asset["slug"] for asset in assets)
    duplicates = sorted(slug for slug, count in counts.items() if count > 1)
    if duplicates:
        raise BootstrapAssetError(f"duplicate asset slug: {', '.join(duplicates)}")

    by_slug = {asset["slug"]: asset for asset in assets}
    children: dict[str, list[str]] = {slug: [] for slug in by_slug}
    ready = deque[str]()
    for asset in assets:
        slug = asset["slug"]
        parent = asset.get("parent")
        if parent is None:
            ready.append(slug)
        elif parent == slug:
            raise BootstrapAssetError(f"Asset {slug} cannot parent itself.")
        elif parent not in by_slug:
            raise BootstrapAssetError(f"Unknown parent for asset {slug}.")
        else:
            children[parent].append(slug)

    ordered = []
    while ready:
        slug = ready.popleft()
        ordered.append(by_slug[slug])
        ready.extend(children[slug])
    if len(ordered) != len(assets):
        raise BootstrapAssetError("Asset parent references contain a cycle.")

    for asset in ordered:
        parent = asset.get("parent")
        if parent is not None:
            if asset["kind"] == Asset.KIND_MACHINE:
                raise BootstrapAssetError("Machine assets cannot have a parent.")
            if by_slug[parent]["kind"] != Asset.KIND_MACHINE:
                raise BootstrapAssetError("A child asset parent must be a machine.")
    return ordered


def _asset_from_record(record: AssetImportRecord, parent: Asset | None) -> Asset:
    return Asset(
        parent=parent,
        slug=record.slug,
        name=record.name,
        kind=record.kind,
        description=record.description,
        location=record.location,
        timezone=record.timezone,
        active=record.active,
        reservable=record.reservable,
        verification_required=record.verification_required,
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

    existing_by_slug = Asset.objects.filter(slug__in=plan_by_slug).select_related("parent")
    for asset in existing_by_slug:
        record = plan_by_slug[asset.slug]
        if _asset_matches_record(asset, record):
            unchanged += 1
        else:
            conflicted += 1

    existing_slugs = {asset.slug for asset in existing_by_slug}

    created = len(plan.records) - len(existing_slugs)
    return created, unchanged, conflicted


def _asset_matches_record(asset: Asset, record: AssetImportRecord) -> bool:
    parent_slug = asset.parent.slug if asset.parent else None
    if parent_slug != record.parent_slug:
        return False

    expected = {
        "name": record.name,
        "kind": record.kind,
        "booking_mode": Asset.BOOKING_EXCLUSIVE,
        "description": record.description,
        "location": record.location,
        "timezone": record.timezone,
        "active": record.active,
        "reservable": record.reservable,
        "capabilities": {},
        "verification_required": record.verification_required,
        "physical_locator": "",
        "legacy_source": None,
        "legacy_id": None,
        "legacy_metadata": {},
    }
    for field_name, expected_value in expected.items():
        if getattr(asset, field_name) != expected_value:
            return False

    try:
        asset.full_clean()
    except ValidationError:
        return False
    return True
