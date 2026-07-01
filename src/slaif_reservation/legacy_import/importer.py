from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.audit.services import append_audit_event
from slaif_reservation.legacy_import.exceptions import LegacyImportError
from slaif_reservation.legacy_import.models import LegacyImportBatch, LegacyImportRecord
from slaif_reservation.legacy_import.planner import (
    normalized_appointment_hash,
    plan_import,
    safe_plan_report,
)
from slaif_reservation.legacy_import.types import ImportPlan, PlannedAppointment
from slaif_reservation.reservations.models import Reservation

UserModel = get_user_model()


@dataclass(frozen=True)
class ApplyResult:
    batch: LegacyImportBatch
    plan: ImportPlan
    counts: dict[str, int]


def _create_batch(
    *, plan: ImportPlan, mode: str, status: str, summary: dict[str, Any]
) -> LegacyImportBatch:
    batch = LegacyImportBatch(
        source_name=plan.export.legacy_source,
        source_checksum=plan.export.source_checksum,
        synthetic=plan.export.synthetic,
        mode=mode,
        status=status,
        summary=summary,
        error_count=sum(1 for message in plan.messages if message.level == "error"),
        warning_count=sum(1 for message in plan.messages if message.level == "warning"),
    )
    batch.full_clean()
    batch.save()
    return batch


def _create_imported_reservation(
    *, item: PlannedAppointment, batch: LegacyImportBatch
) -> Reservation:
    if item.asset_id is None or item.user_id is None:
        raise LegacyImportError("Cannot import an unmapped planned appointment.")
    asset = Asset.objects.select_for_update().get(pk=item.asset_id)
    user = UserModel.objects.select_for_update().get(pk=item.user_id)
    appointment = item.appointment
    reservation = Reservation(
        asset=asset,
        requested_by_user=user,
        source=Reservation.SOURCE_MIGRATION,
        status=Reservation.STATUS_CONFIRMED,
        start_at=appointment.start_at,
        end_at=appointment.end_at,
        effective_end_at=appointment.end_at,
        purpose=appointment.purpose,
    )
    reservation.full_clean(validate_constraints=False)
    try:
        reservation.save()
    except IntegrityError as exc:
        raise LegacyImportError("Reservation conflict occurred during import apply.") from exc

    append_audit_event(
        action=AuditEvent.ACTION_RESERVATION_CREATED,
        target_type="reservation",
        target_id=reservation.id,
        correlation_id=uuid.uuid4(),
        source=AuditEvent.SOURCE_MIGRATION,
        actor_user=None,
        metadata={
            "legacy_source": appointment.legacy_source,
            "legacy_id": appointment.legacy_id,
            "import_batch_id": str(batch.id),
            "asset_id": str(asset.id),
            "start_at": appointment.start_at.isoformat(),
            "end_at": appointment.end_at.isoformat(),
        },
    )

    record = LegacyImportRecord(
        batch=batch,
        legacy_source=appointment.legacy_source,
        legacy_id=appointment.legacy_id,
        normalized_hash=normalized_appointment_hash(appointment),
        result=LegacyImportRecord.RESULT_IMPORTED,
        reservation=reservation,
        safe_metadata={
            "asset_id": str(asset.id),
            "reservation_id": str(reservation.id),
            "start_at": appointment.start_at.isoformat(),
            "end_at": appointment.end_at.isoformat(),
        },
    )
    record.save()
    return reservation


def apply_import(plan: ImportPlan) -> ApplyResult:
    eligible = [record for record in plan.records if record.classification == "would_create"]
    counts = dict(plan.counts)
    counts["imported"] = 0
    with transaction.atomic():
        batch = _create_batch(
            plan=plan,
            mode=LegacyImportBatch.MODE_APPLY,
            status=LegacyImportBatch.STATUS_APPLIED,
            summary={"counts": counts},
        )
        for item in eligible:
            _create_imported_reservation(item=item, batch=batch)
            counts["imported"] += 1
        batch.summary = {"counts": counts}
        batch.full_clean()
        batch.save(update_fields=["summary"])
    return ApplyResult(batch=batch, plan=plan, counts=counts)


def inspect_summary(plan: ImportPlan) -> dict[str, Any]:
    return {
        "legacy_source": plan.export.legacy_source,
        "source_checksum": plan.export.source_checksum,
        "synthetic": plan.export.synthetic,
        "resource_count": len(plan.export.resources),
        "person_count": len(plan.export.people),
        "appointment_count": len(plan.export.appointments),
        "counts": dict(sorted(plan.counts.items())),
    }


def build_plan(export: Any, mapping: Any) -> ImportPlan:
    return plan_import(export, mapping)


def build_safe_report(plan: ImportPlan) -> dict[str, Any]:
    return safe_plan_report(plan)
