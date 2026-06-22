from __future__ import annotations

import threading
from collections import Counter
from datetime import timedelta

import pytest
from django.db import close_old_connections
from django.utils import timezone

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset
from slaif_reservation.reservations import services
from slaif_reservation.reservations.exceptions import (
    MAX_UPCOMING_EXCEEDED,
    RESERVATION_CONFLICT,
    ReservationDomainError,
)
from slaif_reservation.reservations.models import Reservation, ReservationPolicy


def make_user(email: str) -> User:
    return User.objects.create_user(email=email, password="not-a-secret")


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
    ReservationPolicy.objects.create(**values)


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
