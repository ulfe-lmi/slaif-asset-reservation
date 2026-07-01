from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

ImportClassification = Literal[
    "would_create",
    "imported",
    "already_imported",
    "legacy_changed",
    "unmapped_asset",
    "unmapped_user",
    "invalid_time",
    "asset_not_reservable",
    "policy_not_configured",
    "blackout_conflict",
    "reservation_conflict",
    "unsupported_status",
    "skipped_status",
    "error",
]


@dataclass(frozen=True)
class NormalizedLegacyResource:
    legacy_source: str
    legacy_id: str
    name: str
    slug: str | None = None


@dataclass(frozen=True)
class NormalizedLegacyPerson:
    legacy_source: str
    legacy_id: str
    display_name: str


@dataclass(frozen=True)
class NormalizedLegacyAppointment:
    legacy_source: str
    legacy_id: str
    resource_legacy_id: str
    requester_legacy_id: str
    start_at: datetime
    end_at: datetime
    status: str
    purpose: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class NormalizedLegacyExport:
    legacy_source: str
    source_checksum: str
    synthetic: bool
    resources: tuple[NormalizedLegacyResource, ...]
    people: tuple[NormalizedLegacyPerson, ...]
    appointments: tuple[NormalizedLegacyAppointment, ...]


@dataclass(frozen=True)
class ImportMessage:
    level: Literal["warning", "error"]
    code: str
    legacy_id: str
    message: str


@dataclass(frozen=True)
class PlannedAppointment:
    appointment: NormalizedLegacyAppointment
    classification: ImportClassification
    asset_id: str | None = None
    user_id: str | None = None
    reservation_id: str | None = None
    messages: tuple[ImportMessage, ...] = ()


@dataclass(frozen=True)
class ImportPlan:
    export: NormalizedLegacyExport
    records: tuple[PlannedAppointment, ...]
    counts: dict[str, int] = field(default_factory=dict)
    messages: tuple[ImportMessage, ...] = ()
