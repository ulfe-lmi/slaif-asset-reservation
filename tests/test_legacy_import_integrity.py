"""Import error classification at actual PostgreSQL persistence boundaries."""

from __future__ import annotations

from pathlib import Path

import pytest
from django.db import IntegrityError, connection
from tests.test_legacy_import import parsed_plan

from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.legacy_import import importer
from slaif_reservation.legacy_import.models import LegacyImportBatch, LegacyImportRecord
from slaif_reservation.reservations.models import Reservation

pytestmark = pytest.mark.django_db(transaction=True)


def appointments(count: int) -> list[dict[str, str]]:
    return [
        {
            "legacy_id": f"integrity-{index + 1}",
            "resource_legacy_id": "legacy-gpu-1",
            "requester_legacy_id": "legacy-person-1",
            "start": f"2020-01-15T{10 + 2 * index:02}:00:00",
            "end": f"2020-01-15T{11 + 2 * index:02}:00:00",
            "status": "completed",
            "purpose": "Synthetic integrity qualification",
        }
        for index in range(count)
    ]


@pytest.mark.parametrize("count", [1, 2])
@pytest.mark.parametrize("boundary", ["audit", "audit_named_like_exclusion", "record"])
def test_real_unrelated_constraint_failure_rolls_back_complete_batch(
    tmp_path: Path, count: int, boundary: str
) -> None:
    plan = parsed_plan(tmp_path, appointments=appointments(count))
    rejected_id = f"integrity-{count}"
    if boundary == "record":
        model = LegacyImportRecord
        constraint = "ica_import_record_integrity"
        expression = f"legacy_id <> '{rejected_id}'"
    else:
        model = AuditEvent
        constraint = (
            Reservation.EXCLUSION_CONSTRAINT_NAME
            if boundary == "audit_named_like_exclusion"
            else "ica_import_audit_integrity"
        )
        expression = f"action <> 'reservation.created' OR metadata->>'legacy_id' <> '{rejected_id}'"
    table = connection.ops.quote_name(model._meta.db_table)
    quoted_constraint = connection.ops.quote_name(constraint)
    with connection.cursor() as cursor:
        cursor.execute(
            f"ALTER TABLE {table} ADD CONSTRAINT {quoted_constraint} CHECK ({expression})"
        )
    try:
        with pytest.raises(IntegrityError) as raised:
            importer.apply_import(plan)
        assert raised.value.__cause__.diag.constraint_name == constraint
        assert raised.value.__cause__.sqlstate == "23514"
        # In the two-row case even the successful first reservation/audit/record
        # and the applied batch must disappear, rather than becoming a conflict.
        assert LegacyImportBatch.objects.count() == 0
        assert Reservation.objects.count() == 0
        assert AuditEvent.objects.count() == 0
        assert LegacyImportRecord.objects.count() == 0
    finally:
        with connection.cursor() as cursor:
            cursor.execute(f"ALTER TABLE {table} DROP CONSTRAINT {quoted_constraint}")


def test_actual_named_reservation_insert_exclusion_is_a_conflict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = parsed_plan(tmp_path, appointments=appointments(1))
    revalidate = importer._revalidate_for_apply
    competing: list[Reservation] = []

    def insert_after_advisory_check(item):
        checked = revalidate(item)
        assert checked.classification == "would_create"
        competing.append(
            Reservation.objects.create(
                asset_id=checked.asset_id,
                requested_by_user_id=checked.user_id,
                source=Reservation.SOURCE_MIGRATION,
                status=Reservation.STATUS_CONFIRMED,
                start_at=checked.appointment.start_at,
                end_at=checked.appointment.end_at,
                effective_end_at=checked.appointment.end_at,
                purpose="Synthetic concurrent database fixture",
            )
        )
        return checked

    # Only the scheduling seam is gated: both competing and rejected inserts
    # reach real PostgreSQL; no persistence/error/exclusion result is mocked.
    monkeypatch.setattr(importer, "_revalidate_for_apply", insert_after_advisory_check)
    result = importer.apply_import(plan)
    assert result.counts["imported"] == 0
    assert result.counts["reservation_conflict"] == 1
    assert result.plan.records[0].classification == "reservation_conflict"
    assert list(Reservation.objects.values_list("id", flat=True)) == [competing[0].id]
    assert AuditEvent.objects.count() == LegacyImportRecord.objects.count() == 0
    assert result.batch.status == LegacyImportBatch.STATUS_APPLIED
