from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Literal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.utils import timezone

from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.audit.services import append_audit_event
from slaif_reservation.legacy_import.exceptions import LegacyImportError
from slaif_reservation.legacy_import.models import LegacyImportBatch, LegacyImportRecord
from slaif_reservation.legacy_import.planner import (
    PLAN_CLASSIFICATIONS,
    _asset_allowed,
    _message,
    normalized_appointment_hash,
    plan_import,
    safe_plan_report,
)
from slaif_reservation.legacy_import.types import ImportPlan, PlannedAppointment
from slaif_reservation.reservations.exceptions import (
    POLICY_AMBIGUOUS,
    POLICY_NOT_CONFIGURED,
    ReservationDomainError,
)
from slaif_reservation.reservations.models import MaintenanceBlackout, Reservation
from slaif_reservation.reservations.services import (
    _enforce_policy,
    _is_named_reservation_constraint,
    lock_effective_policy,
)

UserModel = get_user_model()


@dataclass(frozen=True)
class ApplyResult:
    batch: LegacyImportBatch
    plan: ImportPlan
    counts: dict[str, int]


class _ReservationInsertConflict(Exception):
    """Only a named exclusion failure at the reservation INSERT boundary."""


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
    user = UserModel.objects.select_for_update(no_key=True).get(pk=item.user_id)
    asset = Asset.objects.select_for_update(no_key=True).get(pk=item.asset_id)
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
        with transaction.atomic():
            reservation.save()
    except IntegrityError as exc:
        if _is_named_reservation_constraint(exc):
            raise _ReservationInsertConflict from exc
        raise

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


def _existing_record_classification(item: PlannedAppointment) -> PlannedAppointment | None:
    appointment = item.appointment
    existing = (
        LegacyImportRecord.objects.select_for_update()
        .filter(
            legacy_source=appointment.legacy_source,
            legacy_id=appointment.legacy_id,
        )
        .first()
    )
    if existing is None:
        return None
    normalized_hash = normalized_appointment_hash(appointment)
    classification: Literal["already_imported", "legacy_changed"] = (
        "already_imported" if existing.normalized_hash == normalized_hash else "legacy_changed"
    )
    return PlannedAppointment(
        appointment=appointment,
        classification=classification,
        asset_id=item.asset_id,
        user_id=item.user_id,
        reservation_id=str(existing.reservation_id) if existing.reservation_id else None,
        messages=(
            _message(
                classification,
                appointment.legacy_id,
                "Legacy appointment was already imported."
                if classification == "already_imported"
                else "Legacy appointment changed after import; not overwritten.",
            ),
        ),
    )


def _revalidate_for_apply(item: PlannedAppointment) -> PlannedAppointment:
    existing = _existing_record_classification(item)
    if existing is not None:
        return existing

    appointment = item.appointment
    if item.asset_id is None:
        return PlannedAppointment(
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
    if item.user_id is None:
        return PlannedAppointment(
            appointment=appointment,
            classification="unmapped_user",
            asset_id=item.asset_id,
            messages=(
                _message(
                    "unmapped_user",
                    appointment.legacy_id,
                    "Legacy requester could not be mapped to an existing user.",
                ),
            ),
        )

    try:
        user = UserModel.objects.select_for_update(no_key=True).get(pk=item.user_id)
    except UserModel.DoesNotExist:
        return PlannedAppointment(
            appointment=appointment,
            classification="unmapped_user",
            asset_id=item.asset_id,
            messages=(
                _message(
                    "unmapped_user", appointment.legacy_id, "Mapped requester no longer exists."
                ),
            ),
        )

    try:
        asset = Asset.objects.select_for_update(no_key=True).get(pk=item.asset_id)
    except Asset.DoesNotExist:
        return PlannedAppointment(
            appointment=appointment,
            classification="unmapped_asset",
            messages=(
                _message(
                    "unmapped_asset",
                    appointment.legacy_id,
                    "Mapped asset no longer exists.",
                ),
            ),
        )
    if asset.parent_id:
        asset.parent = Asset.objects.get(pk=asset.parent_id)

    if not user.is_active or getattr(user, "is_service_account", False):
        return PlannedAppointment(
            appointment=appointment,
            classification="unmapped_user",
            asset_id=str(asset.id),
            user_id=str(user.id),
            messages=(
                _message(
                    "unmapped_user",
                    appointment.legacy_id,
                    "Mapped requester is not an active human user.",
                ),
            ),
        )

    if not _asset_allowed(asset):
        return PlannedAppointment(
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

    try:
        policy = lock_effective_policy(asset)
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
        policy_classification: Literal["policy_not_configured", "error"] = "policy_not_configured"
        if exc.code == POLICY_AMBIGUOUS:
            policy_classification = "error"
        elif exc.code != POLICY_NOT_CONFIGURED:
            policy_classification = "error"
        return PlannedAppointment(
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

    if MaintenanceBlackout.objects.filter(
        asset=asset,
        active=True,
        start_at__lt=appointment.end_at,
        end_at__gt=appointment.start_at,
    ).exists():
        return PlannedAppointment(
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

    if Reservation.objects.filter(
        asset=asset,
        status__in=[Reservation.STATUS_CONFIRMED, Reservation.STATUS_RELEASED],
        start_at__lt=appointment.end_at,
        effective_end_at__gt=appointment.start_at,
    ).exists():
        return PlannedAppointment(
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

    return PlannedAppointment(
        appointment=appointment,
        classification="would_create",
        asset_id=str(asset.id),
        user_id=str(user.id),
    )


def _mark_imported(item: PlannedAppointment, reservation: Reservation) -> PlannedAppointment:
    return PlannedAppointment(
        appointment=item.appointment,
        classification="imported",
        asset_id=item.asset_id,
        user_id=item.user_id,
        reservation_id=str(reservation.id),
    )


def _mark_constraint_conflict(item: PlannedAppointment) -> PlannedAppointment:
    return PlannedAppointment(
        appointment=item.appointment,
        classification="reservation_conflict",
        asset_id=item.asset_id,
        user_id=item.user_id,
        messages=(
            _message(
                "reservation_conflict",
                item.appointment.legacy_id,
                "Appointment overlaps an existing blocking reservation.",
            ),
        ),
    )


def _apply_counts(records: list[PlannedAppointment]) -> dict[str, int]:
    counts = {classification: 0 for classification in PLAN_CLASSIFICATIONS}
    counts["imported"] = 0
    for item in records:
        counts[item.classification] = counts.get(item.classification, 0) + 1
    counts["total"] = len(records)
    return counts


def apply_import(plan: ImportPlan) -> ApplyResult:
    final_records: list[PlannedAppointment] = []
    with transaction.atomic():
        # Apply batches are atomic and may visit the same legacy keys in
        # different input orders. Serialize that existing provenance boundary
        # before taking any domain locks; planning/read-only queries still run.
        with connection.cursor() as cursor:
            table = connection.ops.quote_name(LegacyImportRecord._meta.db_table)
            cursor.execute(f"LOCK TABLE {table} IN SHARE ROW EXCLUSIVE MODE")
        candidates = [item for item in plan.records if item.classification == "would_create"]
        # Lock the complete batch by category, not per item: a later principal
        # must never be acquired while earlier asset/policy locks are held.
        list(
            UserModel.objects.filter(pk__in={item.user_id for item in candidates if item.user_id})
            .order_by("pk")
            .select_for_update(no_key=True)
        )
        list(
            Asset.objects.filter(pk__in={item.asset_id for item in candidates if item.asset_id})
            .order_by("pk")
            .select_for_update(no_key=True)
        )
        batch = _create_batch(
            plan=plan,
            mode=LegacyImportBatch.MODE_APPLY,
            status=LegacyImportBatch.STATUS_APPLIED,
            summary={"counts": {"total": len(plan.records), "imported": 0}},
        )
        for item in plan.records:
            if item.classification != "would_create":
                final_records.append(item)
                continue
            final_item = _revalidate_for_apply(item)
            if final_item.classification != "would_create":
                final_records.append(final_item)
                continue
            try:
                with transaction.atomic():
                    reservation = _create_imported_reservation(item=final_item, batch=batch)
            except _ReservationInsertConflict:
                final_records.append(_mark_constraint_conflict(final_item))
                continue
            final_records.append(_mark_imported(final_item, reservation))
        counts = _apply_counts(final_records)
        final_plan = ImportPlan(
            export=plan.export,
            records=tuple(final_records),
            counts=counts,
            messages=tuple(message for record in final_records for message in record.messages),
        )
        batch.summary = {"counts": counts}
        batch.full_clean()
        batch.save(update_fields=["summary"])
    return ApplyResult(batch=batch, plan=final_plan, counts=counts)


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


def build_apply_report(result: ApplyResult) -> dict[str, Any]:
    report = safe_plan_report(result.plan)
    report["mode"] = LegacyImportBatch.MODE_APPLY
    report["batch_id"] = str(result.batch.id)
    return report
