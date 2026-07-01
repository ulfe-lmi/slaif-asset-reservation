from __future__ import annotations

import json
from datetime import UTC, timedelta
from io import StringIO
from pathlib import Path
from typing import Any

import pytest
import yaml
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.legacy_import.exceptions import LegacyImportError
from slaif_reservation.legacy_import.importer import apply_import
from slaif_reservation.legacy_import.mapping import LegacyMapping, load_mapping
from slaif_reservation.legacy_import.models import LegacyImportBatch, LegacyImportRecord
from slaif_reservation.legacy_import.parser import parse_synthetic_export
from slaif_reservation.legacy_import.planner import plan_import
from slaif_reservation.reservations.models import (
    MaintenanceBlackout,
    Reservation,
    ReservationPolicy,
)
from slaif_reservation.reservations.services import create_blackout

User = get_user_model()


pytestmark = pytest.mark.django_db


def user(email: str = "legacy-user@example.com") -> User:
    return User.objects.filter(email=email).first() or User.objects.create_user(
        email=email,
        password="not-a-secret",
    )


def asset(
    slug: str = "legacy-gpu",
    *,
    legacy_id: str = "legacy-gpu-1",
    active: bool = True,
    reservable: bool = True,
) -> Asset:
    existing = Asset.objects.filter(
        legacy_source="smartscheduling-synthetic",
        legacy_id=legacy_id,
    ).first()
    if existing is not None:
        return existing
    machine = Asset.objects.create(
        slug=f"{slug}-machine",
        name=f"{slug} machine",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
    )
    return Asset.objects.create(
        parent=machine,
        slug=slug,
        name=slug,
        kind=Asset.KIND_GPU,
        active=active,
        reservable=reservable if active else False,
        legacy_source="smartscheduling-synthetic",
        legacy_id=legacy_id,
    )


def policy() -> ReservationPolicy:
    existing = ReservationPolicy.objects.filter(asset__isnull=True).first()
    if existing is not None:
        return existing
    return ReservationPolicy.objects.create(
        name="Synthetic policy",
        min_duration_minutes=15,
        max_duration_minutes=24 * 60,
        booking_horizon_days=365,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=20,
        max_concurrent_per_principal=20,
        purpose_required=False,
    )


def write_export(
    tmp_path: Path,
    *,
    appointments: list[dict[str, Any]] | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    document: dict[str, Any] = {
        "format": "slaif-smartscheduling-synthetic-v1",
        "source": "smartscheduling-synthetic",
        "synthetic": True,
        "resources": [{"legacy_id": "legacy-gpu-1", "name": "Synthetic GPU", "slug": "legacy-gpu"}],
        "people": [{"legacy_id": "legacy-person-1", "display_name": "Synthetic Person"}],
        "appointments": appointments
        or [
            {
                "legacy_id": "legacy-appointment-1",
                "resource_legacy_id": "legacy-gpu-1",
                "requester_legacy_id": "legacy-person-1",
                "start": "2026-01-15T10:00:00",
                "end": "2026-01-15T11:00:00",
                "status": "completed",
                "purpose": "Synthetic purpose",
            }
        ],
    }
    if extra:
        document.update(extra)
    path = tmp_path / "synthetic.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def write_mapping(
    tmp_path: Path, *, owner: User, asset_obj: Asset | None = None, asset_slug: str | None = None
) -> Path:
    document: dict[str, Any] = {
        "format": "slaif-smartscheduling-mapping-v1",
        "users": {"legacy-person-1": str(owner.id)},
    }
    if asset_obj is not None:
        document["assets"] = {"legacy-gpu-1": str(asset_obj.id)}
    if asset_slug is not None:
        document["asset_slugs"] = {"legacy-gpu-1": asset_slug}
    path = tmp_path / "mapping.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def parsed_plan(tmp_path: Path, *, appointments: list[dict[str, Any]] | None = None) -> Any:
    owner = user()
    asset_obj = asset()
    policy()
    export = parse_synthetic_export(
        write_export(tmp_path, appointments=appointments),
        source_name="smartscheduling-synthetic",
        timezone_name="Europe/Ljubljana",
    )
    mapping = load_mapping(write_mapping(tmp_path, owner=owner, asset_obj=asset_obj))
    return plan_import(export, mapping)


def test_valid_synthetic_export_parses_and_normalizes_to_utc(tmp_path: Path) -> None:
    export = parse_synthetic_export(
        write_export(tmp_path),
        source_name="smartscheduling-synthetic",
        timezone_name="Europe/Ljubljana",
    )

    assert export.synthetic is True
    assert len(export.appointments) == 1
    assert export.appointments[0].start_at.tzinfo == UTC
    assert export.appointments[0].legacy_id == "legacy-appointment-1"


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            {
                "appointments": [
                    {
                        "legacy_id": "missing",
                        "requester_legacy_id": "legacy-person-1",
                        "start": "2026-01-15T10:00:00",
                        "end": "2026-01-15T11:00:00",
                        "status": "completed",
                    }
                ]
            },
            "resource_legacy_id is required",
        ),
        (
            {
                "appointments": [
                    {
                        "legacy_id": "bad-time",
                        "resource_legacy_id": "legacy-gpu-1",
                        "requester_legacy_id": "legacy-person-1",
                        "start": "not-a-date",
                        "end": "2026-01-15T11:00:00",
                        "status": "completed",
                    }
                ]
            },
            "start must be an ISO local datetime",
        ),
        (
            {
                "appointments": [
                    {
                        "legacy_id": "unknown-status",
                        "resource_legacy_id": "legacy-gpu-1",
                        "requester_legacy_id": "legacy-person-1",
                        "start": "2026-01-15T10:00:00",
                        "end": "2026-01-15T11:00:00",
                        "status": "mystery",
                    }
                ]
            },
            "Unknown legacy status",
        ),
        (
            {
                "people": [
                    {
                        "legacy_id": "legacy-person-1",
                        "display_name": "Synthetic",
                        "email": "private@example.test",
                    }
                ]
            },
            "Unsupported person field",
        ),
    ],
)
def test_parser_fails_closed_for_invalid_or_private_fields(
    tmp_path: Path,
    mutation: dict[str, Any],
    message: str,
) -> None:
    path = write_export(tmp_path, extra=mutation)

    with pytest.raises(LegacyImportError, match=message):
        parse_synthetic_export(
            path,
            source_name="smartscheduling-synthetic",
            timezone_name="Europe/Ljubljana",
        )


def test_parser_rejects_duplicate_ids_unsupported_extension_and_url(tmp_path: Path) -> None:
    duplicate = write_export(
        tmp_path,
        appointments=[
            {
                "legacy_id": "dup",
                "resource_legacy_id": "legacy-gpu-1",
                "requester_legacy_id": "legacy-person-1",
                "start": "2026-01-15T10:00:00",
                "end": "2026-01-15T11:00:00",
                "status": "completed",
            },
            {
                "legacy_id": "dup",
                "resource_legacy_id": "legacy-gpu-1",
                "requester_legacy_id": "legacy-person-1",
                "start": "2026-01-15T12:00:00",
                "end": "2026-01-15T13:00:00",
                "status": "completed",
            },
        ],
    )
    with pytest.raises(LegacyImportError, match="Duplicate appointment legacy ID"):
        parse_synthetic_export(
            duplicate,
            source_name="smartscheduling-synthetic",
            timezone_name="Europe/Ljubljana",
        )

    unsupported = tmp_path / "export.smart-export.private"
    unsupported.write_text("{}", encoding="utf-8")
    with pytest.raises(LegacyImportError, match="Unsupported export file extension"):
        parse_synthetic_export(
            unsupported,
            source_name="smartscheduling-synthetic",
            timezone_name="Europe/Ljubljana",
        )

    with pytest.raises(LegacyImportError, match="URL inputs are not accepted"):
        parse_synthetic_export(
            Path("https://legacy.example/export.yaml"),
            source_name="smartscheduling-synthetic",
            timezone_name="Europe/Ljubljana",
        )


def test_parser_rejects_nonexistent_and_ambiguous_local_times(tmp_path: Path) -> None:
    nonexistent = write_export(
        tmp_path,
        appointments=[
            {
                "legacy_id": "gap",
                "resource_legacy_id": "legacy-gpu-1",
                "requester_legacy_id": "legacy-person-1",
                "start": "2026-03-29T02:30:00",
                "end": "2026-03-29T03:30:00",
                "status": "completed",
            }
        ],
    )
    with pytest.raises(LegacyImportError, match="does not exist"):
        parse_synthetic_export(
            nonexistent,
            source_name="smartscheduling-synthetic",
            timezone_name="Europe/Ljubljana",
        )

    ambiguous = write_export(
        tmp_path,
        appointments=[
            {
                "legacy_id": "fold",
                "resource_legacy_id": "legacy-gpu-1",
                "requester_legacy_id": "legacy-person-1",
                "start": "2026-10-25T02:30:00",
                "end": "2026-10-25T03:30:00",
                "status": "completed",
            }
        ],
    )
    with pytest.raises(LegacyImportError, match="ambiguous"):
        parse_synthetic_export(
            ambiguous,
            source_name="smartscheduling-synthetic",
            timezone_name="Europe/Ljubljana",
        )


def test_mapping_by_legacy_id_and_slug_and_unmapped_classifications(tmp_path: Path) -> None:
    owner = user()
    asset_obj = asset()
    policy()
    export = parse_synthetic_export(
        write_export(tmp_path),
        source_name="smartscheduling-synthetic",
        timezone_name="Europe/Ljubljana",
    )

    plan = plan_import(
        export, load_mapping(write_mapping(tmp_path, owner=owner, asset_obj=asset_obj))
    )
    assert plan.counts["would_create"] == 1
    assert plan.records[0].asset_id == str(asset_obj.id)
    assert plan.records[0].user_id == str(owner.id)

    by_slug = plan_import(
        export, load_mapping(write_mapping(tmp_path, owner=owner, asset_slug=asset_obj.slug))
    )
    assert by_slug.counts["would_create"] == 1

    no_user_mapping = LegacyMapping(assets={"legacy-gpu-1": asset_obj.id})
    no_user_plan = plan_import(export, no_user_mapping)
    assert no_user_plan.counts["unmapped_user"] == 1


def test_dry_run_writes_no_reservations_or_audit_events(tmp_path: Path) -> None:
    plan = parsed_plan(tmp_path)

    assert plan.counts["would_create"] == 1
    assert Reservation.objects.count() == 0
    assert AuditEvent.objects.count() == 0
    assert LegacyImportBatch.objects.count() == 0


def test_apply_creates_migration_reservation_audit_and_is_idempotent(tmp_path: Path) -> None:
    plan = parsed_plan(tmp_path)

    result = apply_import(plan)

    reservation = Reservation.objects.get()
    assert reservation.source == Reservation.SOURCE_MIGRATION
    assert reservation.status == Reservation.STATUS_CONFIRMED
    assert result.counts["imported"] == 1
    audit = AuditEvent.objects.get(action=AuditEvent.ACTION_RESERVATION_CREATED)
    assert audit.source == AuditEvent.SOURCE_MIGRATION
    assert audit.metadata["legacy_source"] == "smartscheduling-synthetic"
    assert audit.metadata["legacy_id"] == "legacy-appointment-1"
    assert "purpose" not in audit.metadata
    assert LegacyImportRecord.objects.count() == 1

    repeat = parsed_plan(tmp_path)
    assert repeat.counts["already_imported"] == 1
    repeat_result = apply_import(repeat)
    assert repeat_result.counts["imported"] == 0
    assert Reservation.objects.count() == 1
    assert AuditEvent.objects.count() == 1


def test_changed_legacy_record_is_reported_not_overwritten(tmp_path: Path) -> None:
    apply_import(parsed_plan(tmp_path))
    changed = parsed_plan(
        tmp_path,
        appointments=[
            {
                "legacy_id": "legacy-appointment-1",
                "resource_legacy_id": "legacy-gpu-1",
                "requester_legacy_id": "legacy-person-1",
                "start": "2026-01-15T10:30:00",
                "end": "2026-01-15T11:30:00",
                "status": "completed",
            }
        ],
    )

    assert changed.counts["legacy_changed"] == 1
    assert apply_import(changed).counts["imported"] == 0
    assert Reservation.objects.count() == 1


def test_blackout_conflict_deactivated_blackout_and_reservation_conflict(tmp_path: Path) -> None:
    owner = user()
    asset_obj = asset()
    staff = User.objects.create_user(
        email="legacy-staff@example.com",
        password="not-a-secret",
        is_staff=True,
    )
    policy()
    export = parse_synthetic_export(
        write_export(tmp_path),
        source_name="smartscheduling-synthetic",
        timezone_name="Europe/Ljubljana",
    )
    mapping = load_mapping(write_mapping(tmp_path, owner=owner, asset_obj=asset_obj))

    create_blackout(
        asset=asset_obj,
        actor_user=staff,
        reason="Synthetic blackout",
        start_at=export.appointments[0].start_at,
        end_at=export.appointments[0].end_at,
        confirmed_overlap=True,
    )
    assert plan_import(export, mapping).counts["blackout_conflict"] == 1

    blackout = MaintenanceBlackout.objects.get()
    blackout.active = False
    blackout.deactivated_at = timezone.now()
    blackout.deactivated_by = staff
    blackout._slaif_reservation_service_update = True
    blackout.save()
    delattr(blackout, "_slaif_reservation_service_update")
    assert plan_import(export, mapping).counts["would_create"] == 1

    Reservation.objects.create(
        asset=asset_obj,
        requested_by_user=owner,
        source=Reservation.SOURCE_MIGRATION,
        status=Reservation.STATUS_CONFIRMED,
        start_at=export.appointments[0].start_at,
        end_at=export.appointments[0].end_at,
        effective_end_at=export.appointments[0].end_at,
    )
    assert plan_import(export, mapping).counts["reservation_conflict"] == 1


def test_status_asset_policy_classifications(tmp_path: Path) -> None:
    owner = user()
    inactive_asset = asset(active=False, reservable=False)
    policy()
    cancelled = [
        {
            "legacy_id": "cancelled",
            "resource_legacy_id": "legacy-gpu-1",
            "requester_legacy_id": "legacy-person-1",
            "start": "2026-01-15T10:00:00",
            "end": "2026-01-15T11:00:00",
            "status": "cancelled",
        },
        {
            "legacy_id": "waitlisted",
            "resource_legacy_id": "legacy-gpu-1",
            "requester_legacy_id": "legacy-person-1",
            "start": "2026-01-15T12:00:00",
            "end": "2026-01-15T13:00:00",
            "status": "waitlisted",
        },
        {
            "legacy_id": "inactive",
            "resource_legacy_id": "legacy-gpu-1",
            "requester_legacy_id": "legacy-person-1",
            "start": "2026-01-15T14:00:00",
            "end": "2026-01-15T15:00:00",
            "status": "completed",
        },
    ]
    export = parse_synthetic_export(
        write_export(tmp_path, appointments=cancelled),
        source_name="smartscheduling-synthetic",
        timezone_name="Europe/Ljubljana",
    )
    plan = plan_import(
        export, load_mapping(write_mapping(tmp_path, owner=owner, asset_obj=inactive_asset))
    )

    assert plan.counts["skipped_status"] == 1
    assert plan.counts["unsupported_status"] == 1
    assert plan.counts["asset_not_reservable"] == 1


def test_command_dry_run_report_is_redacted_and_apply_requires_explicit_flag(
    tmp_path: Path,
) -> None:
    owner = user()
    asset_obj = asset()
    policy()
    export_path = write_export(tmp_path)
    mapping_path = write_mapping(tmp_path, owner=owner, asset_obj=asset_obj)
    report_path = tmp_path / "report.json"
    stdout = StringIO()

    call_command(
        "import_smartscheduling_export",
        "--input",
        str(export_path),
        "--source",
        "smartscheduling-synthetic",
        "--timezone",
        "Europe/Ljubljana",
        "--mapping",
        str(mapping_path),
        "--report-json",
        str(report_path),
        stdout=stdout,
    )

    output = stdout.getvalue()
    assert "mode=dry-run" in output
    assert "would_create=1" in output
    assert Reservation.objects.count() == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    encoded_report = json.dumps(report)
    assert "Synthetic purpose" not in encoded_report
    assert "phone" not in encoded_report.lower()

    stdout = StringIO()
    call_command(
        "import_smartscheduling_export",
        "--apply",
        "--input",
        str(export_path),
        "--source",
        "smartscheduling-synthetic",
        "--timezone",
        "Europe/Ljubljana",
        "--mapping",
        str(mapping_path),
        stdout=stdout,
    )
    assert "mode=apply" in stdout.getvalue()
    assert "imported=1" in stdout.getvalue()
    assert Reservation.objects.count() == 1


def test_command_inspect_and_plan_outputs_are_deterministic(tmp_path: Path) -> None:
    owner = user()
    asset_obj = asset()
    policy()
    export_path = write_export(tmp_path)
    mapping_path = write_mapping(tmp_path, owner=owner, asset_obj=asset_obj)

    inspect_out = StringIO()
    call_command(
        "inspect_smartscheduling_export",
        "--input",
        str(export_path),
        "--source",
        "smartscheduling-synthetic",
        "--timezone",
        "Europe/Ljubljana",
        "--mapping",
        str(mapping_path),
        stdout=inspect_out,
    )
    assert "mode=inspect" in inspect_out.getvalue()
    assert "appointments=1" in inspect_out.getvalue()

    plan_out = StringIO()
    call_command(
        "plan_smartscheduling_import",
        "--input",
        str(export_path),
        "--source",
        "smartscheduling-synthetic",
        "--timezone",
        "Europe/Ljubljana",
        "--mapping",
        str(mapping_path),
        stdout=plan_out,
    )
    assert "mode=dry-run" in plan_out.getvalue()
    assert "would_create=1" in plan_out.getvalue()


def test_audit_failure_rolls_back_imported_reservation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    plan = parsed_plan(tmp_path)

    def fail_audit(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("synthetic audit failure")

    monkeypatch.setattr("slaif_reservation.legacy_import.importer.append_audit_event", fail_audit)

    with pytest.raises(RuntimeError, match="synthetic audit failure"):
        apply_import(plan)

    assert Reservation.objects.count() == 0
    assert LegacyImportBatch.objects.count() == 0
    assert LegacyImportRecord.objects.count() == 0
    assert AuditEvent.objects.count() == 0


def test_future_import_uses_current_policy_boundaries(tmp_path: Path) -> None:
    owner = user()
    asset_obj = asset()
    ReservationPolicy.objects.create(
        name="Short max policy",
        min_duration_minutes=15,
        max_duration_minutes=30,
        booking_horizon_days=365,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=20,
        max_concurrent_per_principal=20,
        purpose_required=False,
    )
    start = timezone.localtime(timezone.now() + timedelta(days=2)).replace(tzinfo=None)
    end = start + timedelta(hours=1)
    export = parse_synthetic_export(
        write_export(
            tmp_path,
            appointments=[
                {
                    "legacy_id": "future-too-long",
                    "resource_legacy_id": "legacy-gpu-1",
                    "requester_legacy_id": "legacy-person-1",
                    "start": start.isoformat(timespec="minutes"),
                    "end": end.isoformat(timespec="minutes"),
                    "status": "confirmed",
                }
            ],
        ),
        source_name="smartscheduling-synthetic",
        timezone_name="Europe/Ljubljana",
    )

    plan = plan_import(
        export, load_mapping(write_mapping(tmp_path, owner=owner, asset_obj=asset_obj))
    )

    assert plan.counts["error"] == 1
    assert plan.records[0].messages[0].code == "error"
