"""Focused Chromium evidence for the read-only asset calendar (order 054-a).

Real HTTP against real PostgreSQL with a Chromium browser: the authorized
one/four-week desktop and 390px mobile flows (asset-detail entry link,
confirmed/released/cancelled rendering, previous/next/this-week navigation,
view-length switching, owner and detail links), the vertical mobile day
layout without horizontal overflow, privacy denials for staff-without-grant
and anonymous callers, and no visible framework branding. Exactly four
privacy-safe screenshots are captured and retained: 1440 one-week, 1440
four-week, 390 one-week and 390 four-week.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from playwright.sync_api import Page

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset
from slaif_reservation.reservations.models import Reservation

BRANDING = "SLAIF Asset Reservation"
FRAMEWORK_MARKERS = (
    "Django",
    "Django REST framework",
    "Django administration",
    "Django site admin",
    "Powered by Django",
)

DESKTOP = {"width": 1440, "height": 900}
MOBILE = {"width": 390, "height": 844}
DISPLAY_TZ = ZoneInfo("Europe/Ljubljana")
VIEWER_EMAIL = "cal-browser-viewer@example.com"
OWNER_EMAIL = "cal-browser-owner@example.com"
OWNER_NAME = "Browser Calendar Owner"


def _login(page: Page, live_server, user: User) -> None:
    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Email").fill(user.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/")


def _assert_no_framework_branding(page: Page) -> None:
    for marker in FRAMEWORK_MARKERS:
        assert marker not in page.content(), marker
        assert marker not in page.title()


def _assert_no_horizontal_overflow(page: Page) -> None:
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), (
        "horizontal page overflow"
    )


def _screenshot(page: Page, output_path, name: str) -> None:
    page.screenshot(path=f"{output_path}/{name}.png")


def _make_user(email: str, display_name: str, **extra: object) -> User:
    return User.objects.create_user(
        email=email, password="not-a-secret", display_name=display_name, **extra
    )


def _grant(user: User, codenames: list[str]) -> User:
    user.user_permissions.add(
        *Permission.objects.filter(
            codename__in=list(codenames), content_type__app_label="reservations"
        )
    )
    return user


def _local(y: int, mo: int, d: int, h: int, mi: int = 0) -> datetime:
    return datetime(y, mo, d, h, mi, tzinfo=DISPLAY_TZ).astimezone(UTC)


def _make_reservation(
    user: User,
    asset: Asset,
    start: datetime,
    end: datetime,
    *,
    status: str = Reservation.STATUS_CONFIRMED,
    effective_end: datetime | None = None,
) -> Reservation:
    effective = effective_end or end
    return Reservation.objects.create(
        asset=asset,
        requested_by_user=user,
        source=Reservation.SOURCE_WEB,
        status=status,
        start_at=start,
        end_at=end,
        effective_end_at=effective,
        released_at=(effective if status == Reservation.STATUS_RELEASED else None),
        cancelled_at=(
            start + timedelta(minutes=5) if status == Reservation.STATUS_CANCELLED else None
        ),
        cancelled_by=user if status == Reservation.STATUS_CANCELLED else None,
        cancellation_reason="" if status != Reservation.STATUS_CANCELLED else "gone",
    )


@pytest.fixture
def machine() -> Asset:
    return Asset.objects.create(
        slug="calbrowser-machine",
        name="CalBrowser Machine",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
        verification_required=False,
    )


@pytest.fixture
def asset(machine: Asset) -> Asset:
    return Asset.objects.create(
        slug="calbrowser-gpu",
        name="CalBrowser GPU",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
        verification_required=False,
    )


@pytest.fixture
def viewer() -> User:
    return _grant(
        _make_user(VIEWER_EMAIL, "Browser Calendar Viewer", timezone="Europe/Ljubljana"),
        ["view_all_reservations"],
    )


@pytest.fixture
def staff_only() -> User:
    return _make_user(
        "calbrowser-staffonly@example.com",
        "Browser Staff Only",
        timezone="Europe/Ljubljana",
        is_staff=True,
    )


@pytest.fixture
def owner() -> User:
    return _make_user(OWNER_EMAIL, OWNER_NAME, timezone="Europe/Ljubljana")


@pytest.fixture
def week_data(asset: Asset, owner: User) -> dict[str, object]:
    """One confirmed, one released and one cancelled interval, all on the
    Thursday/Tuesday of the viewer's current local week."""
    from django.utils import timezone as django_timezone

    now_local = django_timezone.now().astimezone(DISPLAY_TZ)
    monday_local = now_local - timedelta(days=now_local.weekday())

    def at(day_offset: int, hour: int, minute: int = 0) -> datetime:
        base = monday_local + timedelta(days=day_offset)
        return _local(base.year, base.month, base.day, hour, minute)

    confirmed = _make_reservation(owner, asset, at(3, 14), at(3, 16))
    released = _make_reservation(
        owner,
        asset,
        at(1, 10),
        at(1, 18),
        status=Reservation.STATUS_RELEASED,
        effective_end=at(1, 12),
    )
    cancelled = _make_reservation(
        owner,
        asset,
        at(3, 15, 30),
        at(3, 17),
        status=Reservation.STATUS_CANCELLED,
    )
    return {
        "monday": monday_local.date(),
        "confirmed": confirmed,
        "released": released,
        "cancelled": cancelled,
        "thursday_heading": (monday_local + timedelta(days=3)).strftime("%A %d %b %Y"),
        "tuesday_heading": (monday_local + timedelta(days=1)).strftime("%A %d %b %Y"),
    }


@pytest.mark.django_db(transaction=True)
def test_desktop_one_and_four_week_flows(
    page: Page, live_server, output_path, viewer: User, asset: Asset, week_data: dict
) -> None:
    page.set_viewport_size(DESKTOP)
    _login(page, live_server, viewer)

    # Entry point from the member asset detail: only granted users see it.
    page.goto(f"{live_server.url}{reverse('web:asset-detail', args=[asset.id])}")
    page.get_by_role("link", name=re.compile("Reservation calendar")).click()
    page.wait_for_url(lambda url: "/manage/reservations/calendar/" in url)

    assert page.get_by_role("heading", name="Calendar: CalBrowser GPU", exact=True).is_visible()
    assert BRANDING in page.title()
    assert "Times shown in Europe/Ljubljana." in page.inner_text("header")

    content = page.inner_text("#content")
    # Calendar-versus-history explanation and legend are present.
    assert "Cancelled reservations never appear here" in content
    assert "Confirmed (blocks the asset)" in content
    assert "Released (consumed time)" in content
    # Seven Monday-Sunday day headings for the current local week.
    assert page.locator(".calendar-day-heading").count() == 7
    thursday = page.locator(
        ".calendar-day",
        has=page.get_by_role("heading", name=week_data["thursday_heading"]),
    )
    thursday_text = thursday.inner_text()
    assert "14:00 - 16:00" in thursday_text
    assert OWNER_NAME in thursday_text
    # The cancelled interval (15:30 - 17:00) must not appear.
    assert "15:30 - 17:00" not in content
    tuesday = page.locator(
        ".calendar-day", has=page.get_by_role("heading", name=week_data["tuesday_heading"])
    )
    tuesday_text = tuesday.inner_text()
    assert "10:00 - 12:00" in tuesday_text
    # The status badge renders upper-cased through CSS text-transform.
    assert "RELEASED" in tuesday_text
    # Owner email is not disclosed on the calendar (display name only).
    assert OWNER_EMAIL not in page.content()

    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "reservation-calendar-1440-1week")

    # Chip links to the protected read-only detail.
    confirmed = week_data["confirmed"]
    thursday.get_by_role("link", name=re.compile("14:00 - 16:00")).click()
    page.wait_for_url(lambda url: f"/manage/reservations/{confirmed.id}/" in url)
    assert str(confirmed.id) in page.content()
    page.go_back()
    page.wait_for_url(lambda url: "/manage/reservations/calendar/" in url)

    # Switch to four weeks: the selected week is kept, 28 days render.
    page.get_by_role("link", name="4 weeks").click()
    page.wait_for_url(lambda url: "weeks=4" in url)
    assert page.locator(".calendar-day-heading").count() == 28
    assert "14:00 - 16:00" in page.inner_text("#content")
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "reservation-calendar-1440-4week")

    # Next advances the whole four-week window; This week returns.
    first_before = page.locator(".calendar-day-heading").first.inner_text()
    page.get_by_role("link", name=re.compile("^Next")).click()
    page.wait_for_url(lambda url: "weeks=4" in url)
    first_after = page.locator(".calendar-day-heading").first.inner_text()
    assert first_after != first_before
    assert "14:00 - 16:00" not in page.inner_text("#content")
    page.get_by_role("link", name="This week").click()
    page.wait_for_url(lambda url: "weeks=4" in url)
    assert page.locator(".calendar-day-heading").first.inner_text() == first_before

    # Switch back to one week without losing the selected week.
    page.get_by_role("link", name="1 week").click()
    page.wait_for_url(lambda url: "weeks=1" in url)
    assert page.locator(".calendar-day-heading").count() == 7
    assert "14:00 - 16:00" in page.inner_text("#content")

    # Navigation controls are real keyboard-reachable links.
    for link in page.locator("nav.calendar-controls a").all():
        assert link.get_attribute("href"), "calendar control must be a link"


@pytest.mark.django_db(transaction=True)
def test_mobile_vertical_day_layout(
    page: Page, live_server, output_path, viewer: User, asset: Asset, week_data: dict
) -> None:
    page.set_viewport_size(MOBILE)
    _login(page, live_server, viewer)
    page.goto(f"{live_server.url}{reverse('management-ui:reservation-calendar', args=[asset.id])}")
    page.wait_for_url(lambda url: "/manage/reservations/calendar/" in url)

    # Deliberate vertical day layout: the week grid collapses to block flow.
    week_display = page.evaluate(
        "getComputedStyle(document.querySelector('.calendar-week')).display"
    )
    assert week_display == "block"
    assert page.locator(".calendar-day-heading").count() == 7
    boxes = page.locator(".calendar-day").evaluate_all(
        "els => els.map(el => el.getBoundingClientRect())"
    )
    xs = {round(b["x"], 1) for b in boxes}
    assert len(xs) == 1, f"day cells must stack in one column, got {xs}"
    ys = [b["y"] for b in boxes]
    assert ys == sorted(ys), "day cells must be ordered top to bottom"
    assert "14:00 - 16:00" in page.inner_text("#content")
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "reservation-calendar-390-1week")

    page.get_by_role("link", name="4 weeks").click()
    page.wait_for_url(lambda url: "weeks=4" in url)
    assert page.locator(".calendar-day-heading").count() == 28
    _assert_no_horizontal_overflow(page)
    _screenshot(page, output_path, "reservation-calendar-390-4week")


@pytest.mark.django_db(transaction=True)
def test_privacy_denials_for_unauthorized_callers(
    page: Page,
    live_server,
    viewer: User,
    staff_only: User,
    asset: Asset,
    week_data: dict,
) -> None:
    calendar_path = reverse("management-ui:reservation-calendar", args=[asset.id])
    detail_path = reverse("web:asset-detail", args=[asset.id])

    # Active Staff without the grant: no calendar link, 403 on direct GET,
    # and no owner identity in the response.
    _login(page, live_server, staff_only)
    page.goto(f"{live_server.url}{detail_path}")
    assert page.get_by_role("link", name=re.compile("Reservation calendar")).count() == 0
    page.goto(f"{live_server.url}{calendar_path}")
    assert page.url.endswith(calendar_path)
    assert "restricted" in page.inner_text("body").lower()
    assert OWNER_NAME not in page.content()
    assert OWNER_EMAIL not in page.content()

    # Anonymous callers are redirected to login for the calendar route.
    page.goto(f"{live_server.url}{detail_path}")
    page.get_by_role("button", name="Logout").click()
    page.wait_for_url(lambda url: "/login/" in url)
    page.goto(f"{live_server.url}{calendar_path}")
    page.wait_for_url(lambda url: "/login/" in url)

    # The authorized viewer still reaches the calendar (control check).
    _login(page, live_server, viewer)
    page.goto(f"{live_server.url}{calendar_path}")
    assert "Calendar: CalBrowser GPU" in page.inner_text("h1")
