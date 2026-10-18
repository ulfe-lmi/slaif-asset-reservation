"""Real PostgreSQL locking across ordinary services and synthetic imports."""

from __future__ import annotations

import threading
import time
import uuid
from contextlib import nullcontext
from datetime import timedelta
from pathlib import Path

import pytest
import yaml
from django.contrib.auth.models import Permission
from django.db import close_old_connections, connection, transaction
from django.db.models.query import QuerySet
from django.utils import timezone
from tests import test_legacy_import_concurrency as support
from tests.test_legacy_import_concurrency import (
    build_plan,
    make_asset,
    make_policy,
    make_staff,
    make_user,
)

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.legacy_import import importer
from slaif_reservation.legacy_import.mapping import load_mapping
from slaif_reservation.legacy_import.models import LegacyImportBatch, LegacyImportRecord
from slaif_reservation.legacy_import.parser import parse_synthetic_export
from slaif_reservation.legacy_import.planner import plan_import
from slaif_reservation.reservations import services
from slaif_reservation.reservations.exceptions import (
    POLICY_NOT_CONFIGURED,
    RESERVATION_CONFLICT,
    ReservationDomainError,
)
from slaif_reservation.reservations.models import Reservation, ReservationPolicy

pytestmark = pytest.mark.django_db(transaction=True)


class Race:
    """Separate real connections, observed PostgreSQL waits, bounded cleanup."""

    def __init__(self):
        self.threads = []
        self.pids = {}
        self.results = {}
        self.guard = threading.Lock()

    def start(self, name, call, wrapper=None):
        def worker():
            close_old_connections()
            try:
                connection.ensure_connection()
                with self.guard:
                    self.pids[name] = connection.connection.info.backend_pid
                context = connection.execute_wrapper(wrapper) if wrapper else nullcontext()
                with context:
                    result = call()
            except Exception as error:
                result = error
            finally:
                close_old_connections()
            with self.guard:
                self.results[name] = result

        thread = threading.Thread(target=worker, name=name)
        self.threads.append(thread)
        thread.start()

    def wait_lock(self, name):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            with self.guard:
                pid = self.pids.get(name)
                done = name in self.results
            if pid:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT wait_event_type FROM pg_stat_activity WHERE pid = %s", [pid]
                    )
                    row = cursor.fetchone()
                if row and row[0] == "Lock":
                    return
            assert not done, self.results.get(name)
            time.sleep(0.01)
        raise AssertionError("owned backend did not reach a real PostgreSQL lock wait")

    def finish(self):
        for thread in self.threads:
            thread.join(15)
        assert all(not thread.is_alive() for thread in self.threads)


def first_domain_lock(held, release):
    def wrapper(execute, sql, params, many, context):
        result = execute(sql, params, many, context)
        tables = (User._meta.db_table, Asset._meta.db_table)
        locking = "FOR UPDATE" in sql or "FOR NO KEY UPDATE" in sql
        if not held.is_set() and locking and any(f'"{table}"' in sql for table in tables):
            # The real SELECT has completed; locks have actually been acquired.
            held.set()
            assert release.wait(10)
        return result

    return wrapper


def batch_plan(tmp_path, users, assets, start, end, *, reverse=False):
    documents = [
        yaml.safe_load(support.write_export(tmp_path, index, start=start, end=end).read_text())
        for index in range(len(users))
    ]
    document = dict(documents[0])
    for field in ("resources", "people", "appointments"):
        document[field] = [row for item in documents for row in item[field]]
    if reverse:
        document["appointments"].reverse()
    mapping = {"format": "slaif-smartscheduling-mapping-v1", "users": {}, "assets": {}}
    for index, (user, asset) in enumerate(zip(users, assets, strict=True)):
        one = yaml.safe_load(
            support.write_mapping(tmp_path, index, user=user, asset_obj=asset).read_text()
        )
        mapping["users"].update(one["users"])
        mapping["assets"].update(one["assets"])
    export_file = tmp_path / "batch.yaml"
    mapping_file = tmp_path / "batch-mapping.yaml"
    export_file.write_text(yaml.safe_dump(document))
    mapping_file.write_text(yaml.safe_dump(mapping))
    return plan_import(
        parse_synthetic_export(
            export_file, source_name=support.LEGACY_SOURCE, timezone_name=support.SOURCE_TZ
        ),
        load_mapping(mapping_file),
    )


@pytest.mark.parametrize("first", ["import", "book"])
def test_same_principal_import_booking_serializes_without_deadlock(tmp_path, first):
    make_policy()
    asset = make_asset("same-principal")
    user = make_user("same-principal@example.invalid")
    now = timezone.now()
    start, end = now + timedelta(minutes=10), now + timedelta(hours=1)
    plan = build_plan(tmp_path, 0, user=user, asset_obj=asset, start=start, end=end)
    calls = {
        "import": lambda: importer.apply_import(plan),
        "book": lambda: services.create_reservation(
            asset=asset, requested_by_user=user, start_at=start, end_at=end, purpose="", now=now
        ),
    }
    held, release = threading.Event(), threading.Event()
    race = Race()
    second = "book" if first == "import" else "import"
    try:
        race.start(first, calls[first], first_domain_lock(held, release))
        assert held.wait(10)
        race.start(second, calls[second])
        race.wait_lock(second)
    finally:
        release.set()
        race.finish()
    if first == "import":
        assert not isinstance(race.results["import"], Exception), race.results
        assert race.results["import"].counts["imported"] == 1
        assert isinstance(race.results["book"], ReservationDomainError), race.results
        assert race.results["book"].code == RESERVATION_CONFLICT
    else:
        assert not isinstance(race.results["book"], Exception), race.results
        assert not isinstance(race.results["import"], Exception), race.results
        assert race.results["import"].counts["reservation_conflict"] == 1
    assert Reservation.objects.count() == AuditEvent.objects.count() == 1


def test_batch_later_principal_booking_cannot_invert_locks(tmp_path, monkeypatch):
    make_policy()
    users = [make_user(f"batch-{index}@example.invalid") for index in range(2)]
    assets = [make_asset(f"batch-{index}") for index in range(2)]
    now = timezone.now()
    start, end = now + timedelta(minutes=10), now + timedelta(hours=1)
    plan = batch_plan(tmp_path, users, assets, start, end)
    held, release = threading.Event(), threading.Event()
    original = importer._mark_imported

    def gate(item, reservation):
        if item.appointment.legacy_id == "appointment-0":
            held.set()
            assert release.wait(10)
        return original(item, reservation)

    monkeypatch.setattr(importer, "_mark_imported", gate)
    race = Race()
    try:
        race.start("import", lambda: importer.apply_import(plan))
        assert held.wait(10)
        race.start(
            "book",
            lambda: services.create_reservation(
                asset=assets[0],
                requested_by_user=users[1],
                start_at=start,
                end_at=end,
                purpose="",
                now=now,
            ),
        )
        race.wait_lock("book")
    finally:
        release.set()
        race.finish()
    assert not isinstance(race.results["import"], Exception), race.results
    assert race.results["import"].counts["imported"] == 2
    assert isinstance(race.results["book"], ReservationDomainError), race.results
    assert race.results["book"].code == RESERVATION_CONFLICT
    assert Reservation.objects.count() == AuditEvent.objects.count() == 2
    assert LegacyImportRecord.objects.count() == 2


@pytest.mark.parametrize("action", ["cancel", "release"])
def test_staff_lifecycle_and_import_do_not_invert_reservation_asset_locks(
    tmp_path, monkeypatch, action
):
    make_policy()
    asset = make_asset("staff-lifecycle")
    owner = make_user("import-owner@example.invalid")
    other = make_user("existing-owner@example.invalid")
    staff = make_staff("lifecycle-staff@example.invalid")
    # 050-a: cross-user lifecycle now requires the explicit capability.
    staff.user_permissions.add(
        Permission.objects.get(
            codename=(
                "cancel_others_reservations"
                if action == "cancel"
                else "release_others_reservations"
            ),
            content_type__app_label="reservations",
        )
    )
    now = timezone.now()
    start = now + timedelta(minutes=10) if action == "cancel" else now - timedelta(minutes=10)
    end = now + timedelta(hours=1)
    plan = build_plan(tmp_path, 0, user=owner, asset_obj=asset, start=start, end=end)
    existing = services.create_reservation(
        asset=asset,
        requested_by_user=other,
        start_at=start,
        end_at=end,
        purpose="",
        now=start - timedelta(minutes=1),
    ).reservation
    held, release = threading.Event(), threading.Event()
    allowed = importer._asset_allowed

    def gate(value):
        held.set()
        assert release.wait(10)
        return allowed(value)

    monkeypatch.setattr(importer, "_asset_allowed", gate)
    operation = services.cancel_reservation if action == "cancel" else services.release_reservation
    race = Race()
    try:
        race.start("import", lambda: importer.apply_import(plan))
        assert held.wait(10)
        race.start(
            "staff", lambda: operation(reservation=existing, requested_by_user=staff, now=now)
        )
        race.wait_lock("staff")
    finally:
        release.set()
        race.finish()
    assert not isinstance(race.results["import"], Exception), race.results
    assert race.results["import"].counts["reservation_conflict"] == 1
    assert not isinstance(race.results["staff"], Exception), race.results
    existing.refresh_from_db()
    assert existing.status == (
        Reservation.STATUS_CANCELLED if action == "cancel" else Reservation.STATUS_RELEASED
    )
    assert Reservation.objects.count() == 1
    assert AuditEvent.objects.count() == 2
    assert LegacyImportRecord.objects.count() == 0


def test_reversed_import_batches_are_idempotent_and_keep_report_order(tmp_path, monkeypatch):
    make_policy()
    users = [make_user(f"reverse-{index}@example.invalid") for index in range(2)]
    assets = [make_asset(f"reverse-{index}") for index in range(2)]
    now = timezone.now()
    start, end = now + timedelta(minutes=10), now + timedelta(hours=1)
    first = batch_plan(tmp_path, users, assets, start, end)
    second = batch_plan(tmp_path, users, assets, start, end, reverse=True)
    held, release = threading.Event(), threading.Event()
    mark = importer._mark_imported

    def gate(item, reservation):
        if threading.current_thread().name == "first" and not held.is_set():
            held.set()
            assert release.wait(10)
        return mark(item, reservation)

    monkeypatch.setattr(importer, "_mark_imported", gate)
    race = Race()
    try:
        race.start("first", lambda: importer.apply_import(first))
        assert held.wait(10)
        race.start("second", lambda: importer.apply_import(second))
        race.wait_lock("second")
    finally:
        release.set()
        race.finish()
    assert all(not isinstance(value, Exception) for value in race.results.values()), race.results
    assert race.results["first"].counts["imported"] == 2
    assert race.results["second"].counts["already_imported"] == 2
    assert [r.appointment.legacy_id for r in race.results["second"].plan.records] == [
        "appointment-1",
        "appointment-0",
    ]
    assert Reservation.objects.count() == AuditEvent.objects.count() == 2
    assert LegacyImportRecord.objects.count() == LegacyImportBatch.objects.count() == 2


def test_staff_joined_owner_does_not_invert_batch_principal_order(tmp_path, monkeypatch):
    make_policy()
    # Stable UUID order forces the batch to encounter the other owner before
    # the staff actor; both are legitimate mapped human principals.
    owner = User.objects.create_user(id=uuid.UUID(int=1), email="joined-owner@example.invalid")
    staff = User.objects.create_user(
        id=uuid.UUID(int=2), email="joined-staff@example.invalid", is_staff=True
    )
    # A16: both are legitimate mapped human principals for FUTURE import
    # bookings, so both carry the explicit booking capability.
    for principal in (owner, staff):
        principal.user_permissions.add(
            Permission.objects.get(codename="book_assets", content_type__app_label="reservations")
        )
    # 050-a: staff cancels the owner's reservation, so the explicit
    # cross-user cancellation capability is required.
    staff.user_permissions.add(
        Permission.objects.get(
            codename="cancel_others_reservations", content_type__app_label="reservations"
        )
    )
    assets = [make_asset("joined-first"), make_asset("joined-second")]
    other_asset = make_asset("joined-existing")
    now = timezone.now()
    start, end = now + timedelta(minutes=10), now + timedelta(hours=1)
    plan = batch_plan(tmp_path, [owner, staff], assets, start, end)
    existing = services.create_reservation(
        asset=other_asset,
        requested_by_user=owner,
        start_at=start,
        end_at=end,
        purpose="",
        now=now,
    ).reservation
    held, release = threading.Event(), threading.Event()
    principal = services._lock_principal

    def gate(value):
        locked = principal(value)
        if threading.current_thread().name == "staff":
            held.set()
            assert release.wait(10)
        return locked

    monkeypatch.setattr(services, "_lock_principal", gate)
    race = Race()
    try:
        race.start(
            "staff",
            lambda: services.cancel_reservation(
                reservation=existing, requested_by_user=staff, now=now
            ),
        )
        assert held.wait(10)
        race.start("import", lambda: importer.apply_import(plan))
        race.wait_lock("import")
    finally:
        release.set()
        race.finish()
    assert all(not isinstance(value, Exception) for value in race.results.values()), race.results
    assert race.results["import"].counts["imported"] == 2
    existing.refresh_from_db()
    assert existing.status == Reservation.STATUS_CANCELLED
    assert Reservation.objects.count() == 3
    assert AuditEvent.objects.count() == 4
    assert LegacyImportRecord.objects.count() == 2


def test_principal_asset_mutexes_allow_fk_references_but_block_data_writes():
    asset = make_asset("mutex-compatibility")
    user = make_user("mutex@example.invalid")
    held, release = threading.Event(), threading.Event()
    race = Race()

    def holder():
        with transaction.atomic():
            services._lock_principal(user)
            services._lock_asset(asset)
            held.set()
            assert release.wait(10)

    def reference():
        with transaction.atomic(), connection.cursor() as cursor:
            for model, identifier in ((User, user.pk), (Asset, asset.pk)):
                table = connection.ops.quote_name(model._meta.db_table)
                cursor.execute(f"SELECT id FROM {table} WHERE id = %s FOR KEY SHARE", [identifier])

    def writer(model, identifier, field):
        with transaction.atomic(), connection.cursor() as cursor:
            table = connection.ops.quote_name(model._meta.db_table)
            column = connection.ops.quote_name(field)
            cursor.execute(
                f"UPDATE {table} SET {column} = %s WHERE id = %s", ["Updated", identifier]
            )

    try:
        race.start("holder", holder)
        assert held.wait(10)
        race.start("reference", reference)
        deadline = time.monotonic() + 2
        while "reference" not in race.results and time.monotonic() < deadline:
            time.sleep(0.01)
        assert "reference" in race.results and not isinstance(race.results["reference"], Exception)
        race.start("user-writer", lambda: writer(User, user.pk, "display_name"))
        race.start("asset-writer", lambda: writer(Asset, asset.pk, "name"))
        race.wait_lock("user-writer")
        race.wait_lock("asset-writer")
        user.refresh_from_db()
        asset.refresh_from_db()
        assert user.display_name != "Updated" and asset.name != "Updated"
    finally:
        release.set()
        race.finish()
    assert all(not isinstance(value, Exception) for value in race.results.values()), race.results
    user.refresh_from_db()
    asset.refresh_from_db()
    assert user.display_name == asset.name == "Updated"


def test_policy_target_fk_does_not_deadlock_booking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    make_policy()
    policy = ReservationPolicy.objects.get(asset__isnull=True)
    asset = Asset.objects.create(
        slug="policy-reference",
        name="Synthetic machine",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=True,
    )
    owner = make_user("policy-owner@example.invalid")
    staff = make_staff("policy-staff@example.invalid")
    # 050-a: policy updates require the explicit policy-management capability.
    staff.user_permissions.add(
        Permission.objects.get(
            codename="manage_booking_policies", content_type__app_label="reservations"
        )
    )
    now = timezone.now()
    start = now + timedelta(minutes=10)
    end = start + timedelta(hours=1)
    asset_held = threading.Event()
    policy_held = threading.Event()
    outcomes = {}
    guard = threading.Lock()
    validate = services._validate_asset
    get = QuerySet.get

    def gate_asset(value):
        if threading.current_thread().name == "booking":
            asset_held.set()
            assert policy_held.wait(10)
        return validate(value)

    def gate_policy(query, *args, **kwargs):
        value = get(query, *args, **kwargs)
        if query.model is ReservationPolicy and threading.current_thread().name == "policy":
            policy_held.set()
            assert asset_held.wait(10)
        return value

    monkeypatch.setattr(services, "_validate_asset", gate_asset)
    monkeypatch.setattr(QuerySet, "get", gate_policy)

    def run(label, call):
        close_old_connections()
        try:
            result = call()
        except Exception as error:
            result = error
        finally:
            close_old_connections()
        with guard:
            outcomes[label] = result

    booking = threading.Thread(
        target=run,
        args=(
            "booking",
            lambda: services.create_reservation(
                asset=asset,
                requested_by_user=owner,
                start_at=start,
                end_at=end,
                purpose="",
                now=now,
            ),
        ),
        name="booking",
    )
    policy_update = threading.Thread(
        target=run,
        args=(
            "policy",
            lambda: services.update_policy(policy=policy, actor_user=staff, asset=asset),
        ),
        name="policy",
    )
    booking.start()
    assert asset_held.wait(10)
    policy_update.start()
    booking.join(15)
    policy_update.join(15)
    assert not booking.is_alive() and not policy_update.is_alive()
    assert not isinstance(outcomes["policy"], Exception), outcomes["policy"]
    # A concurrent scope change may invalidate the previously observed global
    # fallback. A stable denial is safe; an OperationalError/deadlock is not.
    if isinstance(outcomes["booking"], Exception):
        assert isinstance(outcomes["booking"], ReservationDomainError), outcomes["booking"]
        assert outcomes["booking"].code == POLICY_NOT_CONFIGURED
    policy.refresh_from_db()
    assert policy.asset_id == asset.id
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_POLICY_UPDATED).count() == 1
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_RESERVATION_CREATED).count() == (
        Reservation.objects.count()
    )
