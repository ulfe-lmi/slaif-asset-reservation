from __future__ import annotations

import threading
import time
from collections import Counter
from collections.abc import Callable
from datetime import datetime, timedelta

import pytest
from django.contrib.auth.models import Permission
from django.db import close_old_connections
from django.utils import timezone

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.reservations import services
from slaif_reservation.reservations.exceptions import (
    BLACKOUT_CONFLICT,
    MAX_UPCOMING_EXCEEDED,
    RESERVATION_CONFLICT,
    ReservationDomainError,
)
from slaif_reservation.reservations.models import (
    MaintenanceBlackout,
    Reservation,
    ReservationPolicy,
)


def make_user(email: str) -> User:
    created = User.objects.create_user(email=email, password="not-a-secret")
    # A16: positive booking fixtures explicitly carry the baseline
    # reservations.book_assets capability (real Permission row).
    created.user_permissions.add(
        Permission.objects.get(codename="book_assets", content_type__app_label="reservations")
    )
    return created


def make_asset(slug: str) -> Asset:
    return Asset.objects.create(
        slug=slug,
        name=slug,
        kind=Asset.KIND_GPU,
        active=True,
        reservable=True,
    )


def make_policy(**overrides: object) -> None:
    values = {
        "name": "global",
        "min_duration_minutes": 1,
        "max_duration_minutes": 240,
        "booking_horizon_days": 1,
        "max_upcoming_per_principal": 5,
        "max_concurrent_per_principal": 5,
    }
    values.update(overrides)
    return ReservationPolicy.objects.create(**values)


def run_parallel(calls) -> list[str]:
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


@pytest.mark.django_db(transaction=True)
def test_two_simultaneous_overlapping_creates_one_conflicts() -> None:
    make_policy()
    asset = make_asset("gpu-a")
    first_user = make_user("a@example.com")
    second_user = make_user("b@example.com")
    now = timezone.now()
    start = now + timedelta(minutes=10)

    outcomes = run_parallel(
        [
            lambda: services.create_reservation(
                asset=asset,
                requested_by_user=first_user,
                start_at=start,
                end_at=start + timedelta(hours=1),
                purpose="",
                now=now,
            ),
            lambda: services.create_reservation(
                asset=asset,
                requested_by_user=second_user,
                start_at=start + timedelta(minutes=15),
                end_at=start + timedelta(hours=1),
                purpose="",
                now=now,
            ),
        ]
    )

    assert Counter(outcomes) == Counter([RESERVATION_CONFLICT, "committed"])
    assert Reservation.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_simultaneous_adjacent_creates_both_commit() -> None:
    make_policy()
    asset = make_asset("gpu-a")
    first_user = make_user("a@example.com")
    second_user = make_user("b@example.com")
    now = timezone.now()
    start = now + timedelta(minutes=10)

    outcomes = run_parallel(
        [
            lambda: services.create_reservation(
                asset=asset,
                requested_by_user=first_user,
                start_at=start,
                end_at=start + timedelta(hours=1),
                purpose="",
                now=now,
            ),
            lambda: services.create_reservation(
                asset=asset,
                requested_by_user=second_user,
                start_at=start + timedelta(hours=1),
                end_at=start + timedelta(hours=2),
                purpose="",
                now=now,
            ),
        ]
    )

    assert Counter(outcomes) == Counter(["committed", "committed"])
    assert Reservation.objects.count() == 2


@pytest.mark.django_db(transaction=True)
def test_simultaneous_non_overlapping_creates_serialize_principal_upcoming_limit() -> None:
    make_policy(max_upcoming_per_principal=1)
    first_asset = make_asset("gpu-a")
    second_asset = make_asset("gpu-b")
    principal = make_user("a@example.com")
    now = timezone.now()
    start = now + timedelta(minutes=10)

    outcomes = run_parallel(
        [
            lambda: services.create_reservation(
                asset=first_asset,
                requested_by_user=principal,
                start_at=start,
                end_at=start + timedelta(minutes=30),
                purpose="",
                now=now,
            ),
            lambda: services.create_reservation(
                asset=second_asset,
                requested_by_user=principal,
                start_at=start + timedelta(hours=1),
                end_at=start + timedelta(hours=2),
                purpose="",
                now=now,
            ),
        ]
    )

    assert Counter(outcomes) == Counter([MAX_UPCOMING_EXCEEDED, "committed"])
    assert Reservation.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_policy_update_waits_for_reservation_operation_policy_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reservation_policy = make_policy(max_upcoming_per_principal=5, max_concurrent_per_principal=5)
    gpu = make_asset("gpu-a")
    principal = make_user("a@example.com")
    admin = User.objects.create_user(
        email="staff@example.com",
        password="not-a-secret",
        is_staff=True,
    )
    now = timezone.now()
    start = now + timedelta(minutes=10)
    policy_locked = threading.Event()
    release_reservation = threading.Event()
    outcomes: list[str] = []
    outcomes_lock = threading.Lock()
    original_overlap = services._raise_if_asset_overlap

    def pause_after_policy_lock(*args: object, **kwargs: object) -> None:
        policy_locked.set()
        assert release_reservation.wait(timeout=10)
        original_overlap(*args, **kwargs)

    monkeypatch.setattr(services, "_raise_if_asset_overlap", pause_after_policy_lock)

    def create_call() -> None:
        close_old_connections()
        try:
            services.create_reservation(
                asset=gpu,
                requested_by_user=principal,
                start_at=start,
                end_at=start + timedelta(minutes=30),
                purpose="",
                now=now,
            )
            outcome = "reservation_committed"
        except ReservationDomainError as exc:
            outcome = exc.code
        finally:
            close_old_connections()
        with outcomes_lock:
            outcomes.append(outcome)

    def update_call() -> None:
        close_old_connections()
        try:
            services.update_policy(
                policy=reservation_policy,
                actor_user=admin,
                max_duration_minutes=300,
            )
            outcome = "policy_updated"
        except ReservationDomainError as exc:
            outcome = exc.code
        finally:
            close_old_connections()
        with outcomes_lock:
            outcomes.append(outcome)

    create_thread = threading.Thread(target=create_call)
    create_thread.start()
    assert policy_locked.wait(timeout=10)

    update_thread = threading.Thread(target=update_call)
    update_thread.start()
    time.sleep(0.25)
    assert update_thread.is_alive()
    reservation_policy.refresh_from_db()
    assert reservation_policy.max_duration_minutes == 240

    release_reservation.set()
    create_thread.join(timeout=10)
    update_thread.join(timeout=10)

    assert not create_thread.is_alive()
    assert not update_thread.is_alive()
    assert Counter(outcomes) == Counter(["reservation_committed", "policy_updated"])
    reservation_policy.refresh_from_db()
    assert reservation_policy.max_duration_minutes == 300


def make_staff(email: str) -> User:
    return User.objects.create_user(
        email=email,
        password="not-a-secret",
        is_staff=True,
    )


def _overlapping_reservations(asset: Asset, start: object, end: object) -> int:
    return Reservation.objects.filter(
        asset=asset,
        status__in=[Reservation.STATUS_CONFIRMED, Reservation.STATUS_RELEASED],
        start_at__lt=end,
        effective_end_at__gt=start,
    ).count()


def _active_blackouts(asset: Asset, start: object, end: object) -> int:
    return MaintenanceBlackout.objects.filter(
        asset=asset,
        active=True,
        start_at__lt=end,
        end_at__gt=start,
    ).count()


def _reservation_call(
    asset: Asset,
    booker: User,
    start: datetime,
    end: datetime,
    now: datetime,
) -> Callable[[], None]:
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


def _blackout_call(
    asset: Asset,
    staff: User,
    start: datetime,
    end: datetime,
) -> Callable[[], None]:
    def call() -> None:
        services.create_blackout(
            asset=asset,
            actor_user=staff,
            reason="maintenance",
            start_at=start,
            end_at=end + timedelta(hours=1),
        )

    return call


def _deactivate_call(blackout: MaintenanceBlackout, staff: User) -> Callable[[], None]:
    def call() -> None:
        services.deactivate_blackout(blackout=blackout, actor_user=staff)

    return call


@pytest.mark.django_db(transaction=True)
def test_reservation_vs_blackout_race_exactly_one_commits_across_repeats() -> None:
    make_policy()
    observed: list[str] = []
    for iteration in range(5):
        asset = make_asset(f"gpu-a{iteration}")
        booker = make_user(f"booker{iteration}@example.com")
        staff = make_staff(f"staff{iteration}@example.com")
        now = timezone.now()
        start = now + timedelta(minutes=10)
        end = start + timedelta(hours=1)

        outcomes = run_parallel(
            [
                _reservation_call(asset=asset, booker=booker, start=start, end=end, now=now),
                _blackout_call(asset=asset, staff=staff, start=start, end=end),
            ]
        )

        assert Counter(outcomes) == Counter([BLACKOUT_CONFLICT, "committed"])
        reservation_count = _overlapping_reservations(asset, start, end)
        blackout_count = _active_blackouts(asset, start, end)
        assert (reservation_count, blackout_count) in [(1, 0), (0, 1)]
        observed.append("reservation_wins" if reservation_count == 1 else "blackout_wins")
    print(f"020-a test 1 observed orderings: {observed}")


@pytest.mark.django_db(transaction=True)
def test_reservation_wins_blackout_blocked_on_asset_lock_then_conflicts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    make_policy()
    asset = make_asset("gpu-a")
    booker = make_user("booker@example.com")
    staff = make_staff("staff@example.com")
    now = timezone.now()
    start = now + timedelta(minutes=10)
    end = start + timedelta(hours=1)
    reservation_holds_lock = threading.Event()
    release_reservation = threading.Event()
    outcomes: list[str] = []
    outcomes_lock = threading.Lock()
    original_blackout_check = services._raise_if_blackout_overlap

    def pause_after_reservation_lock(*args: object, **kwargs: object) -> None:
        reservation_holds_lock.set()
        assert release_reservation.wait(timeout=10)
        original_blackout_check(*args, **kwargs)

    monkeypatch.setattr(services, "_raise_if_blackout_overlap", pause_after_reservation_lock)

    def reservation_call() -> None:
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
            outcome = "reservation_committed"
        except ReservationDomainError as exc:
            outcome = exc.code
        finally:
            close_old_connections()
        with outcomes_lock:
            outcomes.append(outcome)

    def blackout_call() -> None:
        close_old_connections()
        try:
            services.create_blackout(
                asset=asset,
                actor_user=staff,
                reason="maintenance",
                start_at=start,
                end_at=end + timedelta(hours=1),
            )
            outcome = "blackout_committed"
        except ReservationDomainError as exc:
            outcome = exc.code
        finally:
            close_old_connections()
        with outcomes_lock:
            outcomes.append(outcome)

    reservation_thread = threading.Thread(target=reservation_call)
    reservation_thread.start()
    assert reservation_holds_lock.wait(timeout=10)

    blackout_thread = threading.Thread(target=blackout_call)
    blackout_thread.start()
    time.sleep(0.25)
    assert blackout_thread.is_alive()

    release_reservation.set()
    reservation_thread.join(timeout=10)
    blackout_thread.join(timeout=10)
    assert not reservation_thread.is_alive()
    assert not blackout_thread.is_alive()
    assert Counter(outcomes) == Counter(["reservation_committed", BLACKOUT_CONFLICT])

    assert _overlapping_reservations(asset, start, end) == 1
    assert _active_blackouts(asset, start, end) == 0


@pytest.mark.django_db(transaction=True)
def test_blackout_wins_reservation_blocked_on_asset_lock_then_conflicts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    make_policy()
    asset = make_asset("gpu-a")
    booker = make_user("booker@example.com")
    staff = make_staff("staff@example.com")
    now = timezone.now()
    start = now + timedelta(minutes=10)
    end = start + timedelta(hours=1)
    blackout_holds_lock = threading.Event()
    release_blackout = threading.Event()
    outcomes: list[str] = []
    outcomes_lock = threading.Lock()
    original_overlaps = services.overlapping_blocking_reservations

    def pause_after_blackout_lock(*args: object, **kwargs: object) -> list:
        blackout_holds_lock.set()
        assert release_blackout.wait(timeout=10)
        return original_overlaps(*args, **kwargs)

    monkeypatch.setattr(services, "overlapping_blocking_reservations", pause_after_blackout_lock)

    def reservation_call() -> None:
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
            outcome = "reservation_committed"
        except ReservationDomainError as exc:
            outcome = exc.code
        finally:
            close_old_connections()
        with outcomes_lock:
            outcomes.append(outcome)

    def blackout_call() -> None:
        close_old_connections()
        try:
            services.create_blackout(
                asset=asset,
                actor_user=staff,
                reason="maintenance",
                start_at=start,
                end_at=end + timedelta(hours=1),
            )
            outcome = "blackout_committed"
        except ReservationDomainError as exc:
            outcome = exc.code
        finally:
            close_old_connections()
        with outcomes_lock:
            outcomes.append(outcome)

    blackout_thread = threading.Thread(target=blackout_call)
    blackout_thread.start()
    assert blackout_holds_lock.wait(timeout=10)

    reservation_thread = threading.Thread(target=reservation_call)
    reservation_thread.start()
    time.sleep(0.25)
    assert reservation_thread.is_alive()

    release_blackout.set()
    blackout_thread.join(timeout=10)
    reservation_thread.join(timeout=10)
    assert not blackout_thread.is_alive()
    assert not reservation_thread.is_alive()
    assert Counter(outcomes) == Counter(["blackout_committed", BLACKOUT_CONFLICT])

    assert _overlapping_reservations(asset, start, end) == 0
    assert _active_blackouts(asset, start, end) == 1


@pytest.mark.django_db(transaction=True)
def test_deactivation_vs_booking_race_never_books_over_active_blackout() -> None:
    make_policy()
    observed: list[str] = []
    for iteration in range(5):
        asset = make_asset(f"gpu-b{iteration}")
        booker = make_user(f"booker{iteration}@example.com")
        staff = make_staff(f"staff{iteration}@example.com")
        now = timezone.now()
        start = now + timedelta(minutes=10)
        end = start + timedelta(hours=1)
        blackout = MaintenanceBlackout.objects.create(
            asset=asset,
            created_by=staff,
            reason="maintenance",
            start_at=start,
            end_at=end + timedelta(hours=1),
            active=True,
        )

        outcomes = run_parallel(
            [
                _reservation_call(asset=asset, booker=booker, start=start, end=end, now=now),
                _deactivate_call(blackout=blackout, staff=staff),
            ]
        )

        assert Counter(outcomes) in [
            Counter([BLACKOUT_CONFLICT, "committed"]),
            Counter(["committed", "committed"]),
        ]
        blackout.refresh_from_db()
        assert blackout.active is False
        assert blackout.deactivated_at is not None
        assert blackout.deactivated_by_id == staff.pk
        reservation_count = _overlapping_reservations(asset, start, end)
        blackout_count = _active_blackouts(asset, start, end)
        assert not (reservation_count > 0 and blackout_count > 0)
        observed.append("reservation_committed" if reservation_count else "reservation_conflict")
    print(f"020-a test 4 observed orderings: {observed}")


@pytest.mark.django_db(transaction=True)
def test_staff_acknowledged_overlap_committed_alongside_reservation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    make_policy()
    asset = make_asset("gpu-a")
    booker = make_user("booker@example.com")
    staff = make_staff("staff@example.com")
    now = timezone.now()
    start = now + timedelta(minutes=10)
    end = start + timedelta(hours=1)
    reservation_holds_lock = threading.Event()
    release_reservation = threading.Event()
    outcomes: list[str] = []
    outcomes_lock = threading.Lock()
    committed_blackouts: list[MaintenanceBlackout] = []
    original_blackout_check = services._raise_if_blackout_overlap

    def pause_after_reservation_lock(*args: object, **kwargs: object) -> None:
        reservation_holds_lock.set()
        assert release_reservation.wait(timeout=10)
        original_blackout_check(*args, **kwargs)

    monkeypatch.setattr(services, "_raise_if_blackout_overlap", pause_after_reservation_lock)

    def reservation_call() -> None:
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
            outcome = "reservation_committed"
        except ReservationDomainError as exc:
            outcome = exc.code
        finally:
            close_old_connections()
        with outcomes_lock:
            outcomes.append(outcome)

    def blackout_call() -> None:
        close_old_connections()
        try:
            result = services.create_blackout(
                asset=asset,
                actor_user=staff,
                reason="maintenance",
                start_at=start,
                end_at=end + timedelta(hours=1),
                confirmed_overlap=True,
            )
            with outcomes_lock:
                committed_blackouts.append(result.blackout)
            outcome = "blackout_committed"
        except ReservationDomainError as exc:
            outcome = exc.code
        finally:
            close_old_connections()
        with outcomes_lock:
            outcomes.append(outcome)

    reservation_thread = threading.Thread(target=reservation_call)
    reservation_thread.start()
    assert reservation_holds_lock.wait(timeout=10)

    blackout_thread = threading.Thread(target=blackout_call)
    blackout_thread.start()
    time.sleep(0.25)
    assert blackout_thread.is_alive()

    release_reservation.set()
    reservation_thread.join(timeout=10)
    blackout_thread.join(timeout=10)
    assert not reservation_thread.is_alive()
    assert not blackout_thread.is_alive()
    assert Counter(outcomes) == Counter(["reservation_committed", "blackout_committed"])

    assert _overlapping_reservations(asset, start, end) == 1
    assert len(committed_blackouts) == 1
    blackout = committed_blackouts[0]
    blackout.refresh_from_db()
    assert blackout.active is True
    assert _active_blackouts(asset, start, end) == 1
    event = AuditEvent.objects.get(
        action=AuditEvent.ACTION_BLACKOUT_CREATED,
        target_type="maintenance_blackout",
        target_id=blackout.id,
    )
    assert event.metadata.get("overlapping_reservations", 0) >= 1
