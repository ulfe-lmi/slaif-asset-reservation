"""Integrated pilot path — member browser surface (scope item 1).

Proves the pilot member journey through the real browser adapter:
real form login/CSRF, live_server, transaction=True, reusing the fixture
conventions of ``tests/browser/test_human_mvp_browser.py``.

Scope 1a: member logs in, browses assets (reservable GPU child visible,
non-reservable parent not bookable), opens availability, creates a
reservation in a future policy-valid window with local time values, and
sees it in the own list (soonest-first) and on the detail page with
correct local display.

Scope 1b: the member then exercises the lifecycle action the service
permits for the created reservation through the real form. A freshly
created future reservation is UPCOMING: ``release_reservation`` requires
``start_at < now < effective_end_at`` (an ACTIVE window), so the only
permitted lifecycle action is cancellation, and the detail page renders
only the cancel form for the UPCOMING lifecycle.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset, AssetTag
from slaif_reservation.reservations.models import Reservation, ReservationPolicy


@pytest.fixture
def pilot_member() -> User:
    return User.objects.create_user(
        email="pilot-member@example.com",
        password="not-a-secret",
        display_name="Pilot Member",
        timezone="Europe/Ljubljana",
    )


@pytest.fixture
def pilot_machine() -> Asset:
    return Asset.objects.create(
        slug="pilot-machine",
        name="Pilot Machine",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
        verification_required=False,
    )


@pytest.fixture
def pilot_asset(pilot_machine: Asset) -> Asset:
    asset = Asset.objects.create(
        slug="pilot-gpu",
        name="Pilot GPU",
        kind=Asset.KIND_GPU,
        parent=pilot_machine,
        active=True,
        reservable=True,
        verification_required=True,
    )
    tag = AssetTag.objects.create(slug="pilot-tag", name="Pilot Tag")
    asset.tags.add(tag)
    return asset


@pytest.fixture
def pilot_policy(pilot_asset: Asset) -> ReservationPolicy:
    return ReservationPolicy.objects.create(
        name="Pilot policy",
        asset=pilot_asset,
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


def _local(value: datetime, user: User) -> str:
    return value.astimezone(ZoneInfo(user.timezone)).strftime("%Y-%m-%dT%H:%M")


def _local_display(value: datetime, user: User) -> str:
    return value.astimezone(ZoneInfo(user.timezone)).strftime("%Y-%m-%d %H:%M")


def _window(days: int, hour: int = 8) -> tuple[datetime, datetime]:
    start = (timezone.now() + timedelta(days=days)).replace(
        hour=hour, minute=0, second=0, microsecond=0
    )
    return start, start + timedelta(hours=1)


def _book_via_form(
    page,
    live_server,
    user: User,
    asset: Asset,
    start: datetime,
    end: datetime,
    purpose: str,
    **query: str,
) -> None:
    url = f"{live_server.url}/assets/{asset.id}/reserve/"
    if query:
        url += "?" + "&".join(f"{key}={value}" for key, value in query.items())
    page.goto(url)
    page.locator("#id_start").fill(_local(start, user))
    page.locator("#id_end").fill(_local(end, user))
    page.get_by_label("Purpose").fill(purpose)
    page.get_by_role("button", name="Create reservation").click()


@pytest.mark.django_db(transaction=True)
def test_pilot_browser_member_books_and_sees_own_reservation(
    page,
    live_server,
    pilot_member: User,
    pilot_machine: Asset,
    pilot_asset: Asset,
    pilot_policy: ReservationPolicy,
) -> None:
    _login(page, live_server, pilot_member)

    # 1a — browse assets: reservable GPU child visible.
    page.goto(f"{live_server.url}/assets/")
    assert "Pilot GPU" in page.content()

    # 1a — non-reservable parent is not bookable.
    page.goto(f"{live_server.url}/assets/{pilot_machine.id}/")
    machine_content = page.content()
    assert "Reserve this asset" not in machine_content
    assert "This asset is not reservable." in machine_content

    # 1a — opens availability for the GPU.
    page.goto(f"{live_server.url}/assets/{pilot_asset.id}/")
    asset_content = page.content()
    assert "Reserve this asset" in asset_content
    assert "No busy intervals in this window." in asset_content
    assert "Free intervals" in asset_content

    # 1a — creates a reservation in a future policy-valid window using
    # local time values, then a second (earlier) one for ordering.
    later_start, later_end = _window(3)
    earlier_start, earlier_end = _window(2)
    _book_via_form(
        page, live_server, pilot_member, pilot_asset, later_start, later_end, "Pilot later window"
    )
    page.wait_for_url("**/reservations/**/")
    assert "Reservation created" in page.content()
    later = Reservation.objects.get(start_at=later_start)
    assert later.requested_by_user == pilot_member
    _book_via_form(
        page,
        live_server,
        pilot_member,
        pilot_asset,
        earlier_start,
        earlier_end,
        "Pilot earlier window",
    )
    page.wait_for_url("**/reservations/**/")
    assert "Reservation created" in page.content()
    earlier = Reservation.objects.get(start_at=earlier_start)
    assert Reservation.objects.count() == 2

    # 1a — own list, soonest-first: the earlier reservation precedes the later one.
    page.goto(f"{live_server.url}/reservations/")
    content = page.content()
    assert "Upcoming" in content
    assert f"/reservations/{earlier.id}/" in content
    assert f"/reservations/{later.id}/" in content
    assert content.index(f"/reservations/{earlier.id}/") < content.index(
        f"/reservations/{later.id}/"
    )

    # 1a — detail page with correct local display.
    page.goto(f"{live_server.url}/reservations/{later.id}/")
    detail = page.content()
    assert _local_display(later_start, pilot_member) in detail
    assert _local_display(later_end, pilot_member) in detail
    assert "Pilot later window" in detail
    assert "Europe/Ljubljana" in detail


@pytest.mark.django_db(transaction=True)
def test_pilot_browser_member_cancels_upcoming_via_real_form(
    page,
    live_server,
    pilot_member: User,
    pilot_asset: Asset,
    pilot_policy: ReservationPolicy,
) -> None:
    start, end = _window(2)
    _login(page, live_server, pilot_member)
    _book_via_form(page, live_server, pilot_member, pilot_asset, start, end, "Pilot cancel me")
    page.wait_for_url("**/reservations/**/")
    assert "Reservation created" in page.content()
    reservation = Reservation.objects.get(requested_by_user=pilot_member)

    # UPCOMING lifecycle: only cancellation is offered (release requires an
    # ACTIVE window with start_at < now < effective_end_at).
    page.goto(f"{live_server.url}/reservations/{reservation.id}/")
    assert "Upcoming" in page.content()
    assert page.get_by_role("button", name="Cancel reservation").count() == 1
    assert page.get_by_role("button", name="Release reservation").count() == 0

    page.get_by_label("Reason").fill("Pilot cancel reason")
    with page.expect_navigation():
        page.get_by_role("button", name="Cancel reservation").click()
    assert "Reservation cancelled" in page.content()
    assert "Cancelled" in page.content()
    assert "Cancelled at" in page.content()

    reservation.refresh_from_db()
    assert reservation.status == Reservation.STATUS_CANCELLED
    assert reservation.cancelled_by_id == pilot_member.id
    assert reservation.cancellation_reason == "Pilot cancel reason"
    assert reservation.effective_end_at == reservation.end_at

    # The cancelled window no longer blocks availability.
    page.goto(f"{live_server.url}/assets/{pilot_asset.id}/")
    assert "No busy intervals in this window." in page.content()
