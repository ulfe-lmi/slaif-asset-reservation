from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from slaif_reservation.legacy_import.exceptions import LegacyImportError
from slaif_reservation.legacy_import.types import (
    NormalizedLegacyAppointment,
    NormalizedLegacyExport,
    NormalizedLegacyPerson,
    NormalizedLegacyResource,
)
from slaif_reservation.reservations.time_utils import LocalTimeError, interpret_local_wall_time

FORMAT_VERSION = "slaif-smartscheduling-synthetic-v1"
IMPORTABLE_STATUSES = frozenset({"confirmed", "completed"})
SKIPPED_STATUSES = frozenset({"cancelled", "no_show"})
UNSUPPORTED_STATUSES = frozenset({"waitlisted"})
KNOWN_STATUSES = IMPORTABLE_STATUSES | SKIPPED_STATUSES | UNSUPPORTED_STATUSES
SUPPORTED_EXTENSIONS = frozenset({".json", ".yaml", ".yml"})

TOP_LEVEL_KEYS = frozenset({"format", "source", "synthetic", "resources", "people", "appointments"})
RESOURCE_KEYS = frozenset({"legacy_id", "name", "slug"})
PERSON_KEYS = frozenset({"legacy_id", "display_name"})
APPOINTMENT_KEYS = frozenset(
    {
        "legacy_id",
        "resource_legacy_id",
        "requester_legacy_id",
        "start",
        "end",
        "start_fold",
        "end_fold",
        "status",
        "purpose",
        "created_at",
        "updated_at",
    }
)
PRIVATE_OR_UNSUPPORTED_KEYS = frozenset(
    {
        "phone",
        "phone_number",
        "email",
        "e_mail",
        "notes",
        "private_notes",
        "raw",
        "raw_row",
        "cookie",
        "cookies",
        "token",
        "tokens",
        "authorization",
        "authorization_header",
        "url",
        "screenshot",
        "trace",
        "browser_storage",
        "local_storage",
    }
)


URL_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:/+")


def _reject_url(value: str) -> None:
    lowered = value.strip().lower()
    if URL_SCHEME_RE.match(lowered):
        raise LegacyImportError("URL inputs are not accepted.")


def _load_document(path: Path) -> tuple[dict[str, Any], str]:
    _reject_url(str(path))
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise LegacyImportError("Unsupported export file extension.")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise LegacyImportError("Input export file cannot be read.") from exc
    try:
        if path.suffix.lower() == ".json":
            value = json.loads(raw.decode("utf-8"))
        else:
            value = yaml.safe_load(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise LegacyImportError("Input export file is not valid JSON/YAML.") from exc
    if not isinstance(value, dict):
        raise LegacyImportError("Synthetic export must be a JSON/YAML object.")
    return value, hashlib.sha256(raw).hexdigest()


def _unknown_keys(value: dict[str, Any], allowed: frozenset[str]) -> set[str]:
    keys = set(value)
    private = {key for key in keys if key.strip().lower() in PRIVATE_OR_UNSUPPORTED_KEYS}
    unknown = keys - allowed
    return private | unknown


def _required_string(value: dict[str, Any], key: str, *, max_length: int = 160) -> str:
    raw = value.get(key)
    if not isinstance(raw, str) or not raw.strip():
        raise LegacyImportError(f"{key} is required.")
    normalized = raw.strip()
    if len(normalized) > max_length:
        raise LegacyImportError(f"{key} is too long.")
    return normalized


def _optional_string(value: dict[str, Any], key: str, *, max_length: int = 1000) -> str:
    raw = value.get(key, "")
    if raw is None:
        return ""
    if not isinstance(raw, str):
        raise LegacyImportError(f"{key} must be a string.")
    normalized = raw.strip()
    if len(normalized) > max_length:
        raise LegacyImportError(f"{key} is too long.")
    return normalized


def _parse_fold(value: Any, *, key: str) -> int | None:
    if value is None:
        return None
    if value not in (0, 1):
        raise LegacyImportError(f"{key} must be 0 or 1 when supplied.")
    return int(value)


def _parse_local_instant(value: Any, *, timezone_name: str, fold: int | None, key: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise LegacyImportError(f"{key} is required.")
    try:
        local_time = datetime.fromisoformat(value.strip())
    except ValueError as exc:
        raise LegacyImportError(f"{key} must be an ISO local datetime.") from exc
    if local_time.tzinfo is not None:
        raise LegacyImportError(f"{key} must be a local wall time without an offset.")
    try:
        return interpret_local_wall_time(local_time, timezone_name=timezone_name, fold=fold).instant
    except LocalTimeError as exc:
        raise LegacyImportError(f"{key} is not a valid local time: {exc}") from exc


def _parse_optional_aware(value: Any, *, key: str) -> datetime | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise LegacyImportError(f"{key} must be an aware ISO datetime.")
    raw = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise LegacyImportError(f"{key} must be an aware ISO datetime.") from exc
    if parsed.tzinfo is None:
        raise LegacyImportError(f"{key} must be timezone-aware.")
    return parsed.astimezone(UTC)


def _ensure_unique(values: list[str], *, label: str) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    if duplicates:
        raise LegacyImportError(f"Duplicate {label}: {', '.join(sorted(duplicates))}.")


def parse_synthetic_export(
    path: Path, *, source_name: str, timezone_name: str
) -> NormalizedLegacyExport:
    document, checksum = _load_document(path)
    unknown_top = _unknown_keys(document, TOP_LEVEL_KEYS)
    if unknown_top:
        raise LegacyImportError(
            f"Unsupported top-level field(s): {', '.join(sorted(unknown_top))}."
        )
    if document.get("format") != FORMAT_VERSION:
        raise LegacyImportError("Unsupported synthetic export format.")
    source = _required_string(document, "source", max_length=80)
    if source != source_name:
        raise LegacyImportError("Input source does not match --source.")
    if document.get("synthetic") is not True:
        raise LegacyImportError("Only synthetic fixture exports are accepted in this slice.")

    resources_raw = document.get("resources")
    people_raw = document.get("people")
    appointments_raw = document.get("appointments")
    if (
        not isinstance(resources_raw, list)
        or not isinstance(people_raw, list)
        or not isinstance(appointments_raw, list)
    ):
        raise LegacyImportError("resources, people, and appointments must be lists.")

    resources: list[NormalizedLegacyResource] = []
    for raw in resources_raw:
        if not isinstance(raw, dict):
            raise LegacyImportError("Each resource must be an object.")
        unknown = _unknown_keys(raw, RESOURCE_KEYS)
        if unknown:
            raise LegacyImportError(f"Unsupported resource field(s): {', '.join(sorted(unknown))}.")
        resources.append(
            NormalizedLegacyResource(
                legacy_source=source,
                legacy_id=_required_string(raw, "legacy_id"),
                name=_required_string(raw, "name", max_length=180),
                slug=_optional_string(raw, "slug", max_length=120) or None,
            )
        )
    _ensure_unique([resource.legacy_id for resource in resources], label="resource legacy ID")

    people: list[NormalizedLegacyPerson] = []
    for raw in people_raw:
        if not isinstance(raw, dict):
            raise LegacyImportError("Each person must be an object.")
        unknown = _unknown_keys(raw, PERSON_KEYS)
        if unknown:
            raise LegacyImportError(f"Unsupported person field(s): {', '.join(sorted(unknown))}.")
        people.append(
            NormalizedLegacyPerson(
                legacy_source=source,
                legacy_id=_required_string(raw, "legacy_id"),
                display_name=_required_string(raw, "display_name", max_length=180),
            )
        )
    _ensure_unique([person.legacy_id for person in people], label="person legacy ID")

    appointments: list[NormalizedLegacyAppointment] = []
    for raw in appointments_raw:
        if not isinstance(raw, dict):
            raise LegacyImportError("Each appointment must be an object.")
        unknown = _unknown_keys(raw, APPOINTMENT_KEYS)
        if unknown:
            raise LegacyImportError(
                f"Unsupported appointment field(s): {', '.join(sorted(unknown))}."
            )
        legacy_id = _required_string(raw, "legacy_id")
        status = _required_string(raw, "status", max_length=40)
        if status not in KNOWN_STATUSES:
            raise LegacyImportError(f"Unknown legacy status for appointment {legacy_id}.")
        start_at = _parse_local_instant(
            raw.get("start"),
            timezone_name=timezone_name,
            fold=_parse_fold(raw.get("start_fold"), key="start_fold"),
            key="start",
        )
        end_at = _parse_local_instant(
            raw.get("end"),
            timezone_name=timezone_name,
            fold=_parse_fold(raw.get("end_fold"), key="end_fold"),
            key="end",
        )
        if end_at <= start_at:
            raise LegacyImportError(f"Appointment {legacy_id} end must be after start.")
        appointments.append(
            NormalizedLegacyAppointment(
                legacy_source=source,
                legacy_id=legacy_id,
                resource_legacy_id=_required_string(raw, "resource_legacy_id"),
                requester_legacy_id=_required_string(raw, "requester_legacy_id"),
                start_at=start_at,
                end_at=end_at,
                status=status,
                purpose=_optional_string(raw, "purpose", max_length=1000),
                created_at=_parse_optional_aware(raw.get("created_at"), key="created_at"),
                updated_at=_parse_optional_aware(raw.get("updated_at"), key="updated_at"),
            )
        )
    _ensure_unique(
        [appointment.legacy_id for appointment in appointments],
        label="appointment legacy ID",
    )

    return NormalizedLegacyExport(
        legacy_source=source,
        source_checksum=checksum,
        synthetic=True,
        resources=tuple(resources),
        people=tuple(people),
        appointments=tuple(appointments),
    )
