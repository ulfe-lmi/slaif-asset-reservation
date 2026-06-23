from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.urls import reverse
from django.utils import timezone

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset, AssetTag
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.reservations.exceptions import RESERVATION_CONFLICT, ReservationDomainError
from slaif_reservation.reservations.models import (
    SERVICE_UPDATE_ATTR,
    Reservation,
    ReservationPolicy,
)
from slaif_reservation.reservations.services import create_reservation
from slaif_reservation.web.availability import availability_for_asset
from slaif_reservation.web.forms import ReservationForm


@pytest.fixture
def member_user() -> User:
    return User.objects.create_user(
        email="member@example.com",
        password="not-a-secret",
        display_name="Member User",
        timezone="Europe/Ljubljana",
    )


@pytest.fixture
def other_user() -> User:
    return User.objects.create_user(email="other@example.com", password="not-a-secret")


@pytest.fixture
def staff_user() -> User:
    return User.objects.create_user(
        email="staff@example.com",
        password="not-a-secret",
        is_staff=True,
    )


@pytest.fixture
def service_account() -> User:
    return User.objects.create_user(
        email="agent@example.com",
        password="not-a-secret",
        is_service_account=True,
    )


@pytest.fixture
def inactive_user() -> User:
    return User.objects.create_user(
        email="inactive@example.com",
        password="not-a-secret",
        is_active=False,
    )


@pytest.fixture
def machine() -> Asset:
    return Asset.objects.create(
        slug="machine-a",
        name="Machine A",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
        verification_required=False,
    )


@pytest.fixture
def asset(machine: Asset) -> Asset:
    return Asset.objects.create(
        slug="gpu-a",
        name="GPU A",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
        verification_required=True,
    )


@pytest.fixture
def second_asset(machine: Asset) -> Asset:
    return Asset.objects.create(
        slug="gpu-b",
        name="GPU B",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
        verification_required=False,
    )


@pytest.fixture
def policy(asset: Asset) -> ReservationPolicy:
    return ReservationPolicy.objects.create(
        name="Member test policy",
        asset=asset,
        active=True,
        min_duration_minutes=30,
        max_duration_minutes=240,
        booking_horizon_days=30,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=10,
        max_concurrent_per_principal=2,
        purpose_required=False,
    )


@pytest.fixture
def second_policy(second_asset: Asset) -> ReservationPolicy:
    return ReservationPolicy.objects.create(
        name="Second policy",
        asset=second_asset,
        active=True,
        min_duration_minutes=30,
        max_duration_minutes=240,
        booking_horizon_days=30,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=10,
        max_concurrent_per_principal=2,
        purpose_required=False,
    )


def _future_pair(hours: int = 2) -> tuple[datetime, datetime]:
    start = (timezone.now() + timedelta(days=1, hours=hours)).replace(second=0, microsecond=0)
    return start, start + timedelta(hours=1)


@pytest.mark.django_db
def test_login_success_service_account_denial_and_safe_next(
    client,
    member_user: User,
    service_account: User,
) -> None:
    response = client.post(
        "/login/?next=http://example.com/phish",
        {"username": member_user.email, "password": "not-a-secret"},
    )
    assert response.status_code == 302
    assert response["Location"] == "/"

    client.logout()
    response = client.post(
        "/login/",
        {"username": service_account.email, "password": "not-a-secret"},
    )
    assert response.status_code == 200
    assert b"Enter a valid email address and password" in response.content
    assert b"service" not in response.content.lower()


@pytest.mark.django_db
def test_post_only_logout(client, member_user: User) -> None:
    client.force_login(member_user)

    assert client.get("/logout/").status_code == 405
    assert client.post("/logout/").status_code == 302


@pytest.mark.django_db
def test_profile_allows_only_display_name_and_timezone(client, member_user: User) -> None:
    client.force_login(member_user)

    response = client.post(
        "/profile/",
        {
            "display_name": "Updated Name",
            "timezone": "UTC",
            "is_staff": "on",
            "is_service_account": "on",
        },
    )

    assert response.status_code == 302
    member_user.refresh_from_db()
    assert member_user.display_name == "Updated Name"
    assert member_user.timezone == "UTC"
    assert not member_user.is_staff
    assert not member_user.is_service_account

    response = client.post("/profile/", {"display_name": "Bad", "timezone": "Mars/Base"})
    assert response.status_code == 200
    assert b"Enter a valid IANA timezone name" in response.content


@pytest.mark.django_db
def test_member_routes_require_active_human_account(
    client,
    member_user: User,
    inactive_user: User,
    asset: Asset,
) -> None:
    member_paths = [
        "/",
        "/profile/",
        "/assets/",
        f"/assets/{asset.id}/",
        f"/assets/{asset.id}/reserve/",
        "/reservations/",
    ]

    for path in member_paths:
        assert client.get(path).status_code == 302

    client.force_login(member_user)
    for path in member_paths:
        assert client.get(path).status_code == 200

    client.force_login(inactive_user)
    assert client.get("/").status_code == 302


@pytest.mark.django_db
def test_member_asset_browsing_hides_inactive_and_internal_fields(
    client,
    member_user: User,
    asset: Asset,
) -> None:
    inactive = Asset.objects.create(
        slug="inactive-gpu",
        name="Inactive GPU",
        kind=Asset.KIND_GPU,
        parent=asset.parent,
        active=False,
        reservable=False,
        legacy_source="legacy",
        legacy_id="secret-legacy",
        physical_locator="rack secret",
    )
    tag = AssetTag.objects.create(slug="cuda", name="CUDA")
    asset.tags.add(tag)
    client.force_login(member_user)

    response = client.get("/assets/", {"kind": Asset.KIND_GPU, "tag": "cuda", "q": "GPU"})

    assert response.status_code == 200
    content = response.content.decode()
    assert asset.name in content
    assert inactive.name not in content
    assert "secret-legacy" not in content
    assert "rack secret" not in content


@pytest.mark.django_db
def test_staff_asset_api_remains_staff_only(
    client,
    member_user: User,
    staff_user: User,
    asset: Asset,
) -> None:
    client.force_login(member_user)
    assert client.get("/api/v1/assets/").status_code == 403
    assert client.get(f"/api/v1/assets/{asset.id}/").status_code == 403

    client.force_login(staff_user)
    assert client.get("/api/v1/assets/").status_code == 200


@pytest.mark.django_db
def test_availability_clips_merges_and_hides_other_user_private_fields(
    member_user: User,
    other_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    window_date = date(2026, 1, 5)
    tz = ZoneInfo("Europe/Ljubljana")
    first_start = datetime(2026, 1, 5, 9, 0, tzinfo=tz).astimezone(UTC)
    first_end = datetime(2026, 1, 5, 10, 0, tzinfo=tz).astimezone(UTC)
    second_end = datetime(2026, 1, 5, 11, 0, tzinfo=tz).astimezone(UTC)
    create_reservation(
        asset=asset,
        requested_by_user=other_user,
        start_at=first_start,
        end_at=first_end,
        purpose="secret purpose",
        now=datetime(2026, 1, 4, 8, 0, tzinfo=UTC),
    )
    create_reservation(
        asset=asset,
        requested_by_user=member_user,
        start_at=first_end,
        end_at=second_end,
        purpose="own purpose",
        now=datetime(2026, 1, 4, 8, 0, tzinfo=UTC),
    )
    cancelled = create_reservation(
        asset=asset,
        requested_by_user=other_user,
        start_at=datetime(2026, 1, 5, 12, 0, tzinfo=tz).astimezone(UTC),
        end_at=datetime(2026, 1, 5, 13, 0, tzinfo=tz).astimezone(UTC),
        purpose="cancelled secret",
        now=datetime(2026, 1, 4, 8, 0, tzinfo=UTC),
    ).reservation
    cancelled.status = Reservation.STATUS_CANCELLED
    cancelled.cancelled_at = datetime(2026, 1, 4, 9, 0, tzinfo=UTC)
    cancelled.cancelled_by = other_user
    cancelled.full_clean()
    setattr(cancelled, SERVICE_UPDATE_ATTR, True)
    cancelled.save()

    result = availability_for_asset(
        asset=asset,
        principal=member_user,
        start_date=window_date,
        days=1,
        display_timezone="Europe/Ljubljana",
        now=datetime(2026, 1, 4, 8, 0, tzinfo=UTC),
    )

    assert result.bookable
    assert len(result.busy) == 1
    assert result.busy[0].label == "Unavailable"
    assert result.busy[0].reservation_id is None
    assert result.free
    serialized = repr(result)
    assert other_user.email not in serialized
    assert "secret purpose" not in serialized
    assert str(cancelled.id) not in serialized


@pytest.mark.django_db
def test_availability_policy_bounds_and_non_bookable_states(
    member_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    policy.min_duration_minutes = 90
    policy.min_lead_minutes = 60
    policy.booking_horizon_days = 1
    setattr(policy, SERVICE_UPDATE_ATTR, True)
    policy.save()

    result = availability_for_asset(
        asset=asset,
        principal=member_user,
        start_date=date(2026, 3, 29),
        days=1,
        display_timezone="Europe/Ljubljana",
        now=datetime(2026, 3, 28, 23, 30, tzinfo=UTC),
    )

    assert result.free
    assert all(interval.latest_start >= interval.start for interval in result.free)

    asset.reservable = False
    asset.full_clean()
    asset.save()
    result = availability_for_asset(
        asset=asset,
        principal=member_user,
        start_date=date(2026, 3, 29),
        days=1,
        display_timezone="Europe/Ljubljana",
        now=datetime(2026, 3, 28, 23, 30, tzinfo=UTC),
    )
    assert not result.bookable
    assert result.free == []


@pytest.mark.django_db
def test_reservation_form_rejects_dst_nonexistent_and_ambiguous_times() -> None:
    nonexistent = ReservationForm(
        data={
            "start": "2026-03-29T02:30",
            "end": "2026-03-29T03:30",
            "purpose": "",
        },
        timezone_name="Europe/Ljubljana",
    )
    assert not nonexistent.is_valid()
    assert "does not exist" in str(nonexistent.errors["start"])

    ambiguous = ReservationForm(
        data={
            "start": "2026-10-25T02:30",
            "end": "2026-10-25T03:30",
            "purpose": "",
        },
        timezone_name="Europe/Ljubljana",
    )
    assert not ambiguous.is_valid()
    assert "ambiguous" in str(ambiguous.errors["start"])

    explicit = ReservationForm(
        data={
            "start": "2026-10-25T02:30",
            "start_fold": "1",
            "end": "2026-10-25T03:30",
            "purpose": "",
        },
        timezone_name="Europe/Ljubljana",
    )
    assert explicit.is_valid(), explicit.errors


@pytest.mark.django_db
def test_create_reservation_view_uses_domain_service_and_preserves_conflict_input(
    client,
    monkeypatch,
    member_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    calls = []

    def fake_create_reservation(**kwargs):
        calls.append(kwargs)
        raise ReservationDomainError(RESERVATION_CONFLICT, "conflict")

    monkeypatch.setattr("slaif_reservation.web.views.create_reservation", fake_create_reservation)
    client.force_login(member_user)

    response = client.post(
        reverse("web:reserve", args=[asset.id]),
        {
            "start": "2026-01-05T09:00",
            "end": "2026-01-05T10:00",
            "purpose": "Synthetic purpose",
        },
    )

    assert response.status_code == 200
    assert calls[0]["source"] == Reservation.SOURCE_WEB
    assert b"That time is no longer available" in response.content
    assert b"Synthetic purpose" in response.content


@pytest.mark.django_db
def test_duplicate_form_submission_creates_one_reservation(
    client,
    member_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    start, end = _future_pair()
    local_start = start.astimezone(ZoneInfo(member_user.timezone)).strftime("%Y-%m-%dT%H:%M")
    local_end = end.astimezone(ZoneInfo(member_user.timezone)).strftime("%Y-%m-%dT%H:%M")
    data = {"start": local_start, "end": local_end, "purpose": "once"}
    client.force_login(member_user)

    first = client.post(reverse("web:reserve", args=[asset.id]), data)
    second = client.post(reverse("web:reserve", args=[asset.id]), data)

    assert first.status_code == 302
    assert second.status_code == 200
    assert Reservation.objects.filter(asset=asset, requested_by_user=member_user).count() == 1
    assert b"That time is no longer available" in second.content


@pytest.mark.django_db
def test_own_reservation_routes_hide_other_user_and_do_not_mutate_on_get(
    client,
    member_user: User,
    other_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    start, end = _future_pair()
    own = create_reservation(
        asset=asset,
        requested_by_user=member_user,
        start_at=start,
        end_at=end,
        purpose="own",
    ).reservation
    other = create_reservation(
        asset=asset,
        requested_by_user=other_user,
        start_at=end + timedelta(hours=1),
        end_at=end + timedelta(hours=2),
        purpose="other-private-purpose",
    ).reservation
    client.force_login(member_user)

    assert client.get(reverse("web:reservation-detail", args=[own.id])).status_code == 200
    assert client.get(reverse("web:reservation-detail", args=[other.id])).status_code == 404
    assert client.get(reverse("web:reservation-cancel", args=[own.id])).status_code == 405
    own.refresh_from_db()
    assert own.status == Reservation.STATUS_CONFIRMED


@pytest.mark.django_db
def test_cancel_and_release_routes_call_authoritative_services(
    client,
    monkeypatch,
    member_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    start, end = _future_pair()
    reservation = create_reservation(
        asset=asset,
        requested_by_user=member_user,
        start_at=start,
        end_at=end,
        purpose="own",
    ).reservation
    cancelled_calls = []
    release_calls = []

    def fake_cancel_reservation(**kwargs):
        cancelled_calls.append(kwargs)
        return object()

    def fake_release_reservation(**kwargs):
        release_calls.append(kwargs)
        return object()

    monkeypatch.setattr("slaif_reservation.web.views.cancel_reservation", fake_cancel_reservation)
    monkeypatch.setattr("slaif_reservation.web.views.release_reservation", fake_release_reservation)
    client.force_login(member_user)

    assert client.post(reverse("web:reservation-cancel", args=[reservation.id])).status_code == 302
    assert cancelled_calls[0]["source"] == Reservation.SOURCE_WEB
    assert cancelled_calls[0]["requested_by_user"] == member_user

    assert client.post(reverse("web:reservation-release", args=[reservation.id])).status_code == 302
    assert release_calls[0]["source"] == Reservation.SOURCE_WEB
    assert release_calls[0]["requested_by_user"] == member_user


@pytest.mark.django_db
def test_cancellation_error_rolls_back_and_shows_safe_message(
    client,
    monkeypatch,
    member_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    start, end = _future_pair()
    reservation = create_reservation(
        asset=asset,
        requested_by_user=member_user,
        start_at=start,
        end_at=end,
        purpose="own",
    ).reservation

    def fake_cancel_reservation(**kwargs):
        raise ReservationDomainError("unexpected", "database detail")

    monkeypatch.setattr("slaif_reservation.web.views.cancel_reservation", fake_cancel_reservation)
    client.force_login(member_user)

    response = client.post(reverse("web:reservation-cancel", args=[reservation.id]), follow=True)

    reservation.refresh_from_db()
    assert reservation.status == Reservation.STATUS_CONFIRMED
    assert b"The reservation could not be changed" in response.content
    assert b"database detail" not in response.content


@pytest.mark.django_db
def test_openapi_still_has_no_reservation_mutation_routes(client) -> None:
    response = client.get("/api/v1/")

    assert response.status_code == 200
    assert response.json()["endpoints"] == {"assets": "/api/v1/assets/"}
    assert "/api/v1/reservations/" not in response.content.decode()


@pytest.mark.django_db
def test_rendered_availability_does_not_expose_other_user_fields(
    client,
    member_user: User,
    other_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    start, end = _future_pair()
    reservation = create_reservation(
        asset=asset,
        requested_by_user=other_user,
        start_at=start,
        end_at=end,
        purpose="other secret purpose",
    ).reservation
    client.force_login(member_user)

    response = client.get(reverse("web:asset-detail", args=[asset.id]))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Unavailable" in content
    assert other_user.email not in content
    assert "other secret purpose" not in content
    assert str(reservation.id) not in content
    assert "physical_locator" not in content
    assert "legacy_id" not in content


@pytest.mark.django_db
def test_successful_creation_writes_audit_and_redirects_to_detail(
    client,
    member_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    start, end = _future_pair(4)
    local_start = start.astimezone(ZoneInfo(member_user.timezone)).strftime("%Y-%m-%dT%H:%M")
    local_end = end.astimezone(ZoneInfo(member_user.timezone)).strftime("%Y-%m-%dT%H:%M")
    client.force_login(member_user)

    response = client.post(
        reverse("web:reserve", args=[asset.id]),
        {"start": local_start, "end": local_end, "purpose": "safe purpose"},
    )

    reservation = Reservation.objects.get(requested_by_user=member_user)
    assert response.status_code == 302
    assert response["Location"] == reverse("web:reservation-detail", args=[reservation.id])
    assert (
        AuditEvent.objects.filter(
            action=AuditEvent.ACTION_RESERVATION_CREATED,
            target_id=reservation.id,
        ).count()
        == 1
    )
