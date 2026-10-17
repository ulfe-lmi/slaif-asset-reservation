from datetime import timedelta
from pathlib import Path

import pytest
from django.contrib.auth.models import Permission
from django.test import override_settings
from playwright.sync_api import expect
from tests.browser.test_slaif_design import CUSTOM, inspect_surface
from tests.test_reservation_shortcuts import NOW

from slaif_reservation.accounts.models import User
from slaif_reservation.assets.models import Asset
from slaif_reservation.reservations.models import Reservation, ReservationPolicy
from slaif_reservation.reservations.services import update_policy


@pytest.fixture
def clock(monkeypatch):
    monkeypatch.setattr("django.utils.timezone.now", lambda: NOW)


@pytest.fixture
def member():
    created = User.objects.create_user(
        email="uat-member@example.test", password="not-a-secret", timezone="Asia/Kathmandu"
    )
    # A16: explicit baseline booking capability (real Permission row).
    created.user_permissions.add(
        Permission.objects.get(codename="book_assets", content_type__app_label="reservations")
    )
    return created


@pytest.fixture
def staff():
    return User.objects.create_user(
        email="uat-staff@example.test", password="not-a-secret", is_staff=True
    )


@pytest.fixture
def asset():
    return Asset.objects.create(
        slug="uat-workstation",
        name="Atlas workstation",
        kind="machine",
        active=True,
        reservable=True,
    )


@pytest.fixture
def policy(asset):
    return ReservationPolicy.objects.create(
        name="UAT policy",
        asset=None,
        min_duration_minutes=15,
        max_duration_minutes=240,
        booking_horizon_days=7,
        min_lead_minutes=30,
        max_upcoming_per_principal=20,
        max_concurrent_per_principal=8,
    )


@pytest.fixture
def browser_context_args(browser_context_args):
    # Deliberately different from the member profile: no browser-time arithmetic.
    return {**browser_context_args, "timezone_id": "America/Los_Angeles"}


def login(page, live_server, member):
    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Email").fill(member.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in", exact=True).click()
    page.wait_for_url(f"{live_server.url}/")


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("width", [1440, 390])
@pytest.mark.parametrize("theme", ["default", "custom"])
def test_quick_duration_browser_and_range(
    page, live_server, clock, member, asset, policy, width, theme, output_path, request
):
    branding = override_settings(BRANDING_DIR=str(CUSTOM) if theme == "custom" else None)
    branding.enable()
    request.addfinalizer(branding.disable)
    page.set_viewport_size({"width": width, "height": 1200})
    login(page, live_server, member)
    page.goto(f"{live_server.url}/assets/{asset.id}/reserve/")
    inspect_surface(page, output_path, "reserve-custom-selected", width, theme)
    start = page.locator("#id_start")
    expect(start).to_have_value("2026-10-24T14:16")
    expect(page.locator("#id_end")).to_have_value("2026-10-24T15:16")
    assert start.get_attribute("min") == "2026-10-24T14:16"
    assert start.get_attribute("max") == "2026-10-31T13:45"
    expect(page.get_by_text("Reservations may start between", exact=False)).to_be_visible()
    for label in ["1 hour", "2 hours", "4 hours", "Custom end time"]:
        expect(page.get_by_role("radio", name=label, exact=True)).to_be_visible()
    start.fill("2026-10-31T13:46")
    assert start.evaluate("el => el.validity.rangeOverflow")
    start.fill("2026-10-24T14:15")
    assert start.evaluate("el => el.validity.rangeUnderflow")
    start.fill("2026-10-25T15:45")
    page.get_by_role("radio", name="1 hour", exact=True).check()
    expect(page.locator("#id_end")).to_be_hidden()
    assert page.locator("#id_end").is_disabled()
    page.get_by_role("radio", name="Custom end time", exact=True).check()
    expect(page.locator("#id_end")).to_be_visible()
    assert page.locator("#id_end").is_enabled()
    page.get_by_role("radio", name="1 hour", exact=True).check()
    page.wait_for_function("document.fonts.status === 'loaded'")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert page.locator('input[name="duration"]').evaluate_all(
        "els => els.every(el => document.getElementById(el.getAttribute('aria-describedby')))"
    )
    page.get_by_role("button", name="Create reservation").scroll_into_view_if_needed()
    page.evaluate("window.scrollTo(0, 0)")
    Path(output_path).mkdir(parents=True, exist_ok=True)
    inspect_surface(page, output_path, "reserve-quick-selected", width, theme)
    page.screenshot(path=f"{output_path}/reservation-shortcuts-{theme}-{width}.png")
    page.get_by_role("button", name="Create reservation").click()
    page.wait_for_url("**/reservations/**/")
    reservation = Reservation.objects.get(requested_by_user=member)
    assert reservation.start_at == NOW.replace(day=25, hour=10, minute=0, second=0)
    assert reservation.end_at - reservation.start_at == timedelta(hours=1)


@pytest.mark.django_db(transaction=True)
def test_browser_policy_choices_and_stale_forged_post(
    page, live_server, clock, member, asset, policy, staff
):
    update_policy(
        policy=policy, actor_user=staff, min_duration_minutes=90, max_duration_minutes=180
    )
    login(page, live_server, member)
    page.goto(f"{live_server.url}/assets/{asset.id}/reserve/")
    expect(page.get_by_role("radio", name="1 hour", exact=True)).to_have_count(0)
    expect(page.get_by_role("radio", name="4 hours", exact=True)).to_have_count(0)
    page.get_by_role("radio", name="2 hours", exact=True).check()
    page.locator("#id_start").fill("2026-10-26T15:45")
    update_policy(policy=policy, actor_user=staff, booking_horizon_days=1)
    page.get_by_role("button", name="Create reservation").click()
    expect(
        page.get_by_text("The reservation starts beyond the booking horizon.", exact=True)
    ).to_be_visible()
    assert Reservation.objects.count() == 0
    # Bypass the newly rendered browser bounds: the server still rejects it.
    page.locator("#id_start").evaluate(
        "el => { el.removeAttribute('min'); el.removeAttribute('max'); }"
    )
    page.locator("#id_start").fill("2026-10-26T15:45")
    page.get_by_role("button", name="Create reservation").click()
    expect(
        page.get_by_text("The reservation starts beyond the booking horizon.", exact=True)
    ).to_be_visible()
    assert Reservation.objects.count() == 0


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("width", [1440, 390])
def test_browser_can_reserve_with_prefilled_times(
    page, live_server, clock, member, asset, policy, width, output_path
):
    page.set_viewport_size({"width": width, "height": 1200})
    login(page, live_server, member)
    page.goto(f"{live_server.url}/assets/{asset.id}/reserve/")
    expect(page.locator("#id_start")).to_have_value("2026-10-24T14:16")
    expect(page.locator("#id_end")).to_have_value("2026-10-24T15:16")
    expect(page.get_by_role("radio", name="Custom end time", exact=True)).to_be_checked()
    inspect_surface(page, output_path, "reserve-prefilled", width, "default")
    page.get_by_role("button", name="Create reservation").click()
    page.wait_for_url("**/reservations/**/")
    reservation = Reservation.objects.get(requested_by_user=member)
    assert reservation.start_at == NOW.replace(minute=31, second=0)
    assert reservation.end_at == reservation.start_at + timedelta(hours=1)
