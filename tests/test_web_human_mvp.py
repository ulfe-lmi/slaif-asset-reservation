from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth.models import Permission
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
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
from slaif_reservation.web.availability import AvailabilityInputError, availability_for_asset
from slaif_reservation.web.forms import ReservationForm

OVERLONG_TIMEZONE = "A" * 1000


def _grant_booking(target: User) -> None:
    # A16: positive booking fixtures explicitly carry the baseline
    # reservations.book_assets capability (real Permission row).
    target.user_permissions.add(
        Permission.objects.get(codename="book_assets", content_type__app_label="reservations")
    )


@pytest.fixture
def member_user() -> User:
    created = User.objects.create_user(
        email="member@example.com",
        password="not-a-secret",
        display_name="Member User",
        timezone="Europe/Ljubljana",
    )
    _grant_booking(created)
    return created


@pytest.fixture
def other_user() -> User:
    created = User.objects.create_user(email="other@example.com", password="not-a-secret")
    _grant_booking(created)
    return created


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


def _local_utc(value: datetime, timezone_name: str = "Europe/Ljubljana") -> datetime:
    return value.replace(tzinfo=ZoneInfo(timezone_name)).astimezone(UTC)


def _direct_reservation(
    *,
    asset: Asset,
    user: User,
    start: datetime,
    end: datetime,
    status: str = Reservation.STATUS_CONFIRMED,
    cancelled_by: User | None = None,
    released_at: datetime | None = None,
    purpose: str = "",
) -> Reservation:
    effective_end_at = released_at if status == Reservation.STATUS_RELEASED else end
    return Reservation.objects.create(
        asset=asset,
        requested_by_user=user,
        source=Reservation.SOURCE_WEB,
        status=status,
        start_at=start,
        end_at=end,
        effective_end_at=effective_end_at,
        purpose=purpose,
        released_at=released_at if status == Reservation.STATUS_RELEASED else None,
        cancelled_at=start - timedelta(days=1) if status == Reservation.STATUS_CANCELLED else None,
        cancelled_by=cancelled_by if status == Reservation.STATUS_CANCELLED else None,
        cancellation_reason=(
            "private cancellation text" if status == Reservation.STATUS_CANCELLED else ""
        ),
    )


def _csrf_token(client: Client, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200
    return client.cookies["csrftoken"].value


def _assert_in_order(content: str, values: list[str]) -> None:
    positions = [content.index(value) for value in values]
    assert positions == sorted(positions)


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
def test_disallowed_authenticated_sessions_terminate_and_clear_session(
    client,
    member_user: User,
    service_account: User,
    asset: Asset,
) -> None:
    for path in ["/login/", "/", "/assets/", "/reservations/"]:
        client.force_login(service_account)
        response = client.get(path, follow=True)

        assert response.status_code == 200
        assert len(response.redirect_chain) <= 1
        assert response.request["PATH_INFO"] == "/login/"
        assert "_auth_user_id" not in client.session
        content = response.content.decode()
        assert "<h1>Dashboard</h1>" not in content
        assert asset.name not in content

    client.force_login(member_user)
    member_user.is_active = False
    member_user.save(update_fields=["is_active"])
    response = client.get("/", follow=True)
    assert response.status_code == 200
    assert response.request["PATH_INFO"] == "/login/"
    assert "_auth_user_id" not in client.session

    member_user.is_active = True
    member_user.save(update_fields=["is_active"])
    client.force_login(member_user)
    response = client.get("/login/", follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [("/", 302)]
    assert b"Dashboard" in response.content


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
@pytest.mark.parametrize(
    ("timezone_value", "expected_error"),
    [
        ("/etc/passwd", b"Enter a valid IANA timezone name"),
        ("../UTC", b"Enter a valid IANA timezone name"),
        ("a/../UTC", b"Enter a valid IANA timezone name"),
        ("Mars/Base", b"Enter a valid IANA timezone name"),
        (OVERLONG_TIMEZONE, b"Ensure this value has at most 64 characters"),
        ("UTC\x00", b"Null characters are not allowed"),
        ("", b"Timezone is required"),
    ],
)
def test_profile_rejects_malformed_unknown_and_blank_timezone_values(
    client,
    member_user: User,
    timezone_value: str,
    expected_error: bytes,
) -> None:
    client.force_login(member_user)

    response = client.post(
        "/profile/",
        {"display_name": "Member User", "timezone": timezone_value},
    )

    assert response.status_code == 200
    assert expected_error in response.content
    assert b"Traceback" not in response.content
    member_user.refresh_from_db()
    assert member_user.timezone == "Europe/Ljubljana"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "stored_timezone",
    ["/etc/passwd", "../UTC", "a/../UTC", "Mars/Base", ""],
)
def test_invalid_stored_timezone_fails_closed_but_profile_can_repair(
    client,
    member_user: User,
    asset: Asset,
    stored_timezone: str,
) -> None:
    User.objects.filter(id=member_user.id).update(timezone=stored_timezone)
    member_user.refresh_from_db()
    client.force_login(member_user)

    protected_paths = [
        "/",
        "/assets/",
        reverse("web:asset-detail", args=[asset.id]),
        reverse("web:reserve", args=[asset.id]),
        "/reservations/",
    ]
    for path in protected_paths:
        response = client.get(path, follow=True)
        assert response.status_code == 200
        assert response.redirect_chain[-1] == (reverse("web:profile"), 302)
        assert b"Traceback" not in response.content
        assert b"Times shown in Europe/Ljubljana" not in response.content
        assert b"Times shown in UTC" not in response.content

    response = client.get("/profile/")
    assert response.status_code == 200
    assert b"Traceback" not in response.content
    assert b"Times shown in" not in response.content

    response = client.post("/profile/", {"display_name": "Member User", "timezone": "UTC"})
    assert response.status_code == 302
    member_user.refresh_from_db()
    assert member_user.timezone == "UTC"

    response = client.get("/")
    assert response.status_code == 200
    assert b"Times shown in UTC" in response.content


@pytest.mark.django_db
def test_valid_non_default_timezone_is_visible_and_distinct_from_asset_timezone(
    client,
    member_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    member_user.timezone = "America/New_York"
    member_user.save(update_fields=["timezone"])
    start = (timezone.now() + timedelta(days=1)).replace(hour=15, minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=1)
    reservation = _direct_reservation(asset=asset, user=member_user, start=start, end=end)
    client.force_login(member_user)
    visible_start = start.astimezone(ZoneInfo(member_user.timezone)).strftime("%Y-%m-%d %H:%M")
    display_date = start.astimezone(ZoneInfo(member_user.timezone)).date().isoformat()

    response = client.get("/")
    content = response.content.decode()
    assert response.status_code == 200
    assert "Times shown in America/New_York" in content
    assert visible_start in content
    assert f'datetime="{start.isoformat().replace("+00:00", "Z")}"' in content

    response = client.get(
        reverse("web:asset-detail", args=[asset.id]),
        {"date": display_date},
    )
    content = response.content.decode()
    assert response.status_code == 200
    assert "Times shown in America/New_York" in content
    assert "Visible availability intervals use America/New_York" in content
    assert "Asset timezone" in content
    assert "Europe/Ljubljana" in content
    assert (
        str(reservation.id)
        in client.get(reverse("web:reservation-detail", args=[reservation.id])).content.decode()
    )


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

    for path in member_paths[1:]:
        assert client.get(path).status_code == 302
    # The root is the public landing for anonymous visitors; member
    # accounts are still dispatched to the dashboard.
    assert client.get("/").status_code == 200

    client.force_login(member_user)
    for path in member_paths:
        assert client.get(path).status_code == 200

    client.force_login(inactive_user)
    assert client.get("/").status_code == 302


@pytest.mark.django_db
def test_upcoming_reservations_are_chronological_and_owner_bounded(
    client,
    member_user: User,
    other_user: User,
    asset: Asset,
) -> None:
    base = (timezone.now() + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    reservations = [
        _direct_reservation(
            asset=asset,
            user=member_user,
            start=base + timedelta(days=index),
            end=base + timedelta(days=index, hours=1),
        )
        for index in reversed(range(12))
    ]
    reservations.sort(key=lambda reservation: reservation.start_at)
    other = _direct_reservation(
        asset=asset,
        user=other_user,
        start=base - timedelta(hours=2),
        end=base - timedelta(hours=1),
    )
    client.force_login(member_user)

    dashboard_response = client.get("/")
    dashboard_content = dashboard_response.content.decode()
    assert dashboard_response.status_code == 200
    _assert_in_order(dashboard_content, [str(reservation.id) for reservation in reservations[:5]])
    assert str(reservations[5].id) not in dashboard_content
    assert str(other.id) not in dashboard_content

    first_page_response = client.get("/reservations/")
    first_page_content = first_page_response.content.decode()
    assert first_page_response.status_code == 200
    _assert_in_order(first_page_content, [str(reservation.id) for reservation in reservations[:10]])
    assert str(reservations[10].id) not in first_page_content
    assert str(other.id) not in first_page_content

    second_page_response = client.get("/reservations/", {"upcoming_page": 2})
    second_page_content = second_page_response.content.decode()
    assert second_page_response.status_code == 200
    _assert_in_order(
        second_page_content,
        [str(reservation.id) for reservation in reservations[10:]],
    )
    assert str(reservations[0].id) not in second_page_content
    assert str(other.id) not in second_page_content


@pytest.mark.django_db
def test_reservation_list_uses_bounded_database_pages(
    client,
    member_user: User,
    other_user: User,
    asset: Asset,
) -> None:
    base = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)
    completed = [
        _direct_reservation(
            asset=asset,
            user=member_user,
            start=base + timedelta(days=index),
            end=base + timedelta(days=index, hours=1),
        )
        for index in range(31)
    ]
    cancelled = [
        _direct_reservation(
            asset=asset,
            user=member_user,
            start=base + timedelta(days=60 + index),
            end=base + timedelta(days=60 + index, hours=1),
            status=Reservation.STATUS_CANCELLED,
            cancelled_by=member_user,
        )
        for index in range(31)
    ]
    released = [
        _direct_reservation(
            asset=asset,
            user=member_user,
            start=base + timedelta(days=120 + index),
            end=base + timedelta(days=120 + index, hours=2),
            status=Reservation.STATUS_RELEASED,
            released_at=base + timedelta(days=120 + index, hours=1),
        )
        for index in range(31)
    ]
    other = _direct_reservation(
        asset=asset,
        user=other_user,
        start=base + timedelta(days=220),
        end=base + timedelta(days=220, hours=1),
        status=Reservation.STATUS_CANCELLED,
        cancelled_by=other_user,
    )
    client.force_login(member_user)

    with CaptureQueriesContext(connection) as queries:
        response = client.get("/reservations/")

    assert response.status_code == 200
    content = response.content.decode()
    assert str(cancelled[-1].id) in content
    assert str(cancelled[0].id) not in content
    assert str(released[-1].id) in content
    assert str(released[0].id) not in content
    assert str(completed[-1].id) in content
    assert str(completed[0].id) not in content
    assert str(other.id) not in content
    paged_sql = [query["sql"] for query in queries]
    assert any("LIMIT 25" in sql for sql in paged_sql)
    assert not any("LIMIT 31" in sql or "LIMIT 32" in sql for sql in paged_sql)

    response = client.get("/reservations/", {"cancelled_page": 2, "released_page": 2})
    content = response.content.decode()
    assert str(cancelled[0].id) in content
    assert str(released[0].id) in content


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
def test_availability_local_day_boundaries_are_explicit_and_safe(
    client,
    member_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    normal = availability_for_asset(
        asset=asset,
        principal=member_user,
        start_date=date(2026, 1, 5),
        days=1,
        display_timezone="Europe/Ljubljana",
        now=datetime(2026, 1, 4, 8, 0, tzinfo=UTC),
    )
    assert normal.end - normal.start == timedelta(hours=24)

    spring = availability_for_asset(
        asset=asset,
        principal=member_user,
        start_date=date(2026, 3, 29),
        days=1,
        display_timezone="Europe/Ljubljana",
        now=datetime(2026, 3, 28, 8, 0, tzinfo=UTC),
    )
    assert spring.end - spring.start == timedelta(hours=23)

    autumn = availability_for_asset(
        asset=asset,
        principal=member_user,
        start_date=date(2026, 10, 25),
        days=1,
        display_timezone="Europe/Ljubljana",
        now=datetime(2026, 10, 24, 8, 0, tzinfo=UTC),
    )
    assert autumn.end - autumn.start == timedelta(hours=25)

    with pytest.raises(AvailabilityInputError):
        availability_for_asset(
            asset=asset,
            principal=member_user,
            start_date=date(2011, 12, 30),
            days=1,
            display_timezone="Pacific/Apia",
            now=datetime(2011, 12, 29, 8, 0, tzinfo=UTC),
        )

    member_user.timezone = "Pacific/Apia"
    member_user.save(update_fields=["timezone"])
    client.force_login(member_user)
    response = client.get(reverse("web:asset-detail", args=[asset.id]), {"date": "2011-12-30"})
    assert response.status_code == 400
    assert response.content == b"Invalid availability date."


@pytest.mark.django_db
def test_availability_busy_free_rules_are_exact_and_private(
    member_user: User,
    other_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    policy.min_duration_minutes = 60
    setattr(policy, SERVICE_UPDATE_ATTR, True)
    policy.save()

    _direct_reservation(
        asset=asset,
        user=other_user,
        start=_local_utc(datetime(2026, 1, 4, 23, 0)),
        end=_local_utc(datetime(2026, 1, 5, 1, 0)),
        purpose="other private purpose",
    )
    _direct_reservation(
        asset=asset,
        user=other_user,
        start=_local_utc(datetime(2026, 1, 5, 2, 0)),
        end=_local_utc(datetime(2026, 1, 5, 5, 0)),
        status=Reservation.STATUS_RELEASED,
        released_at=_local_utc(datetime(2026, 1, 5, 3, 0)),
        purpose="released private purpose",
    )
    _direct_reservation(
        asset=asset,
        user=other_user,
        start=_local_utc(datetime(2026, 1, 5, 3, 15)),
        end=_local_utc(datetime(2026, 1, 5, 3, 45)),
        status=Reservation.STATUS_CANCELLED,
        cancelled_by=other_user,
        purpose="cancelled private purpose",
    )
    _direct_reservation(
        asset=asset,
        user=other_user,
        start=_local_utc(datetime(2026, 1, 5, 8, 0)),
        end=_local_utc(datetime(2026, 1, 5, 9, 0)),
    )
    _direct_reservation(
        asset=asset,
        user=other_user,
        start=_local_utc(datetime(2026, 1, 5, 9, 0)),
        end=_local_utc(datetime(2026, 1, 5, 10, 0)),
    )
    _direct_reservation(
        asset=asset,
        user=other_user,
        start=_local_utc(datetime(2026, 1, 5, 23, 0)),
        end=_local_utc(datetime(2026, 1, 6, 2, 0)),
    )

    result = availability_for_asset(
        asset=asset,
        principal=member_user,
        start_date=date(2026, 1, 5),
        days=1,
        display_timezone="Europe/Ljubljana",
        now=_local_utc(datetime(2026, 1, 4, 0, 0)),
    )

    assert [(item.start, item.end) for item in result.busy] == [
        (_local_utc(datetime(2026, 1, 5, 0, 0)), _local_utc(datetime(2026, 1, 5, 1, 0))),
        (_local_utc(datetime(2026, 1, 5, 2, 0)), _local_utc(datetime(2026, 1, 5, 3, 0))),
        (_local_utc(datetime(2026, 1, 5, 8, 0)), _local_utc(datetime(2026, 1, 5, 10, 0))),
        (_local_utc(datetime(2026, 1, 5, 23, 0)), _local_utc(datetime(2026, 1, 6, 0, 0))),
    ]
    assert [(item.start, item.end) for item in result.free] == [
        (_local_utc(datetime(2026, 1, 5, 1, 0)), _local_utc(datetime(2026, 1, 5, 2, 0))),
        (_local_utc(datetime(2026, 1, 5, 3, 0)), _local_utc(datetime(2026, 1, 5, 8, 0))),
        (_local_utc(datetime(2026, 1, 5, 10, 0)), _local_utc(datetime(2026, 1, 5, 23, 0))),
    ]
    serialized = repr(result)
    assert other_user.email not in serialized
    assert "other private purpose" not in serialized
    assert "cancelled private purpose" not in serialized
    assert "private cancellation text" not in serialized
    assert all(item.reservation_id is None for item in result.busy)


@pytest.mark.django_db
def test_availability_min_duration_and_inclusive_policy_boundaries(
    member_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    policy.min_duration_minutes = 60
    policy.booking_horizon_days = 0
    policy.min_lead_minutes = 0
    setattr(policy, SERVICE_UPDATE_ATTR, True)
    policy.save()

    result = availability_for_asset(
        asset=asset,
        principal=member_user,
        start_date=date(2026, 1, 5),
        days=1,
        display_timezone="Europe/Ljubljana",
        now=_local_utc(datetime(2026, 1, 5, 0, 0)),
    )
    assert len(result.free) == 1
    assert result.free[0].start == _local_utc(datetime(2026, 1, 5, 0, 0))
    assert result.free[0].latest_start == _local_utc(datetime(2026, 1, 5, 0, 0))

    _direct_reservation(
        asset=asset,
        user=member_user,
        start=_local_utc(datetime(2026, 1, 5, 0, 30)),
        end=_local_utc(datetime(2026, 1, 6, 0, 0)),
    )
    result = availability_for_asset(
        asset=asset,
        principal=member_user,
        start_date=date(2026, 1, 5),
        days=1,
        display_timezone="Europe/Ljubljana",
        now=_local_utc(datetime(2026, 1, 5, 0, 0)),
    )
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
def test_staff_member_routes_cannot_access_or_mutate_other_user_reservations(
    client,
    staff_user: User,
    other_user: User,
    asset: Asset,
) -> None:
    future_start, future_end = _future_pair(8)
    future = _direct_reservation(
        asset=asset,
        user=other_user,
        start=future_start,
        end=future_end,
    )
    active = _direct_reservation(
        asset=asset,
        user=other_user,
        start=timezone.now() - timedelta(hours=1),
        end=timezone.now() + timedelta(hours=1),
    )
    client.force_login(staff_user)

    assert client.get(reverse("web:reservation-detail", args=[future.id])).status_code == 404
    assert client.post(reverse("web:reservation-cancel", args=[future.id])).status_code == 404
    assert client.post(reverse("web:reservation-release", args=[active.id])).status_code == 404

    future.refresh_from_db()
    active.refresh_from_db()
    assert future.status == Reservation.STATUS_CONFIRMED
    assert active.status == Reservation.STATUS_CONFIRMED
    assert future.cancelled_at is None
    assert active.released_at is None


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
def test_api_root_exposes_reservation_api_without_changing_human_routes(client) -> None:
    response = client.get("/api/v1/")

    assert response.status_code == 200
    assert response.json()["endpoints"]["reservations"] == "/api/v1/reservations/"
    assert response.json()["endpoints"]["me"] == "/api/v1/me/"
    assert "tokens" not in response.json()["endpoints"]


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
def test_time_markup_is_utc_while_visible_text_is_local(
    client,
    member_user: User,
    other_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    member_user.timezone = "Europe/Ljubljana"
    member_user.save(update_fields=["timezone"])
    start = (timezone.now() + timedelta(days=1)).replace(second=0, microsecond=0)
    end = start + timedelta(hours=1)
    reservation = _direct_reservation(asset=asset, user=member_user, start=start, end=end)
    _direct_reservation(
        asset=asset,
        user=other_user,
        start=end + timedelta(hours=1),
        end=end + timedelta(hours=2),
    )
    client.force_login(member_user)
    visible_start = start.astimezone(ZoneInfo(member_user.timezone)).strftime("%Y-%m-%d %H:%M")
    utc_start = start.astimezone(UTC).isoformat().replace("+00:00", "Z")
    other_visible_start = (
        (end + timedelta(hours=1))
        .astimezone(ZoneInfo(member_user.timezone))
        .strftime("%Y-%m-%d %H:%M")
    )
    other_utc_start = (end + timedelta(hours=1)).astimezone(UTC).isoformat().replace("+00:00", "Z")

    for path in ["/", "/reservations/", reverse("web:reservation-detail", args=[reservation.id])]:
        response = client.get(path)
        content = response.content.decode()
        assert response.status_code == 200
        assert visible_start in content
        assert f'datetime="{utc_start}"' in content

    response = client.get(
        reverse("web:asset-detail", args=[asset.id]),
        {"date": start.astimezone(ZoneInfo(member_user.timezone)).date().isoformat()},
    )
    content = response.content.decode()
    assert response.status_code == 200
    assert other_visible_start in content
    assert f'datetime="{other_utc_start}"' in content


@pytest.mark.django_db
def test_csrf_required_for_state_changing_forms(
    member_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    login_client = Client(enforce_csrf_checks=True)
    assert (
        login_client.post(
            "/login/",
            {"username": member_user.email, "password": "not-a-secret"},
        ).status_code
        == 403
    )
    token = _csrf_token(login_client, "/login/")
    assert (
        login_client.post(
            "/login/",
            {
                "username": member_user.email,
                "password": "not-a-secret",
                "csrfmiddlewaretoken": token,
            },
        ).status_code
        == 302
    )

    client = Client(enforce_csrf_checks=True)
    client.force_login(member_user)
    assert client.post("/logout/").status_code == 403
    token = _csrf_token(client, "/")
    assert client.post("/logout/", {"csrfmiddlewaretoken": token}).status_code == 302

    client = Client(enforce_csrf_checks=True)
    client.force_login(member_user)
    assert (
        client.post("/profile/", {"display_name": "Blocked", "timezone": "UTC"}).status_code == 403
    )
    member_user.refresh_from_db()
    assert member_user.display_name == "Member User"
    token = _csrf_token(client, "/profile/")
    assert (
        client.post(
            "/profile/",
            {"display_name": "Allowed", "timezone": "UTC", "csrfmiddlewaretoken": token},
        ).status_code
        == 302
    )

    client = Client(enforce_csrf_checks=True)
    client.force_login(member_user)
    start, end = _future_pair(5)
    data = {
        "start": start.astimezone(ZoneInfo(member_user.timezone)).strftime("%Y-%m-%dT%H:%M"),
        "end": end.astimezone(ZoneInfo(member_user.timezone)).strftime("%Y-%m-%dT%H:%M"),
        "purpose": "csrf",
    }
    assert client.post(reverse("web:reserve", args=[asset.id]), data).status_code == 403
    assert not Reservation.objects.filter(purpose="csrf").exists()
    token = _csrf_token(client, reverse("web:reserve", args=[asset.id]))
    assert (
        client.post(
            reverse("web:reserve", args=[asset.id]),
            {**data, "csrfmiddlewaretoken": token},
        ).status_code
        == 302
    )

    future = Reservation.objects.get(purpose="csrf")
    client = Client(enforce_csrf_checks=True)
    client.force_login(member_user)
    assert client.post(reverse("web:reservation-cancel", args=[future.id])).status_code == 403
    future.refresh_from_db()
    assert future.status == Reservation.STATUS_CONFIRMED
    token = _csrf_token(client, reverse("web:reservation-detail", args=[future.id]))
    assert (
        client.post(
            reverse("web:reservation-cancel", args=[future.id]),
            {"csrfmiddlewaretoken": token},
        ).status_code
        == 302
    )

    active = _direct_reservation(
        asset=asset,
        user=member_user,
        start=timezone.now() - timedelta(hours=1),
        end=timezone.now() + timedelta(hours=1),
        purpose="release csrf",
    )
    client = Client(enforce_csrf_checks=True)
    client.force_login(member_user)
    assert client.post(reverse("web:reservation-release", args=[active.id])).status_code == 403
    active.refresh_from_db()
    assert active.status == Reservation.STATUS_CONFIRMED
    token = _csrf_token(client, reverse("web:reservation-detail", args=[active.id]))
    assert (
        client.post(
            reverse("web:reservation-release", args=[active.id]),
            {"csrfmiddlewaretoken": token},
        ).status_code
        == 302
    )


@pytest.mark.django_db
def test_get_action_routes_do_not_mutate(
    client,
    member_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    future_start, future_end = _future_pair(6)
    future = _direct_reservation(asset=asset, user=member_user, start=future_start, end=future_end)
    active = _direct_reservation(
        asset=asset,
        user=member_user,
        start=timezone.now() - timedelta(hours=2),
        end=timezone.now() - timedelta(hours=1),
        status=Reservation.STATUS_CANCELLED,
        cancelled_by=member_user,
    )
    client.force_login(member_user)

    assert client.get("/logout/").status_code == 405
    assert "_auth_user_id" in client.session
    assert client.get(reverse("web:reservation-cancel", args=[future.id])).status_code == 405
    assert client.get(reverse("web:reservation-release", args=[active.id])).status_code == 405
    future.refresh_from_db()
    active.refresh_from_db()
    assert future.status == Reservation.STATUS_CONFIRMED
    assert active.status == Reservation.STATUS_CANCELLED


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
