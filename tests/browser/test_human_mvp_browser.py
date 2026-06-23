from __future__ import annotations

from datetime import timedelta
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset, AssetTag
from slaif_reservation.reservations.models import Reservation, ReservationPolicy
from slaif_reservation.reservations.services import create_reservation


@pytest.fixture
def member_user() -> User:
    return User.objects.create_user(
        email="browser-member@example.com",
        password="not-a-secret",
        timezone="Europe/Ljubljana",
    )


@pytest.fixture
def other_user() -> User:
    return User.objects.create_user(email="browser-other@example.com", password="not-a-secret")


@pytest.fixture
def service_account() -> User:
    return User.objects.create_user(
        email="browser-agent@example.com",
        password="not-a-secret",
        is_service_account=True,
    )


@pytest.fixture
def machine() -> Asset:
    return Asset.objects.create(
        slug="browser-machine",
        name="Browser Machine",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
        verification_required=False,
    )


@pytest.fixture
def asset(machine: Asset) -> Asset:
    asset = Asset.objects.create(
        slug="browser-gpu",
        name="Browser GPU",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
        verification_required=True,
    )
    tag = AssetTag.objects.create(slug="browser-tag", name="Browser Tag")
    asset.tags.add(tag)
    return asset


@pytest.fixture
def second_asset(machine: Asset) -> Asset:
    return Asset.objects.create(
        slug="browser-gpu-two",
        name="Browser GPU Two",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
        verification_required=False,
    )


@pytest.fixture
def policy(asset: Asset) -> ReservationPolicy:
    return ReservationPolicy.objects.create(
        name="Browser policy",
        asset=asset,
        active=True,
        min_duration_minutes=30,
        max_duration_minutes=240,
        booking_horizon_days=30,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=10,
        max_concurrent_per_principal=3,
        purpose_required=False,
    )


@pytest.fixture
def second_policy(second_asset: Asset) -> ReservationPolicy:
    return ReservationPolicy.objects.create(
        name="Browser second policy",
        asset=second_asset,
        active=True,
        min_duration_minutes=30,
        max_duration_minutes=240,
        booking_horizon_days=30,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=10,
        max_concurrent_per_principal=3,
        purpose_required=False,
    )


def _login(page, live_server, user: User) -> None:
    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Email").fill(user.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/")


def _local_value(value, user: User) -> str:
    return value.astimezone(ZoneInfo(user.timezone)).strftime("%Y-%m-%dT%H:%M")


def _future_pair(hours: int = 2):
    start = (timezone.now() + timedelta(days=1, hours=hours)).replace(second=0, microsecond=0)
    return start, start + timedelta(hours=1)


@pytest.mark.django_db(transaction=True)
def test_browser_login_profile_asset_filter_and_post_logout(
    page,
    live_server,
    member_user: User,
    service_account: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Email").fill(service_account.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in").click()
    assert "Enter a valid email address and password" in page.content()

    _login(page, live_server, member_user)
    page.get_by_role("link", name="Profile").click()
    page.get_by_label("Display name").fill("Browser Member")
    page.get_by_label("Timezone").fill("UTC")
    page.get_by_role("button", name="Save profile").click()
    assert "Profile updated" in page.content()

    page.get_by_role("link", name="Assets").click()
    page.get_by_label("Search").fill("Browser")
    page.get_by_label("Tag").select_option("browser-tag")
    page.get_by_role("button", name="Filter").click()
    assert "Browser GPU" in page.content()
    assert "legacy_id" not in page.content()

    page.get_by_role("button", name="Logout").click()
    page.wait_for_url(f"{live_server.url}/login/")


@pytest.mark.django_db(transaction=True)
def test_browser_successful_reservation_creation_and_own_detail(
    page,
    live_server,
    member_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    start, end = _future_pair()
    _login(page, live_server, member_user)
    page.goto(f"{live_server.url}/assets/{asset.id}/reserve/")
    page.locator("#id_start").fill(_local_value(start, member_user))
    page.locator("#id_end").fill(_local_value(end, member_user))
    page.get_by_label("Purpose").fill("Browser reservation")
    page.get_by_role("button", name="Create reservation").click()

    page.wait_for_url("**/reservations/**/")
    assert "Reservation created" in page.content()
    assert "Browser reservation" in page.content()
    assert str(Reservation.objects.get(requested_by_user=member_user).id) in page.content()


@pytest.mark.django_db(transaction=True)
def test_browser_conflict_feedback_preserves_input(
    page,
    live_server,
    member_user: User,
    other_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    start, end = _future_pair(4)
    create_reservation(
        asset=asset,
        requested_by_user=other_user,
        start_at=start,
        end_at=end,
        purpose="private other purpose",
    )
    _login(page, live_server, member_user)
    page.goto(f"{live_server.url}/assets/{asset.id}/reserve/")
    page.locator("#id_start").fill(_local_value(start, member_user))
    page.locator("#id_end").fill(_local_value(end, member_user))
    page.get_by_label("Purpose").fill("Keep this input")
    page.get_by_role("button", name="Create reservation").click()

    content = page.content()
    assert "That time is no longer available" in content
    assert "Keep this input" in content
    assert "private other purpose" not in content
    assert other_user.email not in content


@pytest.mark.django_db(transaction=True)
def test_browser_cancel_release_and_other_user_denial(
    page,
    live_server,
    member_user: User,
    other_user: User,
    asset: Asset,
    second_asset: Asset,
    policy: ReservationPolicy,
    second_policy: ReservationPolicy,
) -> None:
    future_start, future_end = _future_pair(6)
    future = create_reservation(
        asset=asset,
        requested_by_user=member_user,
        start_at=future_start,
        end_at=future_end,
        purpose="cancel me",
    ).reservation
    other = create_reservation(
        asset=asset,
        requested_by_user=other_user,
        start_at=future_end + timedelta(hours=1),
        end_at=future_end + timedelta(hours=2),
        purpose="other",
    ).reservation
    active_end = timezone.now() + timedelta(hours=2)
    active = Reservation.objects.create(
        asset=second_asset,
        requested_by_user=member_user,
        source=Reservation.SOURCE_WEB,
        status=Reservation.STATUS_CONFIRMED,
        start_at=timezone.now() - timedelta(minutes=30),
        end_at=active_end,
        effective_end_at=active_end,
        purpose="release me",
    )

    _login(page, live_server, member_user)
    response = page.goto(f"{live_server.url}/reservations/{other.id}/")
    assert response is not None
    assert response.status == 404

    page.goto(f"{live_server.url}/reservations/{future.id}/")
    with page.expect_navigation():
        page.get_by_role("button", name="Cancel reservation").click()
    assert "Reservation cancelled" in page.content()

    page.goto(f"{live_server.url}/reservations/{active.id}/")
    with page.expect_navigation():
        page.get_by_role("button", name="Release reservation").click()
    assert "Reservation released" in page.content()


@pytest.mark.django_db(transaction=True)
def test_browser_keyboard_navigation_smoke(
    page,
    live_server,
    member_user: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    _login(page, live_server, member_user)
    page.goto(f"{live_server.url}/")
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    assert page.locator(":focus").count() == 1
