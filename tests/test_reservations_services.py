from __future__ import annotations

from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.utils import timezone

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.reservations import services
from slaif_reservation.reservations.exceptions import (
    ASSET_INACTIVE,
    ASSET_NOT_RESERVABLE,
    BOOKING_HORIZON_VIOLATION,
    CANCELLATION_CUTOFF,
    DURATION_TOO_LONG,
    DURATION_TOO_SHORT,
    LEAD_TIME_VIOLATION,
    MAX_CONCURRENT_EXCEEDED,
    MAX_UPCOMING_EXCEEDED,
    POLICY_AMBIGUOUS,
    POLICY_NOT_CONFIGURED,
    PRINCIPAL_INACTIVE,
    PURPOSE_REQUIRED,
    RESERVATION_CONFLICT,
    RESERVATION_IN_PAST,
    RESERVATION_NOT_CANCELLABLE,
    RESERVATION_NOT_OWNED,
    RESERVATION_NOT_RELEASABLE,
    ReservationDomainError,
)
from slaif_reservation.reservations.models import Reservation, ReservationPolicy


def user(email: str = "user@example.com", **overrides: object) -> User:
    return User.objects.create_user(email=email, password="not-a-secret", **overrides)


def asset(slug: str = "asset-a", **overrides: object) -> Asset:
    values = {
        "slug": slug,
        "name": slug.replace("-", " ").title(),
        "kind": Asset.KIND_GPU,
        "active": True,
        "reservable": True,
    }
    values.update(overrides)
    return Asset.objects.create(**values)


def policy(**overrides: object) -> ReservationPolicy:
    values = {
        "name": "Default policy",
        "min_duration_minutes": 15,
        "max_duration_minutes": 240,
        "booking_horizon_days": 30,
        "min_lead_minutes": 0,
        "cancellation_cutoff_minutes": 0,
        "max_upcoming_per_principal": 5,
        "max_concurrent_per_principal": 2,
        "purpose_required": False,
    }
    values.update(overrides)
    return ReservationPolicy.objects.create(**values)


def assert_domain_error(code: str):
    return pytest.raises(ReservationDomainError, match=".", check=lambda exc: exc.code == code)


@pytest.mark.django_db
def test_policy_resolution_order_asset_parent_global() -> None:
    machine = asset("machine-a", kind=Asset.KIND_MACHINE, reservable=False)
    child = asset("machine-a-gpu-0", parent=machine)
    global_policy = policy(name="global")
    parent_policy = policy(name="parent", asset=machine)
    asset_policy = policy(name="asset", asset=child)

    assert services.resolve_effective_policy(child) == asset_policy
    asset_policy.active = False
    asset_policy.save()
    assert services.resolve_effective_policy(child) == parent_policy
    parent_policy.active = False
    parent_policy.save()
    assert services.resolve_effective_policy(child) == global_policy


@pytest.mark.django_db
def test_missing_policy_fails_closed() -> None:
    gpu = asset()

    with assert_domain_error(POLICY_NOT_CONFIGURED):
        services.resolve_effective_policy(gpu)


@pytest.mark.django_db
def test_equal_priority_policy_ambiguity_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    gpu = asset()
    first = policy(name="ambiguous-a")
    second = ReservationPolicy.objects.create(
        name="ambiguous-b",
        active=False,
        min_duration_minutes=1,
        max_duration_minutes=60,
        booking_horizon_days=1,
        max_upcoming_per_principal=1,
        max_concurrent_per_principal=1,
    )
    monkeypatch.setattr(services, "_active_policies_for", lambda _query: [first, second])

    with assert_domain_error(POLICY_AMBIGUOUS):
        services.resolve_effective_policy(gpu)


@pytest.mark.django_db
def test_create_reservation_success_writes_matching_audit_event() -> None:
    principal = user()
    gpu = asset()
    policy(purpose_required=True)
    now = timezone.now()
    start = now + timedelta(hours=1)

    result = services.create_reservation(
        asset=gpu,
        requested_by_user=principal,
        start_at=start,
        end_at=start + timedelta(minutes=30),
        purpose="Model training",
        now=now,
    )

    assert result.reservation.status == Reservation.STATUS_CONFIRMED
    event = AuditEvent.objects.get(action=AuditEvent.ACTION_RESERVATION_CREATED)
    assert event.target_id == result.reservation.id
    assert event.correlation_id == result.correlation_id
    assert "purpose" not in event.metadata


@pytest.mark.django_db
@pytest.mark.parametrize(
    "policy_overrides,start_offset,end_offset,purpose,code",
    [
        ({}, timedelta(minutes=-1), timedelta(minutes=30), "x", RESERVATION_IN_PAST),
        (
            {"min_lead_minutes": 60},
            timedelta(minutes=59),
            timedelta(minutes=90),
            "x",
            LEAD_TIME_VIOLATION,
        ),
        (
            {"booking_horizon_days": 1},
            timedelta(days=1, seconds=1),
            timedelta(days=1, hours=1),
            "x",
            BOOKING_HORIZON_VIOLATION,
        ),
        (
            {"min_duration_minutes": 30},
            timedelta(hours=1),
            timedelta(hours=1, minutes=29),
            "x",
            DURATION_TOO_SHORT,
        ),
        (
            {"max_duration_minutes": 30},
            timedelta(hours=1),
            timedelta(hours=1, minutes=31),
            "x",
            DURATION_TOO_LONG,
        ),
        ({"purpose_required": True}, timedelta(hours=1), timedelta(hours=2), " ", PURPOSE_REQUIRED),
    ],
)
def test_create_reservation_policy_boundaries_fail_closed(
    policy_overrides: dict[str, object],
    start_offset: timedelta,
    end_offset: timedelta,
    purpose: str,
    code: str,
) -> None:
    principal = user()
    gpu = asset()
    policy(**policy_overrides)
    now = timezone.now()

    with assert_domain_error(code):
        services.create_reservation(
            asset=gpu,
            requested_by_user=principal,
            start_at=now + start_offset,
            end_at=now + end_offset,
            purpose=purpose,
            now=now,
        )
    assert AuditEvent.objects.count() == 0


@pytest.mark.django_db
def test_exact_policy_boundaries_are_inclusive() -> None:
    principal = user()
    gpu = asset()
    policy(
        min_duration_minutes=30,
        max_duration_minutes=30,
        min_lead_minutes=15,
        booking_horizon_days=1,
        max_upcoming_per_principal=2,
    )
    now = timezone.now()
    start = now + timedelta(minutes=15)

    services.create_reservation(
        asset=gpu,
        requested_by_user=principal,
        start_at=start,
        end_at=start + timedelta(minutes=30),
        purpose="",
        now=now,
    )
    services.create_reservation(
        asset=gpu,
        requested_by_user=principal,
        start_at=now + timedelta(days=1),
        end_at=now + timedelta(days=1, minutes=30),
        purpose="",
        now=now,
    )

    assert Reservation.objects.count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize(
    "principal_overrides,asset_overrides,code",
    [
        ({"is_active": False}, {}, PRINCIPAL_INACTIVE),
        ({}, {"active": False, "reservable": False}, ASSET_INACTIVE),
        ({}, {"reservable": False}, ASSET_NOT_RESERVABLE),
    ],
)
def test_principal_and_asset_rejections(
    principal_overrides: dict[str, object],
    asset_overrides: dict[str, object],
    code: str,
) -> None:
    principal = user(**principal_overrides)
    gpu = asset(**asset_overrides)
    policy()
    now = timezone.now()
    start = now + timedelta(hours=1)

    with assert_domain_error(code):
        services.create_reservation(
            asset=gpu,
            requested_by_user=principal,
            start_at=start,
            end_at=start + timedelta(minutes=30),
            purpose="",
            now=now,
        )


@pytest.mark.django_db
def test_conflict_produces_stable_code_and_no_failed_audit() -> None:
    principal = user()
    gpu = asset()
    policy(max_upcoming_per_principal=5, max_concurrent_per_principal=5)
    now = timezone.now()
    start = now + timedelta(hours=1)
    services.create_reservation(
        asset=gpu,
        requested_by_user=principal,
        start_at=start,
        end_at=start + timedelta(hours=1),
        purpose="",
        now=now,
    )
    audit_count = AuditEvent.objects.count()

    with assert_domain_error(RESERVATION_CONFLICT):
        services.create_reservation(
            asset=gpu,
            requested_by_user=principal,
            start_at=start + timedelta(minutes=15),
            end_at=start + timedelta(minutes=45),
            purpose="",
            now=now,
        )

    assert AuditEvent.objects.count() == audit_count


@pytest.mark.django_db
def test_upcoming_limit() -> None:
    principal = user()
    gpu = asset()
    policy(max_upcoming_per_principal=1, max_concurrent_per_principal=1)
    now = timezone.now()
    start = now + timedelta(hours=1)
    services.create_reservation(
        asset=gpu,
        requested_by_user=principal,
        start_at=start,
        end_at=start + timedelta(minutes=30),
        purpose="",
        now=now,
    )

    with assert_domain_error(MAX_UPCOMING_EXCEEDED):
        services.create_reservation(
            asset=gpu,
            requested_by_user=principal,
            start_at=start + timedelta(hours=2),
            end_at=start + timedelta(hours=3),
            purpose="",
            now=now,
        )


@pytest.mark.django_db
def test_concurrent_limit() -> None:
    principal = user()
    gpu = asset()
    policy(max_upcoming_per_principal=5, max_concurrent_per_principal=1)
    now = timezone.now()
    start = now + timedelta(hours=1)
    services.create_reservation(
        asset=gpu,
        requested_by_user=principal,
        start_at=start,
        end_at=start + timedelta(hours=2),
        purpose="",
        now=now,
    )
    with assert_domain_error(MAX_CONCURRENT_EXCEEDED):
        services.create_reservation(
            asset=asset("asset-b"),
            requested_by_user=principal,
            start_at=start + timedelta(minutes=30),
            end_at=start + timedelta(hours=1),
            purpose="",
            now=now,
        )


@pytest.mark.django_db
def test_cancellation_authorization_cutoff_transition_and_audit() -> None:
    owner = user()
    other = user("other@example.com")
    staff = user("staff@example.com", is_staff=True)
    gpu = asset()
    policy(cancellation_cutoff_minutes=30, max_upcoming_per_principal=5)
    now = timezone.now()
    start = now + timedelta(hours=2)
    reservation = services.create_reservation(
        asset=gpu,
        requested_by_user=owner,
        start_at=start,
        end_at=start + timedelta(hours=1),
        purpose="",
        now=now,
    ).reservation

    with assert_domain_error(RESERVATION_NOT_OWNED):
        services.cancel_reservation(reservation=reservation, requested_by_user=other, now=now)
    with assert_domain_error(CANCELLATION_CUTOFF):
        services.cancel_reservation(
            reservation=reservation,
            requested_by_user=owner,
            now=start - timedelta(minutes=29, seconds=59),
        )

    result = services.cancel_reservation(
        reservation=reservation,
        requested_by_user=staff,
        reason="operator correction",
        now=start - timedelta(minutes=30),
    )

    assert result.reservation.status == Reservation.STATUS_CANCELLED
    assert result.reservation.cancelled_by == staff
    event = AuditEvent.objects.get(action=AuditEvent.ACTION_RESERVATION_CANCELLED)
    assert "cancellation_reason" not in event.metadata


@pytest.mark.django_db
def test_cancellation_requires_future_confirmed_reservation() -> None:
    owner = user()
    gpu = asset()
    policy()
    now = timezone.now()
    start = now + timedelta(hours=1)
    reservation = services.create_reservation(
        asset=gpu,
        requested_by_user=owner,
        start_at=start,
        end_at=start + timedelta(hours=1),
        purpose="",
        now=now,
    ).reservation

    with assert_domain_error(RESERVATION_NOT_CANCELLABLE):
        services.cancel_reservation(reservation=reservation, requested_by_user=owner, now=start)


@pytest.mark.django_db
def test_release_authorization_active_requirement_transition_and_audit() -> None:
    owner = user()
    other = user("other@example.com")
    gpu = asset()
    policy()
    now = timezone.now()
    start = now + timedelta(minutes=10)
    reservation = services.create_reservation(
        asset=gpu,
        requested_by_user=owner,
        start_at=start,
        end_at=start + timedelta(hours=1),
        purpose="",
        now=now,
    ).reservation

    with assert_domain_error(RESERVATION_NOT_OWNED):
        services.release_reservation(
            reservation=reservation, requested_by_user=other, now=start + timedelta(minutes=1)
        )
    with assert_domain_error(RESERVATION_NOT_RELEASABLE):
        services.release_reservation(reservation=reservation, requested_by_user=owner, now=start)

    result = services.release_reservation(
        reservation=reservation,
        requested_by_user=owner,
        now=start + timedelta(minutes=1),
    )

    assert result.reservation.status == Reservation.STATUS_RELEASED
    assert result.reservation.released_at == start + timedelta(minutes=1)
    event = AuditEvent.objects.get(action=AuditEvent.ACTION_RESERVATION_RELEASED)
    assert event.target_id == result.reservation.id


@pytest.mark.django_db
def test_released_future_remainder_becomes_reservable_after_commit() -> None:
    owner = user()
    gpu = asset()
    policy(max_upcoming_per_principal=5, max_concurrent_per_principal=5)
    now = timezone.now()
    start = now + timedelta(minutes=10)
    reservation = services.create_reservation(
        asset=gpu,
        requested_by_user=owner,
        start_at=start,
        end_at=start + timedelta(hours=2),
        purpose="",
        now=now,
    ).reservation
    release_at = start + timedelta(minutes=30)
    services.release_reservation(reservation=reservation, requested_by_user=owner, now=release_at)

    services.create_reservation(
        asset=gpu,
        requested_by_user=owner,
        start_at=release_at,
        end_at=start + timedelta(hours=2),
        purpose="",
        now=now,
    )

    assert Reservation.objects.count() == 2


@pytest.mark.django_db
def test_audit_failure_rolls_back_reservation(monkeypatch: pytest.MonkeyPatch) -> None:
    principal = user()
    gpu = asset()
    policy()
    now = timezone.now()
    start = now + timedelta(hours=1)

    def fail_audit(*args: object, **kwargs: object) -> None:
        raise IntegrityError("audit failed")

    monkeypatch.setattr(services, "append_audit_event", fail_audit)

    with pytest.raises(IntegrityError, match="audit failed"):
        services.create_reservation(
            asset=gpu,
            requested_by_user=principal,
            start_at=start,
            end_at=start + timedelta(hours=1),
            purpose="",
            now=now,
        )

    assert Reservation.objects.count() == 0


@pytest.mark.django_db
def test_policy_services_write_audit() -> None:
    admin = user(is_staff=True)
    result = services.create_policy(
        actor_user=admin,
        name="Global",
        min_duration_minutes=15,
        max_duration_minutes=60,
        booking_horizon_days=1,
        max_upcoming_per_principal=1,
        max_concurrent_per_principal=1,
    )
    services.update_policy(policy=result.policy, actor_user=admin, max_duration_minutes=120)
    services.deactivate_policy(policy=result.policy, actor_user=admin)

    assert list(AuditEvent.objects.order_by("occurred_at").values_list("action", flat=True)) == [
        AuditEvent.ACTION_POLICY_CREATED,
        AuditEvent.ACTION_POLICY_UPDATED,
        AuditEvent.ACTION_POLICY_DEACTIVATED,
    ]
