"""022-a: legacy-import apply vs ordinary service concurrency, separate transactions.

Barrier-controlled races against real PostgreSQL (transaction=True, per-thread
connections, no database mocks): apply_import revalidates and writes
SOURCE_MIGRATION reservations directly while create_reservation /
create_blackout run concurrently.  Every iteration uses fresh asset/user/
appointment identifiers so iterations are independent.

Pause seams (verified against the source at this revision):
- booking side: services._raise_if_blackout_overlap is called by
  create_reservation AFTER the principal -> asset -> policy row locks, before
  the advisory overlap checks and the insert;
- import side: importer._asset_allowed is called by _revalidate_for_apply
  AFTER the asset row lock (and the user row lock) is held, before the policy
  lock, the locking blackout/reservation probes and the write.
"""

from __future__ import annotations

import threading
import time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import yaml
from django.db import close_old_connections
from django.utils import timezone

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.legacy_import import importer
from slaif_reservation.legacy_import.importer import apply_import
from slaif_reservation.legacy_import.mapping import load_mapping
from slaif_reservation.legacy_import.models import LegacyImportRecord
from slaif_reservation.legacy_import.parser import parse_synthetic_export
from slaif_reservation.legacy_import.planner import plan_import
from slaif_reservation.reservations import services
from slaif_reservation.reservations.exceptions import (
    BLACKOUT_CONFLICT,
    RESERVATION_CONFLICT,
    ReservationDomainError,
)
from slaif_reservation.reservations.models import (
    MaintenanceBlackout,
    Reservation,
    ReservationPolicy,
)

LEGACY_SOURCE = "smartscheduling-synthetic"
SOURCE_TZ = "Europe/Ljubljana"
BLOCKING_STATUSES = [Reservation.STATUS_CONFIRMED, Reservation.STATUS_RELEASED]


def make_user(email: str) -> User:
    return User.objects.create_user(email=email, password="not-a-secret")


def make_staff(email: str) -> User:
    return User.objects.create_user(
        email=email,
        password="not-a-secret",
        is_staff=True,
    )


def make_asset(slug: str) -> Asset:
    return Asset.objects.create(
        slug=slug,
        name=slug,
        kind=Asset.KIND_GPU,
        active=True,
        reservable=True,
    )


def make_policy() -> None:
    ReservationPolicy.objects.create(
        name="global",
        min_duration_minutes=15,
        max_duration_minutes=24 * 60,
        booking_horizon_days=365,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=20,
        max_concurrent_per_principal=20,
        purpose_required=False,
    )


def run_parallel(calls) -> list[str]:
    """Equivalent local copy of the 020-a run_parallel barrier harness."""
    barrier = threading.Barrier(len(calls))
    results: list[str] = []
    lock = threading.Lock()

    def target(call) -> None:
        close_old_connections()
        barrier.wait(timeout=10)
        try:
            call()
        except ReservationDomainError as exc:
            outcome = exc.code
        else:
            outcome = "committed"
        finally:
            close_old_connections()
        with lock:
            results.append(outcome)

    threads = [threading.Thread(target=target, args=(call,)) for call in calls]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)
    assert all(not thread.is_alive() for thread in threads)
    return sorted(results)


def _local_iso(moment: datetime) -> str:
    return timezone.localtime(moment).replace(tzinfo=None).isoformat(timespec="minutes")


def write_export(tmp_path: Path, iteration: int, *, start: datetime, end: datetime) -> Path:
    document = {
        "format": "slaif-smartscheduling-synthetic-v1",
        "source": LEGACY_SOURCE,
        "synthetic": True,
        "resources": [
            {
                "legacy_id": f"res-{iteration}",
                "name": f"Synthetic GPU {iteration}",
                "slug": f"synthetic-gpu-{iteration}",
            }
        ],
        "people": [
            {"legacy_id": f"person-{iteration}", "display_name": f"Synthetic Person {iteration}"}
        ],
        "appointments": [
            {
                "legacy_id": f"appointment-{iteration}",
                "resource_legacy_id": f"res-{iteration}",
                "requester_legacy_id": f"person-{iteration}",
                "start": _local_iso(start),
                "end": _local_iso(end),
                "status": "confirmed",
                "purpose": "Synthetic purpose",
            }
        ],
    }
    path = tmp_path / f"synthetic-{iteration}.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def write_mapping(tmp_path: Path, iteration: int, *, user: User, asset_obj: Asset) -> Path:
    document = {
        "format": "slaif-smartscheduling-mapping-v1",
        "users": {f"person-{iteration}": str(user.id)},
        "assets": {f"res-{iteration}": str(asset_obj.id)},
    }
    path = tmp_path / f"mapping-{iteration}.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def build_plan(
    tmp_path: Path, iteration: int, *, user: User, asset_obj: Asset, start: datetime, end: datetime
):
    export = parse_synthetic_export(
        write_export(tmp_path, iteration, start=start, end=end),
        source_name=LEGACY_SOURCE,
        timezone_name=SOURCE_TZ,
    )
    mapping = load_mapping(write_mapping(tmp_path, iteration, user=user, asset_obj=asset_obj))
    plan = plan_import(export, mapping)
    assert plan.counts["would_create"] == 1
    assert plan.records[0].asset_id == str(asset_obj.id)
    assert plan.records[0].user_id == str(user.id)
    return plan


def _blocking_reservations(asset: Asset, start: datetime, end: datetime) -> int:
    return Reservation.objects.filter(
        asset=asset,
        status__in=BLOCKING_STATUSES,
        start_at__lt=end,
        effective_end_at__gt=start,
    ).count()


def _active_blackouts(asset: Asset, start: datetime, end: datetime) -> int:
    return MaintenanceBlackout.objects.filter(
        asset=asset,
        active=True,
        start_at__lt=end,
        end_at__gt=start,
    ).count()


def _migration_audits_for_asset(asset: Asset) -> int:
    return AuditEvent.objects.filter(
        action=AuditEvent.ACTION_RESERVATION_CREATED,
        source=AuditEvent.SOURCE_MIGRATION,
        metadata__asset_id=str(asset.id),
    ).count()


def _apply_call(plan, result_store: dict):
    def call() -> None:
        result_store["result"] = apply_import(plan)

    return call


def _reservation_call(asset: Asset, booker: User, start: datetime, end: datetime, now: datetime):
    def call() -> None:
        services.create_reservation(
            asset=asset,
            requested_by_user=booker,
            start_at=start,
            end_at=end,
            purpose="",
            now=now,
        )

    return call


def _blackout_call(asset: Asset, staff: User, start: datetime, end: datetime):
    def call() -> None:
        services.create_blackout(
            asset=asset,
            actor_user=staff,
            reason="maintenance",
            start_at=start,
            end_at=end + timedelta(hours=1),
            confirmed_overlap=False,
        )

    return call


def _created_audits_for(row: Reservation) -> int:
    return AuditEvent.objects.filter(
        action=AuditEvent.ACTION_RESERVATION_CREATED,
        target_id=row.id,
    ).count()


@pytest.mark.django_db(transaction=True)
def test_apply_vs_reservation_race_exactly_one_commits_across_repeats(tmp_path: Path) -> None:
    make_policy()
    observed: list[str] = []
    for iteration in range(5):
        asset = make_asset(f"race-a{iteration}")
        mapped_user = make_user(f"import-user{iteration}@example.com")
        booker = make_user(f"booker{iteration}@example.com")
        now = timezone.now()
        start = now + timedelta(minutes=10)
        end = start + timedelta(hours=1)
        plan = build_plan(
            tmp_path, iteration, user=mapped_user, asset_obj=asset, start=start, end=end
        )
        apply_result: dict = {}
        outcomes = run_parallel(
            [
                _apply_call(plan, apply_result),
                _reservation_call(asset, booker, start, end, now),
            ]
        )
        assert len(outcomes) == 2

        # Invariant: exactly one committed blocking reservation on X/R, never both.
        assert _blocking_reservations(asset, start, end) == 1
        row = Reservation.objects.get(
            asset=asset,
            status__in=BLOCKING_STATUSES,
            start_at__lt=end,
            effective_end_at__gt=start,
        )
        counts = apply_result["result"].batch.summary["counts"]

        if RESERVATION_CONFLICT in outcomes:
            # Booking side lost: import side committed the migration row.
            assert Counter(outcomes) == Counter(["committed", RESERVATION_CONFLICT])
            assert row.source == Reservation.SOURCE_MIGRATION
            assert row.status == Reservation.STATUS_CONFIRMED
            assert row.requested_by_user_id == mapped_user.id
            assert counts["imported"] == 1
            assert _created_audits_for(row) == 1
            audit = AuditEvent.objects.get(
                action=AuditEvent.ACTION_RESERVATION_CREATED, target_id=row.id
            )
            assert audit.source == AuditEvent.SOURCE_MIGRATION
            assert audit.actor_user_id is None
            record = LegacyImportRecord.objects.get(
                legacy_source=LEGACY_SOURCE, legacy_id=f"appointment-{iteration}"
            )
            assert record.result == LegacyImportRecord.RESULT_IMPORTED
            assert record.reservation_id == row.id
            observed.append("import_wins")
        else:
            # Import side lost internally: booking committed, apply batch applied
            # with the item classified reservation_conflict.
            assert Counter(outcomes) == Counter(["committed", "committed"])
            assert row.source == Reservation.SOURCE_WEB
            assert row.status == Reservation.STATUS_CONFIRMED
            assert row.requested_by_user_id == booker.id
            assert counts["reservation_conflict"] == 1
            assert counts["imported"] == 0
            assert _created_audits_for(row) == 1
            audit = AuditEvent.objects.get(
                action=AuditEvent.ACTION_RESERVATION_CREATED, target_id=row.id
            )
            assert audit.source == AuditEvent.SOURCE_WEB
            assert audit.actor_user_id == booker.id
            # No migration artifacts for the lost import.
            assert (
                Reservation.objects.filter(asset=asset, source=Reservation.SOURCE_MIGRATION).count()
                == 0
            )
            assert (
                LegacyImportRecord.objects.filter(
                    legacy_source=LEGACY_SOURCE, legacy_id=f"appointment-{iteration}"
                ).count()
                == 0
            )
            assert _migration_audits_for_asset(asset) == 0
            observed.append("booking_wins")

    print(f"022-a test 1 observed orderings: {observed}")


@pytest.mark.django_db(transaction=True)
def test_import_wins_reservation_blocked_on_asset_lock_then_conflicts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    make_policy()
    asset = make_asset("race-b")
    mapped_user = make_user("import-user@example.com")
    booker = make_user("booker@example.com")
    now = timezone.now()
    start = now + timedelta(minutes=10)
    end = start + timedelta(hours=1)
    plan = build_plan(tmp_path, 0, user=mapped_user, asset_obj=asset, start=start, end=end)

    import_holds_lock = threading.Event()
    release_import = threading.Event()
    booking_holds_lock = threading.Event()
    release_booking = threading.Event()
    original_asset_allowed = importer._asset_allowed
    original_blackout_check = services._raise_if_blackout_overlap

    def pause_import_after_asset_lock(asset_obj: Asset) -> bool:
        import_holds_lock.set()
        assert release_import.wait(timeout=10)
        return original_asset_allowed(asset_obj)

    def pause_booking_after_asset_lock(*args: object, **kwargs: object) -> None:
        booking_holds_lock.set()
        assert release_booking.wait(timeout=10)
        original_blackout_check(*args, **kwargs)

    monkeypatch.setattr(importer, "_asset_allowed", pause_import_after_asset_lock)
    monkeypatch.setattr(services, "_raise_if_blackout_overlap", pause_booking_after_asset_lock)

    apply_result: dict = {}

    def import_call() -> None:
        close_old_connections()
        try:
            apply_result["result"] = apply_import(plan)
        finally:
            close_old_connections()

    import_thread = threading.Thread(target=import_call)
    import_thread.start()
    assert import_holds_lock.wait(timeout=10)

    booking_outcome: dict = {}

    def booking_call() -> None:
        close_old_connections()
        try:
            services.create_reservation(
                asset=asset,
                requested_by_user=booker,
                start_at=start,
                end_at=end,
                purpose="",
                now=now,
            )
            booking_outcome["code"] = "committed"
        except ReservationDomainError as exc:
            booking_outcome["code"] = exc.code
        finally:
            close_old_connections()

    booking_thread = threading.Thread(target=booking_call)
    booking_thread.start()
    time.sleep(0.25)
    assert booking_thread.is_alive()  # booking blocked on the asset row lock

    release_import.set()
    import_thread.join(timeout=10)
    assert not import_thread.is_alive()
    result = apply_result["result"]
    assert result.counts["imported"] == 1
    assert result.plan.records[0].classification == "imported"
    # Import is committed while the booking has not committed yet (it cannot
    # pass the gated advisory stage before release_booking).
    assert _blocking_reservations(asset, start, end) == 1
    assert not booking_holds_lock.is_set() or booking_thread.is_alive()

    assert booking_holds_lock.wait(timeout=10)
    release_booking.set()
    booking_thread.join(timeout=10)
    assert not booking_thread.is_alive()
    assert booking_outcome["code"] == RESERVATION_CONFLICT

    # Final state: exactly one reservation on X/R, SOURCE_MIGRATION, with its
    # audit event (source migration, no actor) and the import record.
    assert _blocking_reservations(asset, start, end) == 1
    row = Reservation.objects.get(
        asset=asset, status__in=BLOCKING_STATUSES, start_at__lt=end, effective_end_at__gt=start
    )
    assert row.source == Reservation.SOURCE_MIGRATION
    assert row.status == Reservation.STATUS_CONFIRMED
    assert row.requested_by_user_id == mapped_user.id
    assert _created_audits_for(row) == 1
    audit = AuditEvent.objects.get(action=AuditEvent.ACTION_RESERVATION_CREATED, target_id=row.id)
    assert audit.source == AuditEvent.SOURCE_MIGRATION
    assert audit.actor_user_id is None
    record = LegacyImportRecord.objects.get(legacy_source=LEGACY_SOURCE, legacy_id="appointment-0")
    assert record.result == LegacyImportRecord.RESULT_IMPORTED
    assert record.reservation_id == row.id
    assert result.batch.summary["counts"]["imported"] == 1


@pytest.mark.django_db(transaction=True)
def test_reservation_wins_import_blocked_on_asset_lock_then_conflicts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    make_policy()
    asset = make_asset("race-c")
    mapped_user = make_user("import-user@example.com")
    booker = make_user("booker@example.com")
    now = timezone.now()
    start = now + timedelta(minutes=10)
    end = start + timedelta(hours=1)
    plan = build_plan(tmp_path, 0, user=mapped_user, asset_obj=asset, start=start, end=end)

    booking_holds_lock = threading.Event()
    release_booking = threading.Event()
    original_blackout_check = services._raise_if_blackout_overlap

    def pause_booking_after_asset_lock(*args: object, **kwargs: object) -> None:
        booking_holds_lock.set()
        assert release_booking.wait(timeout=10)
        original_blackout_check(*args, **kwargs)

    monkeypatch.setattr(services, "_raise_if_blackout_overlap", pause_booking_after_asset_lock)

    def booking_call() -> None:
        close_old_connections()
        try:
            services.create_reservation(
                asset=asset,
                requested_by_user=booker,
                start_at=start,
                end_at=end,
                purpose="",
                now=now,
            )
        finally:
            close_old_connections()

    booking_thread = threading.Thread(target=booking_call)
    booking_thread.start()
    assert booking_holds_lock.wait(timeout=10)

    apply_result: dict = {}

    def import_call() -> None:
        close_old_connections()
        try:
            apply_result["result"] = apply_import(plan)
        finally:
            close_old_connections()

    import_thread = threading.Thread(target=import_call)
    import_thread.start()
    time.sleep(0.25)
    assert import_thread.is_alive()  # import blocked on the asset row lock

    release_booking.set()
    booking_thread.join(timeout=10)
    assert not booking_thread.is_alive()

    import_thread.join(timeout=10)
    assert not import_thread.is_alive()
    result = apply_result["result"]
    assert result.counts["imported"] == 0
    assert result.counts["reservation_conflict"] == 1
    assert result.plan.records[0].classification == "reservation_conflict"
    assert result.batch.summary["counts"]["reservation_conflict"] == 1

    # Final state: exactly one reservation on X/R, the booking side's, with its
    # audit event; no migration artifacts for the lost import.
    assert _blocking_reservations(asset, start, end) == 1
    row = Reservation.objects.get(
        asset=asset, status__in=BLOCKING_STATUSES, start_at__lt=end, effective_end_at__gt=start
    )
    assert row.source == Reservation.SOURCE_WEB
    assert row.status == Reservation.STATUS_CONFIRMED
    assert row.requested_by_user_id == booker.id
    assert _created_audits_for(row) == 1
    audit = AuditEvent.objects.get(action=AuditEvent.ACTION_RESERVATION_CREATED, target_id=row.id)
    assert audit.source == AuditEvent.SOURCE_WEB
    assert audit.actor_user_id == booker.id
    assert Reservation.objects.filter(asset=asset, source=Reservation.SOURCE_MIGRATION).count() == 0
    assert (
        LegacyImportRecord.objects.filter(
            legacy_source=LEGACY_SOURCE, legacy_id="appointment-0"
        ).count()
        == 0
    )
    assert _migration_audits_for_asset(asset) == 0


@pytest.mark.django_db(transaction=True)
def test_apply_vs_blackout_race_never_leaves_migration_over_active_blackout(
    tmp_path: Path,
) -> None:
    make_policy()
    observed: list[str] = []
    for iteration in range(5):
        asset = make_asset(f"race-d{iteration}")
        mapped_user = make_user(f"import-user{iteration}@example.com")
        staff = make_staff(f"staff{iteration}@example.com")
        now = timezone.now()
        start = now + timedelta(minutes=10)
        end = start + timedelta(hours=1)
        plan = build_plan(
            tmp_path, iteration, user=mapped_user, asset_obj=asset, start=start, end=end
        )
        apply_result: dict = {}
        outcomes = run_parallel(
            [
                _apply_call(plan, apply_result),
                _blackout_call(asset, staff, start, end),
            ]
        )
        assert len(outcomes) == 2

        # Invariant: never a committed migration reservation overlapping X/M
        # while an ACTIVE blackout overlaps X/M.
        reservation_count = _blocking_reservations(asset, start, end)
        blackout_count = _active_blackouts(asset, start, end)
        assert (reservation_count, blackout_count) in [(1, 0), (0, 1)]
        counts = apply_result["result"].batch.summary["counts"]

        if blackout_count == 1:
            # Blackout committed first: import item classified blackout_conflict.
            assert Counter(outcomes) == Counter(["committed", "committed"])
            assert counts["blackout_conflict"] == 1
            assert counts["imported"] == 0
            assert Reservation.objects.filter(asset=asset).count() == 0
            assert (
                LegacyImportRecord.objects.filter(
                    legacy_source=LEGACY_SOURCE, legacy_id=f"appointment-{iteration}"
                ).count()
                == 0
            )
            assert _migration_audits_for_asset(asset) == 0
            blackout = MaintenanceBlackout.objects.get(asset=asset)
            assert blackout.active is True
            assert blackout.created_by_id == staff.id
            assert (
                AuditEvent.objects.filter(
                    action=AuditEvent.ACTION_BLACKOUT_CREATED,
                    target_type="maintenance_blackout",
                    target_id=blackout.id,
                ).count()
                == 1
            )
            observed.append("blackout_wins")
        else:
            # Import committed first: blackout creation raised BLACKOUT_CONFLICT.
            assert Counter(outcomes) == Counter([BLACKOUT_CONFLICT, "committed"])
            assert counts["imported"] == 1
            row = Reservation.objects.get(asset=asset)
            assert row.source == Reservation.SOURCE_MIGRATION
            assert row.status == Reservation.STATUS_CONFIRMED
            assert row.requested_by_user_id == mapped_user.id
            assert MaintenanceBlackout.objects.filter(asset=asset).count() == 0
            assert _created_audits_for(row) == 1
            audit = AuditEvent.objects.get(
                action=AuditEvent.ACTION_RESERVATION_CREATED, target_id=row.id
            )
            assert audit.source == AuditEvent.SOURCE_MIGRATION
            assert audit.actor_user_id is None
            observed.append("import_wins")

    print(f"022-a test 4 observed orderings: {observed}")
