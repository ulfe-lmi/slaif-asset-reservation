"""Order 049-a — browser qualification of booking eligibility (SAR-049).

Focused Chromium checks at 1440 and 390 against real PostgreSQL:

- eligible AND ineligible assets both stay visible in the member list;
  the per-row "You can book" column and the detail "Booking access" line
  show the state, and the Reserve action is offered only to eligible
  members (with a clear, non-private reason otherwise);
- an eligible booking works end-to-end through the form;
- direct requests are denied: GET on the reserve page of an ineligible
  asset redirects with a message, and a forged raw POST (CSRF token from
  the session cookie) creates nothing;
- the admin booking-access fields: generated dual-select help is bound,
  keyboard-reachable, no horizontal overflow, no framework wording;
- default and custom theme both render the eligibility information.

At most two privacy-safe screenshots are captured and viewed in this
fresh context (no tokens, passwords, CSRF values or member metadata).
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth.models import Permission
from django.test import override_settings
from django.utils import timezone
from playwright.sync_api import Page

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset
from slaif_reservation.reservations.models import Reservation, ReservationPolicy

REPO_ROOT = Path(__file__).resolve().parents[2]
CUSTOM_BRANDING = REPO_ROOT / "tests" / "fixtures" / "branding" / "custom"

DESKTOP = {"width": 1440, "height": 900}
MOBILE = {"width": 390, "height": 844}

GROUP_NAME = "Bookers"


# --- fixtures ---------------------------------------------------------------


@pytest.fixture
def member_user() -> User:
    """Active member with the global booking capability but no groups."""
    created = User.objects.create_user(
        email="booking-member@example.com",
        password="not-a-secret",
        display_name="Booking Member",
        timezone="Europe/Ljubljana",
    )
    created.user_permissions.add(
        Permission.objects.get(codename="book_assets", content_type__app_label="reservations")
    )
    return created


@pytest.fixture
def machine() -> Asset:
    return Asset.objects.create(
        slug="booking-machine",
        name="Booking Machine",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
        verification_required=False,
    )


@pytest.fixture
def open_asset(machine: Asset) -> Asset:
    return Asset.objects.create(
        slug="booking-open",
        name="Booking Open GPU",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
        verification_required=False,
    )


@pytest.fixture
def bookers_group() -> object:
    from django.contrib.auth.models import Group

    return Group.objects.create(name=GROUP_NAME)


@pytest.fixture
def restricted_asset(bookers_group: object, machine: Asset) -> Asset:
    asset = Asset.objects.create(
        slug="booking-restricted",
        name="Booking Restricted GPU",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
        verification_required=False,
        booking_restricted=True,
    )
    asset.allowed_booking_groups.add(bookers_group)
    return asset


@pytest.fixture
def global_policy() -> ReservationPolicy:
    return ReservationPolicy.objects.create(
        name="Booking browser global policy",
        asset=None,
        min_duration_minutes=30,
        max_duration_minutes=240,
        booking_horizon_days=30,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=10,
        max_concurrent_per_principal=5,
        purpose_required=False,
    )


@pytest.fixture
def admin_user() -> User:
    return User.objects.create_superuser(
        email="booking-admin@example.com",
        password="not-a-secret",
        display_name="Booking Admin",
    )


@pytest.fixture
def branding_custom():
    with override_settings(BRANDING_DIR=str(CUSTOM_BRANDING)):
        yield


# --- helpers ------------------------------------------------------------------


def _login(page: Page, live_server, user: User) -> None:
    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Email").fill(user.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/")


def _admin_login(page: Page, live_server, user: User) -> None:
    page.goto(f"{live_server.url}/admin/login/")
    page.get_by_label("Email").fill(user.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/admin/")


def _local_value(value, user: User) -> str:
    return value.astimezone(ZoneInfo(user.timezone)).strftime("%Y-%m-%dT%H:%M")


def _future_pair():
    start = (timezone.now() + timedelta(days=1, hours=2)).replace(second=0, microsecond=0)
    return start, start + timedelta(hours=1)


def _row(page: Page, name: str):
    return page.locator("tr", has=page.get_by_role("link", name=name, exact=True))


def _bookable_cell(page: Page, name: str) -> str:
    return _row(page, name).locator("td").nth(4).inner_text()


def _assert_no_horizontal_overflow(page: Page) -> None:
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), (
        "horizontal page overflow"
    )


# --- member surface ------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_member_list_and_detail_show_booking_access(
    page: Page,
    live_server,
    output_path,
    member_user: User,
    open_asset: Asset,
    restricted_asset: Asset,
    global_policy,
) -> None:
    _login(page, live_server, member_user)

    # Default (packaged) identity renders the same information.
    assert page.locator("img.brand-logo").get_attribute("src") == (
        "/static/web/brand/slaif-logo.svg"
    )

    # --- 1440 -----------------------------------------------------------------
    page.goto(f"{live_server.url}/assets/")
    page.set_viewport_size(DESKTOP)
    # Both assets remain visible regardless of personal eligibility.
    assert _row(page, open_asset.name).count() == 1
    assert _row(page, restricted_asset.name).count() == 1
    # The per-row column distinguishes the states.
    assert _bookable_cell(page, open_asset.name) == "yes"
    assert _bookable_cell(page, restricted_asset.name) == "no"
    # The corrected reservable-filter guidance is about the asset flag.
    assert (
        "not of your personal booking access"
        in page.locator("#filter-reservable-help").inner_text()
    )
    _assert_no_horizontal_overflow(page)

    # Eligible asset: access line + Reserve action offered.
    page.goto(f"{live_server.url}/assets/{open_asset.id}/")
    assert "Booking access" in page.content()
    assert "You can book this asset." in page.content()
    assert page.get_by_role("link", name="Reserve this asset").count() == 1

    # Ineligible asset: clear reason, no Reserve action, no private data.
    page.goto(f"{live_server.url}/assets/{restricted_asset.id}/")
    assert "Restricted to specific approved groups" in page.content()
    assert page.get_by_role("link", name="Reserve this asset").count() == 0
    assert GROUP_NAME not in page.content()
    _assert_no_horizontal_overflow(page)
    # Screenshot 1 of 2: privacy-safe (group name, tokens and member
    # metadata are absent from this view).
    page.screenshot(
        path=f"{output_path}/booking-eligibility-member-detail-1440.png",
        full_page=True,
    )

    # --- 390 ------------------------------------------------------------------
    page.goto(f"{live_server.url}/assets/")
    page.set_viewport_size(MOBILE)
    assert _bookable_cell(page, open_asset.name) == "yes"
    assert _bookable_cell(page, restricted_asset.name) == "no"
    _assert_no_horizontal_overflow(page)


@pytest.mark.django_db(transaction=True)
def test_member_eligible_booking_works(
    page: Page,
    live_server,
    member_user: User,
    open_asset: Asset,
    global_policy,
) -> None:
    start, end = _future_pair()
    _login(page, live_server, member_user)
    page.goto(f"{live_server.url}/assets/{open_asset.id}/")
    page.set_viewport_size(DESKTOP)
    page.get_by_role("link", name="Reserve this asset").click()
    page.locator("#id_start").fill(_local_value(start, member_user))
    page.locator("#id_end").fill(_local_value(end, member_user))
    page.get_by_label("Purpose").fill("Browser booking")
    page.get_by_role("button", name="Create reservation").click()

    page.wait_for_url("**/reservations/**/")
    assert "Reservation created" in page.content()
    created = Reservation.objects.get(requested_by_user=member_user)
    assert created.asset_id == open_asset.id
    assert str(created.id) in page.content()


@pytest.mark.django_db(transaction=True)
def test_direct_requests_denied_for_ineligible(
    page: Page,
    live_server,
    member_user: User,
    restricted_asset: Asset,
    global_policy,
) -> None:
    start, end = _future_pair()
    _login(page, live_server, member_user)

    # GET on the reserve page is denied by redirect, with the message
    # visible on the returned detail page.
    page.set_viewport_size(DESKTOP)
    page.goto(f"{live_server.url}/assets/{restricted_asset.id}/reserve/")
    page.wait_for_url(f"**/assets/{restricted_asset.id}/")
    assert "members of specific approved groups" in page.content()
    assert "not currently one of them" in page.content()
    assert Reservation.objects.count() == 0

    # Forged direct POST (the form is not even offered to this member):
    # a REAL form-encoded request carrying the valid existing session CSRF
    # token (cookie + csrftoken form field), with a valid reservation
    # payload; nothing is created.
    cookie = next(c for c in page.context.cookies() if c["name"] == "csrftoken")
    response = page.request.post(
        f"{live_server.url}/assets/{restricted_asset.id}/reserve/",
        form={
            "csrfmiddlewaretoken": cookie["value"],
            "start": _local_value(start, member_user),
            "end": _local_value(end, member_user),
            "duration": "custom",
            "purpose": "forged",
        },
    )
    assert response.status == 200
    body = response.text()
    assert "members of specific approved groups" in body
    assert "not currently one of them" in body
    assert "Reservation created" not in body
    assert Reservation.objects.count() == 0


# --- admin surface ---------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_admin_booking_access_controls(
    page: Page,
    live_server,
    output_path,
    admin_user: User,
    restricted_asset: Asset,
    global_policy,
) -> None:
    _admin_login(page, live_server, admin_user)
    page.goto(f"{live_server.url}/admin/assets/asset/{restricted_asset.pk}/change/")

    # --- 1440 -----------------------------------------------------------------
    page.set_viewport_size(DESKTOP)
    for suffix in ("_from", "_to"):
        page.wait_for_function(
            r"""(sel) => {
                const el = document.querySelector(sel);
                const h = document.getElementById("id_allowed_booking_groups_helptext");
                return !!(el && h && (el.getAttribute("aria-describedby") || "")
                    .split(/\s+/).includes(h.id));
            }""",
            arg=[f"#id_allowed_booking_groups{suffix}"],
            timeout=10000,
        )
    for suffix in ("_from", "_to"):
        control = page.locator(f"#id_allowed_booking_groups{suffix}")
        assert control.count() == 1, f"missing control id_allowed_booking_groups{suffix}"
        assert control.first.is_visible()
        assert (
            "id_allowed_booking_groups_helptext"
            in (control.first.get_attribute("aria-describedby") or "").split()
        )
    help_text = page.locator("#id_allowed_booking_groups_helptext").inner_text()
    assert "Membership in ANY ONE selected group is enough" in help_text
    assert "Django" not in help_text
    assert "Django" not in page.locator("#id_booking_restricted_helptext").inner_text()

    # Keyboard-reachable generated list boxes.
    page.focus("#id_allowed_booking_groups_to")
    assert page.evaluate("document.activeElement.id") == "id_allowed_booking_groups_to"

    # The selected operator group is listed (staff surface only).
    assert GROUP_NAME in page.content()
    _assert_no_horizontal_overflow(page)

    # --- 390 ------------------------------------------------------------------
    page.set_viewport_size(MOBILE)
    for suffix in ("_from", "_to"):
        control = page.locator(f"#id_allowed_booking_groups{suffix}")
        assert control.count() == 1
        assert control.first.is_visible()
    assert GROUP_NAME in page.content()
    _assert_no_horizontal_overflow(page)
    # Screenshot 2 of 2: admin configuration view at 390 (no member data).
    page.screenshot(
        path=f"{output_path}/booking-eligibility-admin-asset-390.png",
        full_page=True,
    )


# --- custom theme ------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_custom_theme_renders_booking_access(
    page: Page,
    live_server,
    branding_custom,
    member_user: User,
    open_asset: Asset,
    restricted_asset: Asset,
    global_policy,
) -> None:
    _login(page, live_server, member_user)
    page.goto(f"{live_server.url}/assets/")
    page.set_viewport_size(DESKTOP)
    assert page.locator("img.brand-logo").get_attribute("src") == "/branding/logo"
    assert _bookable_cell(page, open_asset.name) == "yes"
    assert _bookable_cell(page, restricted_asset.name) == "no"

    page.goto(f"{live_server.url}/assets/{restricted_asset.id}/")
    assert "Restricted to specific approved groups" in page.content()
    assert page.get_by_role("link", name="Reserve this asset").count() == 0
    _assert_no_horizontal_overflow(page)

    # The custom-brand eligibility controls are checked at 390 as well.
    page.goto(f"{live_server.url}/assets/")
    page.set_viewport_size(MOBILE)
    assert _bookable_cell(page, open_asset.name) == "yes"
    assert _bookable_cell(page, restricted_asset.name) == "no"
    _assert_no_horizontal_overflow(page)

    page.goto(f"{live_server.url}/assets/{restricted_asset.id}/")
    assert "Restricted to specific approved groups" in page.content()
    assert page.get_by_role("link", name="Reserve this asset").count() == 0
    _assert_no_horizontal_overflow(page)
