from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from django.contrib.admin.sites import site
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.admin import AuditEventAdmin
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.reservations.admin import ReservationAdmin, ReservationPolicyAdmin
from slaif_reservation.reservations.models import (
    Reservation,
    ReservationLifecycle,
    ReservationPolicy,
    derive_lifecycle,
)


def create_user(email: str = "user@example.com", **overrides: object) -> User:
    return User.objects.create_user(email=email, password="not-a-secret", **overrides)


def create_asset(slug: str = "asset-a", **overrides: object) -> Asset:
    values = {
        "slug": slug,
        "name": slug.replace("-", " ").title(),
        "kind": Asset.KIND_GPU,
        "active": True,
        "reservable": True,
    }
    values.update(overrides)
    return Asset.objects.create(**values)


def create_policy(**overrides: object) -> ReservationPolicy:
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


def create_reservation_row(
    *,
    asset: Asset,
    user: User,
    start_at,
    end_at,
    status: str = Reservation.STATUS_CONFIRMED,
    **overrides: object,
) -> Reservation:
    values = {
        "asset": asset,
        "requested_by_user": user,
        "source": Reservation.SOURCE_WEB,
        "status": status,
        "start_at": start_at,
        "end_at": end_at,
        "effective_end_at": end_at,
        "purpose": "test",
    }
    values.update(overrides)
    return Reservation.objects.create(**values)


@pytest.mark.django_db
def test_policy_and_reservation_use_uuid_identities() -> None:
    user = create_user()
    asset = create_asset()
    policy = create_policy(asset=asset)
    start = timezone.now() + timedelta(hours=1)
    reservation = create_reservation_row(
        asset=asset, user=user, start_at=start, end_at=start + timedelta(hours=1)
    )

    assert isinstance(policy.id, uuid.UUID)
    assert isinstance(reservation.id, uuid.UUID)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field,value",
    [
        ("min_duration_minutes", 0),
        ("max_duration_minutes", 10),
        ("max_upcoming_per_principal", 0),
        ("max_concurrent_per_principal", 0),
    ],
)
def test_policy_numeric_validation(field: str, value: int) -> None:
    values = {
        "name": "Invalid",
        "min_duration_minutes": 15,
        "max_duration_minutes": 60,
        "booking_horizon_days": 1,
        "max_upcoming_per_principal": 1,
        "max_concurrent_per_principal": 1,
    }
    values[field] = value
    policy = ReservationPolicy(**values)

    with pytest.raises(ValidationError):
        policy.full_clean()


@pytest.mark.django_db
def test_policy_active_scope_is_database_enforced() -> None:
    asset = create_asset()
    create_policy(asset=asset)
    with pytest.raises(IntegrityError), transaction.atomic():
        create_policy(name="Duplicate asset policy", asset=asset)

    create_policy(name="Global")
    with pytest.raises(IntegrityError), transaction.atomic():
        create_policy(name="Duplicate global")


@pytest.mark.django_db
def test_reservation_state_validation_rejects_inconsistent_fields() -> None:
    user = create_user()
    asset = create_asset()
    start = timezone.now() + timedelta(hours=1)
    reservation = Reservation(
        asset=asset,
        requested_by_user=user,
        source=Reservation.SOURCE_WEB,
        status=Reservation.STATUS_RELEASED,
        start_at=start,
        end_at=start + timedelta(hours=2),
        effective_end_at=start + timedelta(hours=2),
    )

    with pytest.raises(ValidationError, match="Released reservations require released_at"):
        reservation.full_clean()


@pytest.mark.django_db(transaction=True)
def test_postgresql_exclusion_rejects_direct_overlap() -> None:
    user = create_user()
    asset = create_asset()
    start = timezone.now() + timedelta(hours=1)
    create_reservation_row(
        asset=asset, user=user, start_at=start, end_at=start + timedelta(hours=1)
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        create_reservation_row(
            asset=asset,
            user=user,
            start_at=start + timedelta(minutes=30),
            end_at=start + timedelta(hours=2),
        )


@pytest.mark.django_db(transaction=True)
def test_postgresql_exclusion_allows_adjacent_and_different_asset_ranges() -> None:
    user = create_user()
    asset = create_asset()
    other_asset = create_asset("asset-b")
    start = timezone.now() + timedelta(hours=1)
    create_reservation_row(
        asset=asset, user=user, start_at=start, end_at=start + timedelta(hours=1)
    )

    create_reservation_row(
        asset=asset,
        user=user,
        start_at=start + timedelta(hours=1),
        end_at=start + timedelta(hours=2),
    )
    create_reservation_row(
        asset=other_asset,
        user=user,
        start_at=start + timedelta(minutes=15),
        end_at=start + timedelta(minutes=45),
    )

    assert Reservation.objects.count() == 3


@pytest.mark.django_db(transaction=True)
def test_cancelled_reservation_does_not_block() -> None:
    user = create_user()
    asset = create_asset()
    start = timezone.now() + timedelta(hours=1)
    create_reservation_row(
        asset=asset,
        user=user,
        start_at=start,
        end_at=start + timedelta(hours=1),
        status=Reservation.STATUS_CANCELLED,
        cancelled_at=timezone.now(),
        cancelled_by=user,
    )

    create_reservation_row(
        asset=asset,
        user=user,
        start_at=start + timedelta(minutes=15),
        end_at=start + timedelta(minutes=45),
    )

    assert Reservation.objects.count() == 2


@pytest.mark.django_db(transaction=True)
def test_released_reservation_blocks_only_historical_effective_interval() -> None:
    user = create_user()
    asset = create_asset()
    start = timezone.now() - timedelta(hours=1)
    released_at = start + timedelta(minutes=30)
    end = start + timedelta(hours=2)
    create_reservation_row(
        asset=asset,
        user=user,
        start_at=start,
        end_at=end,
        effective_end_at=released_at,
        status=Reservation.STATUS_RELEASED,
        released_at=released_at,
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        create_reservation_row(
            asset=asset,
            user=user,
            start_at=start + timedelta(minutes=10),
            end_at=start + timedelta(minutes=20),
        )

    create_reservation_row(
        asset=asset,
        user=user,
        start_at=released_at,
        end_at=end,
    )

    assert Reservation.objects.count() == 2


@pytest.mark.django_db
def test_lifecycle_completed_is_derived_without_status_update() -> None:
    user = create_user()
    asset = create_asset()
    now = timezone.now()
    reservation = create_reservation_row(
        asset=asset,
        user=user,
        start_at=now - timedelta(hours=2),
        end_at=now - timedelta(hours=1),
    )

    assert derive_lifecycle(reservation, at=now) == ReservationLifecycle.COMPLETED
    reservation.refresh_from_db()
    assert reservation.status == Reservation.STATUS_CONFIRMED


@pytest.mark.django_db
def test_audit_event_is_append_only_and_admin_read_only(rf) -> None:
    user = create_user(is_staff=True, is_superuser=True)
    event = AuditEvent.objects.create(
        occurred_at=timezone.now(),
        actor_user=user,
        action=AuditEvent.ACTION_RESERVATION_CREATED,
        target_type="reservation",
        target_id=uuid.uuid4(),
        correlation_id=uuid.uuid4(),
        source=AuditEvent.SOURCE_WEB,
        metadata={"safe": "value"},
    )
    event.metadata = {"safe": "changed"}

    with pytest.raises(ValidationError, match="append-only"):
        event.save()
    with pytest.raises(ValidationError, match="append-only"):
        event.delete()

    request = rf.get("/admin/")
    request.user = user
    audit_admin = site._registry[AuditEvent]
    assert isinstance(audit_admin, AuditEventAdmin)
    assert not audit_admin.has_add_permission(request)
    assert not audit_admin.has_change_permission(request, event)
    assert not audit_admin.has_delete_permission(request, event)


@pytest.mark.django_db
def test_reservation_and_policy_admin_are_read_only(rf) -> None:
    staff = create_user("staff@example.com", is_staff=True, is_superuser=True)
    request = rf.get("/admin/")
    request.user = staff

    reservation_admin = site._registry[Reservation]
    policy_admin = site._registry[ReservationPolicy]

    assert isinstance(reservation_admin, ReservationAdmin)
    assert isinstance(policy_admin, ReservationPolicyAdmin)
    assert not reservation_admin.has_add_permission(request)
    assert not reservation_admin.has_change_permission(request)
    assert not reservation_admin.has_delete_permission(request)
    assert not policy_admin.has_add_permission(request)
    assert not policy_admin.has_change_permission(request)
    assert not policy_admin.has_delete_permission(request)
