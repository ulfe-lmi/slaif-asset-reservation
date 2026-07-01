from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from django.contrib.auth import get_user_model
from django.utils import timezone

from slaif_reservation.assets.models import Asset
from slaif_reservation.legacy_import.mapping import LegacyMapping, map_asset, map_user_id
from slaif_reservation.legacy_import.models import LegacyImportRecord
from slaif_reservation.legacy_import.parser import (
    IMPORTABLE_STATUSES,
    SKIPPED_STATUSES,
    UNSUPPORTED_STATUSES,
)
from slaif_reservation.legacy_import.types import (
    ImportMessage,
    ImportPlan,
    NormalizedLegacyAppointment,
    NormalizedLegacyExport,
    PlannedAppointment,
)
from slaif_reservation.reservations.exceptions import (
    POLICY_AMBIGUOUS,
    POLICY_NOT_CONFIGURED,
    ReservationDomainError,
)
from slaif_reservation.reservations.models import MaintenanceBlackout, Reservation
from slaif_reservation.reservations.services import _enforce_policy, resolve_effective_policy

UserModel = get_user_model()

PLAN_CLASSIFICATIONS = (
    "would_create",
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
)


def normalized_appointment_hash(appointment: NormalizedLegacyAppointment) -> str:
    payload = {
        "legacy_source": appointment.legacy_source,
        "legacy_id": appointment.legacy_id,
        "resource_legacy_id": appointment.resource_legacy_id,
        "requester_legacy_id": appointment.requester_legacy_id,
        "start_at": appointment.start_at.isoformat(),
        "end_at": appointment.end_at.isoformat(),
        "status": appointment.status,
        "purpose": appointment.purpose,
        "created_at": appointment.created_at.isoformat() if appointment.created_at else None,
        "updated_at": appointment.updated_at.isoformat() if appointment.updated_at else None,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _message(code: str, legacy_id: str, message: str, *, level: str = "warning") -> ImportMessage:
    assert level in {"warning", "error"}
    typed_level: Literal["warning", "error"] = "error" if level == "error" else "warning"
    return ImportMessage(level=typed_level, code=code, legacy_id=legacy_id, message=message)


def _asset_allowed(asset: Asset) -> bool:
    return bool(asset.active and asset.reservable and asset.booking_mode == Asset.BOOKING_EXCLUSIVE)


def _blocking_reservation_exists(asset: Asset, appointment: NormalizedLegacyAppointment) -> bool:
    return Reservation.objects.filter(
        asset=asset,
        status__in=[Reservation.STATUS_CONFIRMED, Reservation.STATUS_RELEASED],
        start_at__lt=appointment.end_at,
        effective_end_at__gt=appointment.start_at,
    ).exists()


def _blackout_exists(asset: Asset, appointment: NormalizedLegacyAppointment) -> bool:
    return MaintenanceBlackout.objects.filter(
        asset=asset,
        active=True,
        start_at__lt=appointment.end_at,
        end_at__gt=appointment.start_at,
    ).exists()


def plan_import(export: NormalizedLegacyExport, mapping: LegacyMapping) -> ImportPlan:
    resources = {resource.legacy_id: resource for resource in export.resources}
    planned: list[PlannedAppointment] = []
    messages: list[ImportMessage] = []

    for appointment in export.appointments:
        existing = LegacyImportRecord.objects.filter(
            legacy_source=appointment.legacy_source,
            legacy_id=appointment.legacy_id,
        ).first()
        normalized_hash = normalized_appointment_hash(appointment)
        if existing is not None:
            existing_classification: Literal["already_imported", "legacy_changed"] = (
                "already_imported"
                if existing.normalized_hash == normalized_hash
                else "legacy_changed"
            )
            planned.append(
                PlannedAppointment(
                    appointment=appointment,
                    classification=existing_classification,
                    reservation_id=str(existing.reservation_id)
                    if existing.reservation_id
                    else None,
                    messages=(
                        _message(
                            existing_classification,
                            appointment.legacy_id,
                            "Legacy appointment was already imported."
                            if existing_classification == "already_imported"
                            else "Legacy appointment changed after import; not overwritten.",
                        ),
                    ),
                )
            )
            continue

        if appointment.status in SKIPPED_STATUSES:
            planned.append(
                PlannedAppointment(
                    appointment=appointment,
                    classification="skipped_status",
                    messages=(
                        _message(
                            "skipped_status",
                            appointment.legacy_id,
                            "Legacy status is intentionally skipped.",
                        ),
                    ),
                )
            )
            continue
        if (
            appointment.status in UNSUPPORTED_STATUSES
            or appointment.status not in IMPORTABLE_STATUSES
        ):
            planned.append(
                PlannedAppointment(
                    appointment=appointment,
                    classification="unsupported_status",
                    messages=(
                        _message(
                            "unsupported_status",
                            appointment.legacy_id,
                            "Legacy status is not imported in this slice.",
                            level="error",
                        ),
                    ),
                )
            )
            continue

        resource = resources.get(appointment.resource_legacy_id)
        asset = map_asset(mapping, export, resource) if resource else None
        if asset is None:
            planned.append(
                PlannedAppointment(
                    appointment=appointment,
                    classification="unmapped_asset",
                    messages=(
                        _message(
                            "unmapped_asset",
                            appointment.legacy_id,
                            "Legacy resource could not be mapped to an asset.",
                        ),
                    ),
                )
            )
            continue

        user_id = map_user_id(mapping, appointment.requester_legacy_id)
        user = UserModel.objects.filter(pk=user_id).first() if user_id else None
        if user is None:
            planned.append(
                PlannedAppointment(
                    appointment=appointment,
                    classification="unmapped_user",
                    asset_id=str(asset.id),
                    messages=(
                        _message(
                            "unmapped_user",
                            appointment.legacy_id,
                            "Legacy requester could not be mapped to an existing user.",
                        ),
                    ),
                )
            )
            continue

        if not _asset_allowed(asset):
            planned.append(
                PlannedAppointment(
                    appointment=appointment,
                    classification="asset_not_reservable",
                    asset_id=str(asset.id),
                    user_id=str(user.id),
                    messages=(
                        _message(
                            "asset_not_reservable",
                            appointment.legacy_id,
                            "Mapped asset is inactive, non-reservable, or unsupported.",
                        ),
                    ),
                )
            )
            continue

        try:
            policy = resolve_effective_policy(asset)
            if appointment.start_at >= timezone.now():
                _enforce_policy(
                    policy=policy,
                    principal=user,
                    start_at=appointment.start_at,
                    end_at=appointment.end_at,
                    purpose=appointment.purpose,
                    now=timezone.now(),
                )
        except ReservationDomainError as exc:
            policy_classification: Literal["policy_not_configured", "error"] = (
                "policy_not_configured"
            )
            if exc.code == POLICY_AMBIGUOUS:
                policy_classification = "error"
            elif exc.code != POLICY_NOT_CONFIGURED:
                policy_classification = "error"
            planned.append(
                PlannedAppointment(
                    appointment=appointment,
                    classification=policy_classification,
                    asset_id=str(asset.id),
                    user_id=str(user.id),
                    messages=(
                        _message(
                            policy_classification,
                            appointment.legacy_id,
                            "No unambiguous effective reservation policy applies.",
                            level="error",
                        ),
                    ),
                )
            )
            continue

        if _blackout_exists(asset, appointment):
            planned.append(
                PlannedAppointment(
                    appointment=appointment,
                    classification="blackout_conflict",
                    asset_id=str(asset.id),
                    user_id=str(user.id),
                    messages=(
                        _message(
                            "blackout_conflict",
                            appointment.legacy_id,
                            "Appointment overlaps an active maintenance blackout.",
                        ),
                    ),
                )
            )
            continue

        if _blocking_reservation_exists(asset, appointment):
            planned.append(
                PlannedAppointment(
                    appointment=appointment,
                    classification="reservation_conflict",
                    asset_id=str(asset.id),
                    user_id=str(user.id),
                    messages=(
                        _message(
                            "reservation_conflict",
                            appointment.legacy_id,
                            "Appointment overlaps an existing blocking reservation.",
                        ),
                    ),
                )
            )
            continue

        planned.append(
            PlannedAppointment(
                appointment=appointment,
                classification="would_create",
                asset_id=str(asset.id),
                user_id=str(user.id),
            )
        )

    counts: dict[str, int] = {classification: 0 for classification in PLAN_CLASSIFICATIONS}
    for item in planned:
        counts[item.classification] = counts.get(item.classification, 0) + 1
        messages.extend(item.messages)
    counts["total"] = len(planned)

    return ImportPlan(
        export=export, records=tuple(planned), counts=counts, messages=tuple(messages)
    )


def safe_plan_report(plan: ImportPlan) -> dict[str, Any]:
    return {
        "legacy_source": plan.export.legacy_source,
        "source_checksum": plan.export.source_checksum,
        "synthetic": plan.export.synthetic,
        "counts": dict(sorted(plan.counts.items())),
        "records": [
            {
                "legacy_id": record.appointment.legacy_id,
                "classification": record.classification,
                "asset_id": record.asset_id,
                "user_id": record.user_id,
                "reservation_id": record.reservation_id,
                "messages": [
                    {"level": message.level, "code": message.code, "message": message.message}
                    for message in record.messages
                ],
            }
            for record in plan.records
        ],
    }
