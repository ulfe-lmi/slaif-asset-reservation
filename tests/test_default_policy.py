from __future__ import annotations

import threading
import uuid
from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command, get_commands
from django.db import IntegrityError
from django.utils import timezone

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.reservations import services
from slaif_reservation.reservations.exceptions import (
    BOOKING_HORIZON_VIOLATION,
    DURATION_TOO_LONG,
    DURATION_TOO_SHORT,
    MAX_CONCURRENT_EXCEEDED,
    MAX_UPCOMING_EXCEEDED,
    ReservationDomainError,
)
from slaif_reservation.reservations.initialization import (
    PRESERVED_REASON,
    initialize_default_policy,
)
from slaif_reservation.reservations.models import Reservation, ReservationPolicy


def user(email: str = "member@example.com", **overrides: object) -> User:
    return User.objects.create_user(email=email, password="not-a-secret", **overrides)


def staff(email: str = "staff@example.com") -> User:
    return user(email, is_staff=True)


def asset(slug: str = "gpu-a") -> Asset:
    return Asset.objects.create(
        slug=slug,
        name=slug.replace("-", " ").title(),
        kind=Asset.KIND_GPU,
        active=True,
        reservable=True,
    )


def assert_domain_error(code: str):
    return pytest.raises(ReservationDomainError, match=".", check=lambda exc: exc.code == code)


def assert_default_policy_values(policy: ReservationPolicy) -> None:
    assert policy.name == "default"
    assert policy.asset_id is None
    assert policy.active is True
    assert policy.min_duration_minutes == 1
    assert policy.max_duration_minutes == 2880
    assert policy.booking_horizon_days == 7
    assert policy.min_lead_minutes == 0
    assert policy.cancellation_cutoff_minutes == 0
    assert policy.max_upcoming_per_principal == 50
    assert policy.max_concurrent_per_principal == 8
    assert policy.purpose_required is False


@pytest.mark.django_db
def test_fresh_initialization_creates_exactly_one_default_policy_and_audit() -> None:
    # No application/worker startup side effect: a fresh migrated database
    # contains no policy rows before the explicit command runs.
    assert ReservationPolicy.objects.count() == 0
    assert AuditEvent.objects.count() == 0

    output = StringIO()
    call_command("initialize_default_policy", stdout=output)
    rendered = output.getvalue()
    assert rendered.startswith("status=created")
    assert " name=default" in rendered
    assert " asset=null" in rendered
    assert " active=true" in rendered
    assert " max_duration_minutes=2880" in rendered
    assert " booking_horizon_days=7" in rendered
    assert " max_upcoming_per_principal=50" in rendered
    assert " max_concurrent_per_principal=8" in rendered
    assert " purpose_required=false" in rendered
    correlation_text = rendered.split("correlation=", 1)[1].strip()

    policies = list(ReservationPolicy.objects.all())
    assert len(policies) == 1
    assert_default_policy_values(policies[0])
    assert policies[0].id is not None

    events = list(AuditEvent.objects.all())
    assert len(events) == 1
    event = events[0]
    assert event.action == AuditEvent.ACTION_POLICY_CREATED
    assert event.target_type == "reservation_policy"
    assert event.target_id == policies[0].id
    assert event.source == AuditEvent.SOURCE_ADMIN
    assert event.actor_user_id is None
    assert event.correlation_id == uuid.UUID(correlation_text)
    assert event.metadata == {
        "asset_id": None,
        "initialization": "initialize_default_policy",
    }


@pytest.mark.django_db
def test_repeated_initialization_is_a_noop() -> None:
    call_command("initialize_default_policy", stdout=StringIO())
    policy = ReservationPolicy.objects.get()
    before = {
        field: getattr(policy, field)
        for field in (
            "name",
            "asset_id",
            "active",
            "min_duration_minutes",
            "max_duration_minutes",
            "booking_horizon_days",
            "min_lead_minutes",
            "cancellation_cutoff_minutes",
            "max_upcoming_per_principal",
            "max_concurrent_per_principal",
            "purpose_required",
            "created_at",
            "updated_at",
        )
    }
    assert AuditEvent.objects.count() == 1

    output = StringIO()
    call_command("initialize_default_policy", stdout=output)
    rendered = output.getvalue()
    assert rendered.startswith("status=skipped")
    assert f"reason={PRESERVED_REASON}" in rendered

    assert ReservationPolicy.objects.count() == 1
    assert AuditEvent.objects.count() == 1
    policy.refresh_from_db()
    after = {field: getattr(policy, field) for field in before}
    assert after == before


@pytest.mark.django_db
def test_existing_active_global_policy_preserved() -> None:
    admin = staff()
    services.create_policy(
        actor_user=admin,
        name="operator-global",
        min_duration_minutes=30,
        max_duration_minutes=120,
        booking_horizon_days=1,
        max_upcoming_per_principal=3,
        max_concurrent_per_principal=2,
    )
    policy = ReservationPolicy.objects.get()
    assert AuditEvent.objects.count() == 1

    output = StringIO()
    call_command("initialize_default_policy", stdout=output)
    assert output.getvalue().startswith("status=skipped")

    assert ReservationPolicy.objects.count() == 1
    assert AuditEvent.objects.count() == 1
    policy.refresh_from_db()
    assert policy.name == "operator-global"
    assert policy.active is True
    assert policy.min_duration_minutes == 30
    assert policy.asset_id is None


@pytest.mark.django_db
def test_existing_inactive_global_policy_preserved_without_reactivation() -> None:
    admin = staff()
    result = services.create_policy(
        actor_user=admin,
        name="operator-disabled",
        min_duration_minutes=15,
        max_duration_minutes=60,
        booking_horizon_days=2,
        max_upcoming_per_principal=4,
        max_concurrent_per_principal=2,
    )
    services.deactivate_policy(policy=result.policy, actor_user=admin)
    assert AuditEvent.objects.count() == 2

    output = StringIO()
    call_command("initialize_default_policy", stdout=output)
    assert output.getvalue().startswith("status=skipped")

    assert ReservationPolicy.objects.count() == 1
    assert AuditEvent.objects.count() == 2
    result.policy.refresh_from_db()
    assert result.policy.active is False
    assert result.policy.name == "operator-disabled"


@pytest.mark.django_db
def test_existing_asset_specific_policy_preserved() -> None:
    admin = staff()
    machine = Asset.objects.create(
        slug="machine-a",
        name="Machine A",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
    )
    services.create_policy(
        actor_user=admin,
        name="machine-policy",
        asset=machine,
        min_duration_minutes=10,
        max_duration_minutes=90,
        booking_horizon_days=3,
        max_upcoming_per_principal=2,
        max_concurrent_per_principal=2,
    )
    assert ReservationPolicy.objects.filter(asset__isnull=True).count() == 0

    output = StringIO()
    call_command("initialize_default_policy", stdout=output)
    assert output.getvalue().startswith("status=skipped")

    assert ReservationPolicy.objects.count() == 1
    assert ReservationPolicy.objects.filter(asset__isnull=True).count() == 0
    assert AuditEvent.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_initialization_creates_exactly_one_policy_and_audit() -> None:
    assert ReservationPolicy.objects.count() == 0
    results: list[str] = []
    lock = threading.Lock()
    barrier = threading.Barrier(4)

    def target() -> None:
        from django.db import close_old_connections

        close_old_connections()
        try:
            barrier.wait(timeout=15)
            result = initialize_default_policy()
            outcome = "created" if result.created else "skipped"
        except Exception:
            outcome = "error"
        finally:
            close_old_connections()
        with lock:
            results.append(outcome)

    threads = [threading.Thread(target=target) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
        assert not thread.is_alive()

    assert results.count("created") == 1
    assert results.count("skipped") == 3
    policies = list(ReservationPolicy.objects.all())
    assert len(policies) == 1
    assert_default_policy_values(policies[0])
    events = list(AuditEvent.objects.all())
    assert len(events) == 1
    assert events[0].target_id == policies[0].id
    assert events[0].actor_user_id is None


@pytest.mark.django_db(transaction=True)
def test_race_initialization_vs_configured_specific_insertion() -> None:
    admin = staff()
    specific_asset = Asset.objects.create(
        slug="machine-race",
        name="Machine Race",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
    )
    outcomes: dict[str, str] = {}
    lock = threading.Lock()
    barrier = threading.Barrier(2)

    def initializer() -> None:
        from django.db import close_old_connections

        close_old_connections()
        try:
            barrier.wait(timeout=15)
            result = initialize_default_policy()
            outcome = "created" if result.created else "skipped"
        except Exception:
            outcome = "error"
        finally:
            close_old_connections()
        with lock:
            outcomes["initializer"] = outcome

    def configured_insertion() -> None:
        from django.db import close_old_connections

        close_old_connections()
        try:
            barrier.wait(timeout=15)
            services.create_policy(
                actor_user=admin,
                name="operator-specific",
                asset=specific_asset,
                min_duration_minutes=5,
                max_duration_minutes=45,
                booking_horizon_days=1,
                max_upcoming_per_principal=2,
                max_concurrent_per_principal=2,
            )
            outcome = "committed"
        except Exception:
            outcome = "error"
        finally:
            close_old_connections()
        with lock:
            outcomes["configured"] = outcome

    threads = [threading.Thread(target=initializer), threading.Thread(target=configured_insertion)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
        assert not thread.is_alive()

    assert outcomes["initializer"] in ("created", "skipped")
    assert outcomes["configured"] == "committed"

    policies = list(ReservationPolicy.objects.order_by("id"))
    specific = [p for p in policies if p.asset_id == specific_asset.id]
    assert len(specific) == 1
    assert specific[0].name == "operator-specific"
    assert specific[0].active is True
    assert specific[0].min_duration_minutes == 5
    globals_ = [p for p in policies if p.asset_id is None]
    assert len(globals_) <= 1
    for policy in globals_:
        assert policy.active is True
        assert_default_policy_values(policy)
    # Every policy row has exactly one coupled creation audit; no row is
    # audited twice and no audit references a missing policy.
    events = list(AuditEvent.objects.all())
    assert len(events) == len(policies)
    assert {event.target_id for event in events} == {policy.id for policy in policies}
    created_by_actor = {event.target_id: event.actor_user_id for event in events}
    assert created_by_actor[specific[0].id] == admin.id
    for policy in globals_:
        assert created_by_actor[policy.id] is None


@pytest.mark.django_db(transaction=True)
def test_race_initialization_vs_active_global_insertion() -> None:
    admin = staff()
    outcomes: dict[str, str] = {}
    lock = threading.Lock()
    barrier = threading.Barrier(2)

    def initializer() -> None:
        from django.db import close_old_connections

        close_old_connections()
        try:
            barrier.wait(timeout=15)
            result = initialize_default_policy()
            outcome = "created" if result.created else "skipped"
        except Exception:
            outcome = "error"
        finally:
            close_old_connections()
        with lock:
            outcomes["initializer"] = outcome

    def global_insertion() -> None:
        from django.db import close_old_connections

        close_old_connections()
        try:
            barrier.wait(timeout=15)
            services.create_policy(
                actor_user=admin,
                name="operator-global",
                min_duration_minutes=20,
                max_duration_minutes=200,
                booking_horizon_days=2,
                max_upcoming_per_principal=3,
                max_concurrent_per_principal=3,
            )
            outcome = "committed"
        except IntegrityError:
            outcome = "unique-conflict"
        finally:
            close_old_connections()
        with lock:
            outcomes["global"] = outcome

    threads = [threading.Thread(target=initializer), threading.Thread(target=global_insertion)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
        assert not thread.is_alive()

    assert outcomes["initializer"] in ("created", "skipped")
    assert outcomes["global"] in ("committed", "unique-conflict")
    assert outcomes["initializer"] == "created" or outcomes["global"] == "committed"

    policies = list(ReservationPolicy.objects.all())
    assert len(policies) == 1
    assert policies[0].asset_id is None
    assert policies[0].active is True
    events = list(AuditEvent.objects.all())
    assert len(events) == 1
    assert events[0].target_id == policies[0].id
    if policies[0].name == "default":
        assert_default_policy_values(policies[0])
        assert events[0].actor_user_id is None
    else:
        assert policies[0].name == "operator-global"
        assert events[0].actor_user_id == admin.id


@pytest.mark.django_db
def test_audit_failure_rolls_back_initialization(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_audit(*args: object, **kwargs: object) -> None:
        raise IntegrityError("audit failed")

    monkeypatch.setattr(
        "slaif_reservation.reservations.initialization.append_audit_event", fail_audit
    )

    with pytest.raises(IntegrityError, match="audit failed"):
        initialize_default_policy()

    assert ReservationPolicy.objects.count() == 0
    assert AuditEvent.objects.count() == 0


@pytest.mark.django_db
def test_fresh_asset_is_immediately_reservable_under_initialized_defaults() -> None:
    call_command("initialize_default_policy", stdout=StringIO())
    principal = user()
    gpu = asset()
    now = timezone.now()

    result = services.create_reservation(
        asset=gpu,
        requested_by_user=principal,
        start_at=now + timedelta(hours=1),
        end_at=now + timedelta(hours=2),
        purpose="",
        now=now,
    )

    assert result.reservation.status == Reservation.STATUS_CONFIRMED
    assert Reservation.objects.count() == 1
    created = [
        event
        for event in AuditEvent.objects.all()
        if event.action == AuditEvent.ACTION_RESERVATION_CREATED
    ]
    assert len(created) == 1


@pytest.mark.django_db
def test_default_policy_enforces_duration_minimum_and_maximum() -> None:
    call_command("initialize_default_policy", stdout=StringIO())
    principal = user()
    gpu = asset()
    now = timezone.now()

    with assert_domain_error(DURATION_TOO_SHORT):
        services.create_reservation(
            asset=gpu,
            requested_by_user=principal,
            start_at=now + timedelta(hours=1),
            end_at=now + timedelta(hours=1, seconds=30),
            purpose="",
            now=now,
        )
    with assert_domain_error(DURATION_TOO_LONG):
        services.create_reservation(
            asset=gpu,
            requested_by_user=principal,
            start_at=now + timedelta(hours=1),
            end_at=now + timedelta(hours=1) + timedelta(minutes=2881),
            purpose="",
            now=now,
        )
    # Exactly 2880 minutes is the documented maximum and is accepted.
    exact_max = services.create_reservation(
        asset=gpu,
        requested_by_user=principal,
        start_at=now + timedelta(hours=1),
        end_at=now + timedelta(hours=1) + timedelta(minutes=2880),
        purpose="",
        now=now,
    )
    assert exact_max.reservation.status == Reservation.STATUS_CONFIRMED


@pytest.mark.django_db
def test_default_policy_enforces_seven_day_start_horizon() -> None:
    call_command("initialize_default_policy", stdout=StringIO())
    principal = user()
    gpu = asset()
    now = timezone.now()

    with assert_domain_error(BOOKING_HORIZON_VIOLATION):
        services.create_reservation(
            asset=gpu,
            requested_by_user=principal,
            start_at=now + timedelta(days=7, minutes=1),
            end_at=now + timedelta(days=7, minutes=1) + timedelta(hours=1),
            purpose="",
            now=now,
        )
    assert Reservation.objects.count() == 0


@pytest.mark.django_db
def test_default_policy_allows_start_at_now_with_zero_lead() -> None:
    call_command("initialize_default_policy", stdout=StringIO())
    principal = user()
    gpu = asset()
    now = timezone.now()

    result = services.create_reservation(
        asset=gpu,
        requested_by_user=principal,
        start_at=now,
        end_at=now + timedelta(hours=1),
        purpose="",
        now=now,
    )
    assert result.reservation.status == Reservation.STATUS_CONFIRMED


@pytest.mark.django_db
def test_default_policy_upcoming_limit_is_fifty_per_principal_across_assets() -> None:
    call_command("initialize_default_policy", stdout=StringIO())
    principal = user()
    first_gpu = asset("gpu-up-1")
    second_gpu = asset("gpu-up-2")
    now = timezone.now()

    for index in range(50):
        services.create_reservation(
            asset=first_gpu if index % 2 == 0 else second_gpu,
            requested_by_user=principal,
            start_at=now + timedelta(hours=1 + 2 * index),
            end_at=now + timedelta(hours=2 + 2 * index),
            purpose="",
            now=now,
        )
    assert Reservation.objects.count() == 50

    with assert_domain_error(MAX_UPCOMING_EXCEEDED):
        services.create_reservation(
            asset=first_gpu,
            requested_by_user=principal,
            start_at=now + timedelta(hours=1 + 2 * 50),
            end_at=now + timedelta(hours=2 + 2 * 50),
            purpose="",
            now=now,
        )
    assert Reservation.objects.count() == 50


@pytest.mark.django_db
def test_default_policy_overlap_limit_is_eight_intersecting_records_per_principal() -> None:
    call_command("initialize_default_policy", stdout=StringIO())
    principal = user()
    now = timezone.now()
    start = now + timedelta(hours=1)
    end = now + timedelta(hours=2)

    for index in range(8):
        gpu = asset(f"gpu-ov-{index}")
        services.create_reservation(
            asset=gpu,
            requested_by_user=principal,
            start_at=start,
            end_at=end,
            purpose="",
            now=now,
        )
    # The overlap limit counts existing blocking records intersecting the
    # proposed interval across the principal's assets, not a simultaneous
    # occupancy sweep: eight intersecting records already block a ninth.
    with assert_domain_error(MAX_CONCURRENT_EXCEEDED):
        services.create_reservation(
            asset=asset("gpu-ov-8"),
            requested_by_user=principal,
            start_at=start,
            end_at=end,
            purpose="",
            now=now,
        )
    assert Reservation.objects.count() == 8
    # A non-intersecting proposal for the same principal is unaffected by
    # the overlap count.
    later = services.create_reservation(
        asset=asset("gpu-ov-9"),
        requested_by_user=principal,
        start_at=end + timedelta(hours=1),
        end_at=end + timedelta(hours=2),
        purpose="",
        now=now,
    )
    assert later.reservation.status == Reservation.STATUS_CONFIRMED
    assert Reservation.objects.count() == 9


@pytest.mark.django_db
def test_command_is_registered_and_migrations_alone_do_not_initialize() -> None:
    commands = get_commands()
    assert "initialize_default_policy" in commands
    # Migrations are applied by the test harness before this test; the
    # migrated schema alone must not create a policy row.
    assert ReservationPolicy.objects.count() == 0
    assert AuditEvent.objects.count() == 0
