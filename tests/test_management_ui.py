from __future__ import annotations

from datetime import UTC, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from slaif_reservation.accounts.models import User
from slaif_reservation.accounts.services import issue_api_token
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.reservations.exceptions import BLACKOUT_CONFLICT, ReservationDomainError
from slaif_reservation.reservations.models import (
    MaintenanceBlackout,
    Reservation,
    ReservationPolicy,
)
from slaif_reservation.reservations.services import (
    create_blackout,
    create_reservation,
    deactivate_blackout,
)
from slaif_reservation.web.availability import availability_for_asset


@pytest.fixture
def member_user() -> User:
    return User.objects.create_user(
        email="member-management@example.com",
        password="not-a-secret",
        display_name="Member User",
    )


@pytest.fixture
def other_user() -> User:
    return User.objects.create_user(
        email="other-management@example.com",
        password="not-a-secret",
        display_name="Other User",
    )


@pytest.fixture
def staff_user() -> User:
    return User.objects.create_user(
        email="staff-management@example.com",
        password="not-a-secret",
        display_name="Staff User",
        is_staff=True,
    )


@pytest.fixture
def superuser() -> User:
    return User.objects.create_superuser(
        email="super-management@example.com",
        password="not-a-secret",
        display_name="Super User",
    )


@pytest.fixture
def service_account() -> User:
    return User.objects.create_user(
        email="service-management@example.com",
        password="not-a-secret",
        is_staff=True,
        is_service_account=True,
    )


@pytest.fixture
def inactive_staff() -> User:
    return User.objects.create_user(
        email="inactive-management@example.com",
        password="not-a-secret",
        is_staff=True,
        is_active=False,
    )


@pytest.fixture
def machine() -> Asset:
    return Asset.objects.create(
        slug="management-machine",
        name="Management Machine",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
        verification_required=False,
    )


@pytest.fixture
def asset(machine: Asset) -> Asset:
    return Asset.objects.create(
        slug="management-gpu",
        name="Management GPU",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
        verification_required=False,
    )


@pytest.fixture
def policy(asset: Asset) -> ReservationPolicy:
    return ReservationPolicy.objects.create(
        name="Management policy",
        asset=asset,
        min_duration_minutes=15,
        max_duration_minutes=240,
        booking_horizon_days=30,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=20,
        max_concurrent_per_principal=5,
        purpose_required=False,
    )


def future_window(days: int = 1, hours: int = 2) -> tuple[timezone.datetime, timezone.datetime]:
    start = (timezone.now() + timedelta(days=days, hours=hours)).replace(
        second=0,
        microsecond=0,
    )
    return start, start + timedelta(hours=1)


def direct_reservation(
    *,
    owner: User,
    target: Asset,
    start: timezone.datetime,
    end: timezone.datetime,
    status: str = Reservation.STATUS_CONFIRMED,
    released_at: timezone.datetime | None = None,
) -> Reservation:
    return Reservation.objects.create(
        asset=target,
        requested_by_user=owner,
        source=Reservation.SOURCE_WEB,
        status=status,
        start_at=start,
        end_at=end,
        effective_end_at=released_at if released_at else end,
        released_at=released_at if status == Reservation.STATUS_RELEASED else None,
        cancelled_at=(
            start - timedelta(minutes=5) if status == Reservation.STATUS_CANCELLED else None
        ),
        cancelled_by=owner if status == Reservation.STATUS_CANCELLED else None,
        cancellation_reason=(
            "private cancellation" if status == Reservation.STATUS_CANCELLED else ""
        ),
        purpose="private management purpose",
    )


def bearer(owner: User, scopes: list[str]) -> str:
    result = issue_api_token(
        owner=owner,
        name="Management API token",
        scopes=scopes,
        lifetime_days=1,
    )
    return result.bearer_token


def auth_header(token: str) -> dict[str, str]:
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.mark.django_db
def test_management_access_role_matrix(
    client: Client,
    member_user: User,
    staff_user: User,
    superuser: User,
    service_account: User,
    inactive_staff: User,
) -> None:
    response = client.get("/manage/")
    assert response.status_code == 302
    assert "/login/" in response["Location"]

    for denied in (member_user, service_account):
        client.force_login(denied)
        response = client.get("/manage/")
        assert response.status_code == 403
        client.logout()
    client.force_login(inactive_staff)
    response = client.get("/manage/")
    assert response.status_code == 302
    assert "/login/" in response["Location"]
    client.logout()

    for allowed in (staff_user, superuser):
        client.force_login(allowed)
        response = client.get("/manage/")
        assert response.status_code == 200
        assert b"Management" in response.content
        client.logout()


@pytest.mark.django_db
def test_staff_member_routes_remain_owner_only(
    client: Client,
    staff_user: User,
    other_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    start, end = future_window()
    reservation = direct_reservation(owner=other_user, target=asset, start=start, end=end)
    client.force_login(staff_user)

    assert client.get(f"/reservations/{reservation.id}/").status_code == 404
    assert (
        client.post(f"/reservations/{reservation.id}/cancel/", {"reason": "x"}).status_code == 404
    )
    assert client.post(f"/reservations/{reservation.id}/release/").status_code == 404
    reservation.refresh_from_db()
    assert reservation.status == Reservation.STATUS_CONFIRMED


@pytest.mark.django_db
def test_policy_management_create_update_deactivate_and_audit(
    client: Client,
    staff_user: User,
    asset: Asset,
) -> None:
    client.force_login(staff_user)
    payload = {
        "name": "Managed policy",
        "asset": str(asset.id),
        "min_duration_minutes": "15",
        "max_duration_minutes": "120",
        "booking_horizon_days": "30",
        "min_lead_minutes": "0",
        "cancellation_cutoff_minutes": "0",
        "max_upcoming_per_principal": "10",
        "max_concurrent_per_principal": "2",
    }

    response = client.post("/manage/policies/new/", payload)
    assert response.status_code == 302
    policy = ReservationPolicy.objects.get(name="Managed policy")
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_POLICY_CREATED).count() == 1

    response = client.post(
        f"/manage/policies/{policy.id}/edit/",
        payload | {"name": "Managed policy updated", "max_duration_minutes": "180"},
    )
    assert response.status_code == 302
    policy.refresh_from_db()
    assert policy.name == "Managed policy updated"
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_POLICY_UPDATED).count() == 1

    response = client.post(f"/manage/policies/{policy.id}/deactivate/")
    assert response.status_code == 302
    policy.refresh_from_db()
    assert not policy.active
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_POLICY_DEACTIVATED).count() == 1


@pytest.mark.django_db
def test_policy_management_invalid_bounds_and_active_scope_conflict(
    client: Client,
    staff_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    client.force_login(staff_user)
    payload = {
        "name": "Conflicting policy",
        "asset": str(asset.id),
        "min_duration_minutes": "60",
        "max_duration_minutes": "30",
        "booking_horizon_days": "30",
        "min_lead_minutes": "0",
        "cancellation_cutoff_minutes": "0",
        "max_upcoming_per_principal": "10",
        "max_concurrent_per_principal": "2",
    }
    response = client.post("/manage/policies/new/", payload)
    assert response.status_code == 200
    assert b"Maximum duration" in response.content

    payload["max_duration_minutes"] = "120"
    response = client.post("/manage/policies/new/", payload)
    assert response.status_code == 200
    assert b"could not be created" in response.content
    assert ReservationPolicy.objects.filter(name="Conflicting policy").count() == 0


@pytest.mark.django_db
def test_blackout_model_services_and_creation_confirmation(
    client: Client,
    staff_user: User,
    member_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    start, end = future_window()
    direct_reservation(owner=member_user, target=asset, start=start, end=end)
    client.force_login(staff_user)
    payload = {
        "asset": str(asset.id),
        "timezone": "UTC",
        "start": start.astimezone(UTC).replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M"),
        "end": end.astimezone(UTC).replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M"),
        "reason": "maintenance window",
    }

    response = client.post("/manage/blackouts/new/", payload)
    assert response.status_code == 200
    assert b"Confirm creation" in response.content
    assert MaintenanceBlackout.objects.count() == 0

    response = client.post("/manage/blackouts/new/", payload | {"confirm_overlaps": "on"})
    assert response.status_code == 302
    blackout = MaintenanceBlackout.objects.get()
    assert blackout.active
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_BLACKOUT_CREATED).count() == 1

    response = client.post(f"/manage/blackouts/{blackout.id}/deactivate/")
    assert response.status_code == 302
    blackout.refresh_from_db()
    assert not blackout.active
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_BLACKOUT_DEACTIVATED).count() == 1


@pytest.mark.django_db
def test_blackout_blocks_web_and_api_reservation_creation_and_half_open_boundary(
    client: Client,
    staff_user: User,
    member_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    start, end = future_window(days=2)
    create_blackout(
        asset=asset,
        actor_user=staff_user,
        reason="maintenance",
        start_at=start,
        end_at=end,
        confirmed_overlap=True,
    )

    with pytest.raises(ReservationDomainError, check=lambda exc: exc.code == BLACKOUT_CONFLICT):
        create_reservation(
            asset=asset,
            requested_by_user=member_user,
            start_at=start + timedelta(minutes=15),
            end_at=end - timedelta(minutes=15),
            purpose="web",
        )
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_RESERVATION_CREATED).count() == 0

    result = create_reservation(
        asset=asset,
        requested_by_user=member_user,
        start_at=end,
        end_at=end + timedelta(minutes=30),
        purpose="adjacent",
    )
    assert result.reservation.start_at == end

    api_owner = User.objects.create_user(email="api-blackout@example.com", password="not-a-secret")
    token = bearer(api_owner, ["reservations:create"])
    response = client.post(
        "/api/v1/reservations/",
        data={
            "asset_id": str(asset.id),
            "start_at": (start + timedelta(minutes=20)).isoformat(),
            "end_at": (end - timedelta(minutes=20)).isoformat(),
            "purpose": "api",
        },
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="blackout-test-key",
        **auth_header(token),
    )
    assert response.status_code == 409
    assert response.json()["code"] == BLACKOUT_CONFLICT


@pytest.mark.django_db
def test_blackout_availability_privacy_and_deactivation(
    staff_user: User,
    member_user: User,
    other_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    window_start = (timezone.now() + timedelta(days=3)).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    blackout = create_blackout(
        asset=asset,
        actor_user=staff_user,
        reason="private maintenance reason",
        start_at=window_start + timedelta(hours=2),
        end_at=window_start + timedelta(hours=4),
        confirmed_overlap=True,
    ).blackout
    direct_reservation(
        owner=other_user,
        target=asset,
        start=window_start + timedelta(hours=4),
        end=window_start + timedelta(hours=5),
    )

    result = availability_for_asset(
        asset=asset,
        principal=member_user,
        start_date=window_start.date(),
        days=1,
        display_timezone="UTC",
        now=window_start - timedelta(days=1),
    )
    assert [(busy.start, busy.end, busy.label) for busy in result.busy] == [
        (window_start + timedelta(hours=2), window_start + timedelta(hours=5), "Unavailable")
    ]
    rendered = str(result)
    assert "private maintenance reason" not in rendered
    assert other_user.email not in rendered

    deactivate_blackout(blackout=blackout, actor_user=staff_user)
    result = availability_for_asset(
        asset=asset,
        principal=member_user,
        start_date=window_start.date(),
        days=1,
        display_timezone="UTC",
        now=window_start - timedelta(days=1),
    )
    assert result.busy[0].start == window_start + timedelta(hours=4)


@pytest.mark.django_db
def test_blackout_audit_failure_rolls_back_creation_and_deactivation(
    monkeypatch: pytest.MonkeyPatch,
    staff_user: User,
    asset: Asset,
) -> None:
    start, end = future_window(days=6)

    def fail_audit(*args: object, **kwargs: object) -> None:
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr("slaif_reservation.reservations.services.append_audit_event", fail_audit)
    with pytest.raises(RuntimeError):
        create_blackout(
            asset=asset,
            actor_user=staff_user,
            reason="maintenance",
            start_at=start,
            end_at=end,
            confirmed_overlap=True,
        )
    assert MaintenanceBlackout.objects.count() == 0

    monkeypatch.undo()
    blackout = create_blackout(
        asset=asset,
        actor_user=staff_user,
        reason="maintenance",
        start_at=start,
        end_at=end,
        confirmed_overlap=True,
    ).blackout

    monkeypatch.setattr("slaif_reservation.reservations.services.append_audit_event", fail_audit)
    with pytest.raises(RuntimeError):
        deactivate_blackout(blackout=blackout, actor_user=staff_user)
    blackout.refresh_from_db()
    assert blackout.active
    assert blackout.deactivated_at is None


@pytest.mark.django_db
def test_staff_cross_user_reservation_management_and_csrf(
    staff_user: User,
    other_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    start, end = future_window(days=4)
    reservation = direct_reservation(owner=other_user, target=asset, start=start, end=end)
    client = Client(enforce_csrf_checks=True)
    client.force_login(staff_user)

    response = client.get("/manage/reservations/")
    assert response.status_code == 200
    assert other_user.email.encode() in response.content

    assert client.get(f"/manage/reservations/{reservation.id}/cancel/").status_code == 405
    response = client.post(f"/manage/reservations/{reservation.id}/cancel/", {"reason": "ops"})
    assert response.status_code == 403
    reservation.refresh_from_db()
    assert reservation.status == Reservation.STATUS_CONFIRMED

    token_response = client.get(f"/manage/reservations/{reservation.id}/")
    csrf = client.cookies["csrftoken"].value
    assert token_response.status_code == 200
    response = client.post(
        f"/manage/reservations/{reservation.id}/cancel/",
        {"reason": "ops"},
        HTTP_X_CSRFTOKEN=csrf,
    )
    assert response.status_code == 302
    reservation.refresh_from_db()
    assert reservation.status == Reservation.STATUS_CANCELLED
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_RESERVATION_CANCELLED).count() == 1


@pytest.mark.django_db
def test_audit_browsing_export_and_privacy(client: Client, staff_user: User, asset: Asset) -> None:
    event = AuditEvent.objects.create(
        occurred_at=timezone.now(),
        actor_user=staff_user,
        action=AuditEvent.ACTION_BLACKOUT_CREATED,
        target_type="maintenance_blackout",
        target_id=asset.id,
        correlation_id=asset.id,
        source=AuditEvent.SOURCE_ADMIN,
        metadata={"asset_slug": asset.slug, "safe": "value"},
    )
    client.force_login(staff_user)

    listing = client.get("/manage/audit/", {"action": AuditEvent.ACTION_BLACKOUT_CREATED})
    assert listing.status_code == 200
    assert str(event.target_id).encode() in listing.content

    detail = client.get(f"/manage/audit/{event.id}/")
    assert detail.status_code == 200
    assert b"safe" in detail.content

    export = client.get("/manage/audit/export.csv", {"action": AuditEvent.ACTION_BLACKOUT_CREATED})
    assert export.status_code == 200
    body = b"".join(export.streaming_content).decode()
    assert "maintenance_blackout.created" in body
    assert "asset_slug" in body
    assert "Authorization" not in body
    assert "cookie" not in body.lower()
    assert "pepper" not in body.lower()


@pytest.mark.django_db
def test_admin_blackout_and_domain_delete_boundaries(
    admin_client,
    staff_user: User,
    asset: Asset,
) -> None:
    blackout = create_blackout(
        asset=asset,
        actor_user=staff_user,
        reason="maintenance",
        start_at=timezone.now() + timedelta(days=5),
        end_at=timezone.now() + timedelta(days=5, hours=1),
        confirmed_overlap=True,
    ).blackout

    with pytest.raises(ValidationError):
        blackout.delete()
    with pytest.raises(ValidationError):
        MaintenanceBlackout.objects.filter(pk=blackout.pk).delete()
    with pytest.raises(ValidationError):
        MaintenanceBlackout.objects.filter(pk=blackout.pk).update(reason="changed")

    response = admin_client.get(reverse("admin:reservations_maintenanceblackout_changelist"))
    assert response.status_code == 200
    response = admin_client.get(reverse("admin:reservations_maintenanceblackout_add"))
    assert response.status_code == 403
