from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import yaml

from slaif_reservation.assets.models import Asset
from slaif_reservation.legacy_import.exceptions import LegacyImportError
from slaif_reservation.legacy_import.parser import _reject_url
from slaif_reservation.legacy_import.types import NormalizedLegacyExport, NormalizedLegacyResource

MAPPING_FORMAT = "slaif-smartscheduling-mapping-v1"
MAPPING_EXTENSIONS = frozenset({".json", ".yaml", ".yml"})
MAPPING_TOP_KEYS = frozenset({"format", "users", "assets", "asset_slugs"})


class LegacyMapping:
    def __init__(
        self,
        *,
        users: dict[str, uuid.UUID] | None = None,
        assets: dict[str, uuid.UUID] | None = None,
        asset_slugs: dict[str, str] | None = None,
    ) -> None:
        self.users = users or {}
        self.assets = assets or {}
        self.asset_slugs = asset_slugs or {}


def _load_mapping(path: Path) -> dict[str, Any]:
    _reject_url(str(path))
    if path.suffix.lower() not in MAPPING_EXTENSIONS:
        raise LegacyImportError("Unsupported mapping file extension.")
    try:
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw) if path.suffix.lower() == ".json" else yaml.safe_load(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise LegacyImportError("Mapping file is not valid JSON/YAML.") from exc
    if not isinstance(value, dict):
        raise LegacyImportError("Mapping file must be an object.")
    unknown = set(value) - MAPPING_TOP_KEYS
    if unknown:
        raise LegacyImportError(f"Unsupported mapping field(s): {', '.join(sorted(unknown))}.")
    if value.get("format") != MAPPING_FORMAT:
        raise LegacyImportError("Unsupported mapping file format.")
    return value


def _parse_uuid_map(value: Any, *, label: str) -> dict[str, uuid.UUID]:
    if value in (None, {}):
        return {}
    if not isinstance(value, dict):
        raise LegacyImportError(f"{label} mapping must be an object.")
    parsed: dict[str, uuid.UUID] = {}
    for legacy_id, target in value.items():
        if not isinstance(legacy_id, str) or not legacy_id.strip():
            raise LegacyImportError(f"{label} mapping contains an invalid legacy ID.")
        if not isinstance(target, str):
            raise LegacyImportError(f"{label} mapping target must be a UUID string.")
        try:
            parsed[legacy_id.strip()] = uuid.UUID(target.strip())
        except ValueError as exc:
            raise LegacyImportError(f"{label} mapping target must be a UUID string.") from exc
    return parsed


def _parse_slug_map(value: Any) -> dict[str, str]:
    if value in (None, {}):
        return {}
    if not isinstance(value, dict):
        raise LegacyImportError("asset_slugs mapping must be an object.")
    parsed: dict[str, str] = {}
    for legacy_id, slug in value.items():
        if not isinstance(legacy_id, str) or not legacy_id.strip():
            raise LegacyImportError("asset_slugs mapping contains an invalid legacy ID.")
        if not isinstance(slug, str) or not slug.strip():
            raise LegacyImportError("asset_slugs mapping target must be a non-empty slug.")
        parsed[legacy_id.strip()] = slug.strip()
    return parsed


def load_mapping(path: Path | None) -> LegacyMapping:
    if path is None:
        return LegacyMapping()
    value = _load_mapping(path)
    users = _parse_uuid_map(value.get("users"), label="users")
    assets = _parse_uuid_map(value.get("assets"), label="assets")
    asset_slugs = _parse_slug_map(value.get("asset_slugs"))
    duplicate_values = sorted(set(assets) & set(asset_slugs))
    if duplicate_values:
        raise LegacyImportError(
            f"Asset mapping contains duplicate legacy ID(s): {', '.join(duplicate_values)}."
        )
    return LegacyMapping(users=users, assets=assets, asset_slugs=asset_slugs)


def map_user_id(mapping: LegacyMapping, legacy_id: str) -> uuid.UUID | None:
    return mapping.users.get(legacy_id)


def map_asset(
    mapping: LegacyMapping, export: NormalizedLegacyExport, resource: NormalizedLegacyResource
) -> Asset | None:
    by_legacy = Asset.objects.filter(
        legacy_source=export.legacy_source,
        legacy_id=resource.legacy_id,
    ).order_by("id")
    if by_legacy.count() == 1:
        return by_legacy.first()
    if resource.legacy_id in mapping.assets:
        return Asset.objects.filter(pk=mapping.assets[resource.legacy_id]).first()
    if resource.legacy_id in mapping.asset_slugs:
        return Asset.objects.filter(slug=mapping.asset_slugs[resource.legacy_id]).first()
    if resource.slug:
        matches = Asset.objects.filter(slug=resource.slug).order_by("id")
        if matches.count() == 1:
            return matches.first()
    return None
