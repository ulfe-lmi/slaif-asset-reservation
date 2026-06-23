from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

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
def test_policy_target_allows_machine_and_any_child_but_rejects_orphan_non_machine() -> None:
    machine = create_asset("machine-a", kind=Asset.KIND_MACHINE, reservable=False)
    cpu_pool = create_asset("machine-a-cpu", kind=Asset.KIND_CPU_POOL, parent=machine)
    service = create_asset("machine-a-service", kind=Asset.KIND_SERVICE, parent=machine)
    orphan_service = create_asset("orphan-service", kind=Asset.KIND_SERVICE)

    create_policy(name="machine policy", asset=machine)
    create_policy(name="cpu policy", asset=cpu_pool)
    create_policy(name="service policy", asset=service)

    invalid = ReservationPolicy(
        name="orphan",
        asset=orphan_service,
        min_duration_minutes=15,
        max_duration_minutes=60,
        booking_horizon_days=1,
        max_upcoming_per_principal=1,
        max_concurrent_per_principal=1,
    )
    with pytest.raises(ValidationError, match="machine or child asset"):
        invalid.full_clean()


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
def test_lifecycle_rejects_naive_at_value() -> None:
    user = create_user()
    asset = create_asset()
    now = timezone.now()
    reservation = create_reservation_row(
        asset=asset,
        user=user,
        start_at=now + timedelta(hours=1),
        end_at=now + timedelta(hours=2),
    )

    with pytest.raises(ValidationError, match="at must be timezone-aware"):
        derive_lifecycle(reservation, at=datetime(2026, 1, 1, 12, 0))


@pytest.mark.django_db
def test_reservation_model_validation_uses_absolute_instants_and_rejects_naive_values() -> None:
    user = create_user()
    asset = create_asset()
    start = datetime(2026, 3, 29, 1, 30, tzinfo=ZoneInfo("Europe/Ljubljana"))
    end_same_instant = datetime(2026, 3, 29, 0, 30, tzinfo=ZoneInfo("UTC"))
    reservation = Reservation(
        asset=asset,
        requested_by_user=user,
        source=Reservation.SOURCE_WEB,
        status=Reservation.STATUS_CONFIRMED,
        start_at=start,
        end_at=end_same_instant,
        effective_end_at=end_same_instant,
    )
    with pytest.raises(ValidationError, match="End must be after start"):
        reservation.full_clean()

    reservation.start_at = datetime(2026, 1, 1, 12, 0)
    reservation.end_at = timezone.now() + timedelta(hours=1)
    reservation.effective_end_at = reservation.end_at
    with pytest.raises(ValidationError, match="start_at must be timezone-aware"):
        reservation.full_clean()


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
def test_audit_event_blocks_ordinary_overwrite_update_and_delete() -> None:
    user = create_user(is_staff=True)
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

    reconstructed = AuditEvent(
        id=event.id,
        occurred_at=timezone.now(),
        actor_user=user,
        action=AuditEvent.ACTION_RESERVATION_CANCELLED,
        target_type="reservation",
        target_id=uuid.uuid4(),
        correlation_id=uuid.uuid4(),
        source=AuditEvent.SOURCE_WEB,
        metadata={"safe": "changed"},
    )
    with pytest.raises(ValidationError, match="append-only"):
        reconstructed.save()
    with pytest.raises(ValidationError, match="append-only"):
        AuditEvent.objects.filter(pk=event.pk).update(metadata={"safe": "changed"})
    event.metadata = {"safe": "changed"}
    with pytest.raises(ValidationError, match="append-only"):
        AuditEvent.objects.bulk_update([event], ["metadata"])
    with pytest.raises(ValidationError, match="append-only"):
        AuditEvent.objects.filter(pk=event.pk).delete()

    event.refresh_from_db()
    assert event.action == AuditEvent.ACTION_RESERVATION_CREATED
    assert event.metadata == {"safe": "value"}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "metadata",
    [
        {"nested": {"password": "hidden"}},
        {"items": [{"token": "hidden"}]},
        {"headers": {"Authorization": "hidden"}},
        {"nested": {"raw-request body": "hidden"}},
        {"items": [{"Physical Locator": "hidden"}]},
    ],
)
def test_audit_metadata_rejects_forbidden_nested_keys(metadata: dict[str, object]) -> None:
    with pytest.raises(ValidationError, match="forbidden key"):
        AuditEvent.objects.create(
            occurred_at=timezone.now(),
            action=AuditEvent.ACTION_RESERVATION_CREATED,
            target_type="reservation",
            target_id=uuid.uuid4(),
            correlation_id=uuid.uuid4(),
            source=AuditEvent.SOURCE_WEB,
            metadata=metadata,
        )


@pytest.mark.django_db
def test_audit_metadata_rejects_oversized_nested_payload() -> None:
    with pytest.raises(ValidationError, match="too large"):
        AuditEvent.objects.create(
            occurred_at=timezone.now(),
            action=AuditEvent.ACTION_RESERVATION_CREATED,
            target_type="reservation",
            target_id=uuid.uuid4(),
            correlation_id=uuid.uuid4(),
            source=AuditEvent.SOURCE_WEB,
            metadata={"nested": {"safe": "x" * 5000}},
        )


@pytest.mark.django_db
def test_reservation_history_and_hard_delete_are_protected() -> None:
    user = create_user()
    asset = create_asset()
    other_asset = create_asset("asset-b")
    start = timezone.now() + timedelta(hours=1)
    reservation = create_reservation_row(
        asset=asset, user=user, start_at=start, end_at=start + timedelta(hours=1)
    )

    reservation.asset = other_asset
    with pytest.raises(ValidationError, match="authoritative services"):
        reservation.save()
    with pytest.raises(ValidationError, match="hard-deleted"):
        reservation.delete()
    with pytest.raises(ValidationError, match="changed through services"):
        Reservation.objects.filter(pk=reservation.pk).update(source=Reservation.SOURCE_ADMIN)
    with pytest.raises(ValidationError, match="hard-deleted"):
        Reservation.objects.filter(pk=reservation.pk).delete()


@pytest.mark.django_db
def test_reservation_policy_updates_and_hard_delete_are_protected() -> None:
    reservation_policy = create_policy()

    reservation_policy.name = "changed"
    with pytest.raises(ValidationError, match="audited services"):
        reservation_policy.save()
    with pytest.raises(ValidationError, match="hard-deleted"):
        reservation_policy.delete()
    with pytest.raises(ValidationError, match="changed through services"):
        ReservationPolicy.objects.filter(pk=reservation_policy.pk).update(name="changed")
    with pytest.raises(ValidationError, match="hard-deleted"):
        ReservationPolicy.objects.filter(pk=reservation_policy.pk).delete()


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
