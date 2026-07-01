from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.management.base import CommandError, CommandParser
from django.db import DatabaseError

from slaif_reservation.legacy_import.exceptions import LegacyImportError
from slaif_reservation.legacy_import.importer import build_plan
from slaif_reservation.legacy_import.mapping import load_mapping
from slaif_reservation.legacy_import.parser import parse_synthetic_export


def add_common_import_arguments(parser: CommandParser, *, include_mapping: bool = True) -> None:
    parser.add_argument("--input", required=True, help="Path to a synthetic export JSON/YAML file.")
    parser.add_argument("--source", required=True, help="Expected legacy source name.")
    parser.add_argument(
        "--timezone", required=True, help="IANA timezone for legacy local wall times."
    )
    if include_mapping:
        parser.add_argument("--mapping", help="Optional validated legacy mapping JSON/YAML path.")
    parser.add_argument("--report-json", help="Optional explicit path for a redacted JSON report.")


def load_plan(options: dict[str, Any]) -> Any:
    try:
        export = load_export(options)
        mapping = load_mapping(Path(str(options["mapping"])) if options.get("mapping") else None)
        return build_plan(export, mapping)
    except LegacyImportError as exc:
        raise CommandError(str(exc)) from exc
    except DatabaseError as exc:
        raise CommandError(
            "Migration planning database tables are unavailable; run migrations."
        ) from exc


def load_export(options: dict[str, Any]) -> Any:
    try:
        return parse_synthetic_export(
            Path(str(options["input"])),
            source_name=str(options["source"]),
            timezone_name=str(options["timezone"]),
        )
    except LegacyImportError as exc:
        raise CommandError(str(exc)) from exc


def write_report(path_value: str | None, payload: dict[str, Any]) -> None:
    if not path_value:
        return
    path = Path(path_value)
    raw = str(path)
    if raw.startswith(("http://", "https://")):
        raise CommandError("Report path must be a local filesystem path.")
    if not path.parent.exists():
        raise CommandError("Report parent directory does not exist.")
    try:
        path.write_text(
            json.dumps(payload, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise CommandError("Report file could not be written.") from exc


def print_counts(command: Any, counts: dict[str, int]) -> None:
    for key in sorted(counts):
        command.stdout.write(f"{key}={counts[key]}")
