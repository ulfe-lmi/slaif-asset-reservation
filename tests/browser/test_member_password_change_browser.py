"""Real Chromium/HTTP/PostgreSQL checks for member password change (056-a).

Desktop 1440 and mobile 390: the Profile link, guided fields with labels
and accessible help associations, the wrong-old-password validation, the
successful change with current-session continuity, branding and overflow
boundaries. Screenshots are privacy-safe: no entered credential value,
hash, CSRF or cookie material; no one-time display surface.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page

from slaif_reservation.accounts.models import User

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


@pytest.fixture
def member_user() -> User:
    return User.objects.create_user(
        email="pw-change-member@example.com",
        password="not-a-secret",
        display_name="Password Change Member",
        timezone="Europe/Ljubljana",
    )


def _login(page: Page, live_server, user: User) -> None:
    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Email").fill(user.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/")


def _assert_no_horizontal_overflow(page: Page) -> None:
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), (
        "horizontal page overflow"
    )


def _assert_help_near_control(page: Page, control_selector: str, help_id: str) -> None:
    """Substantive nearby-help check (same contract as the guidance tour)."""
    control = page.locator(control_selector)
    assert control.count() == 1, f"ambiguous or missing control {control_selector}"
    assert control.first.is_visible(), f"control {control_selector} is not visible"
    help_el = page.locator(f"#{help_id}")
    assert help_el.count() == 1, f"missing help #{help_id}"
    assert help_el.first.is_visible(), f"help #{help_id} is not visible"
    bound_and_near = page.evaluate(
        r"""([control, help]) => {
            const c = document.querySelector(control);
            const h = document.getElementById(help);
            if (!c || !h) return false;
            const described = (c.getAttribute("aria-describedby") || "").split(/\s+/);
            if (!described.includes(h.id)) return false;
            const box = c.closest(".field, .filter, .form-row, fieldset");
            return box !== null && box.contains(h);
        }""",
        [control_selector, help_id],
    )
    assert bound_and_near, f"help #{help_id} is not bound to and near {control_selector}"


def _assert_no_framework_branding(page: Page) -> None:
    for marker in FRAMEWORK_MARKERS:
        assert marker not in page.content(), marker


def _capture(page: Page, output_path, name: str) -> None:
    page.screenshot(path=f"{output_path}/{name}.png")


@pytest.mark.django_db(transaction=True)
def test_browser_member_password_change(
    page: Page,
    live_server,
    output_path,
    member_user: User,
) -> None:
    page.set_viewport_size(DESKTOP)
    _login(page, live_server, member_user)

    # The Profile page offers the obvious password-change action.
    page.goto(f"{live_server.url}/profile/")
    link = page.get_by_role("link", name="Change your password")
    assert link.count() == 1
    assert link.is_visible()
    link.click()
    page.wait_for_url(f"{live_server.url}/profile/password/")

    # Branded, guided, and free of any stored or submitted secret material.
    assert f"Change password — {BRANDING}" == page.title()
    assert "Change password" in page.locator("h1").inner_text()
    _assert_no_framework_branding(page)
    _assert_help_near_control(page, "#id_old_password", "id_old_password-help")
    _assert_help_near_control(page, "#id_new_password1", "id_new_password1-help")
    _assert_help_near_control(page, "#id_new_password2", "id_new_password2-help")
    assert "at least 8 characters" in page.locator("#id_new_password1-help").inner_text()
    for control in ("#id_old_password", "#id_new_password1", "#id_new_password2"):
        assert page.locator(control).input_value() == ""
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "member-password-change-1440")

    # Wrong current password: validation is shown, nothing is changed.
    page.locator("#id_old_password").fill("wrong-current-passw0rd")
    page.locator("#id_new_password1").fill("brand-new-passw0rd")
    page.locator("#id_new_password2").fill("brand-new-passw0rd")
    page.get_by_role("button", name="Change password").click()
    page.wait_for_url(f"{live_server.url}/profile/password/")
    assert page.locator(".error-summary").first.is_visible()
    member_user.refresh_from_db()
    assert member_user.check_password("not-a-secret")
    _capture(page, output_path, "member-password-change-error-1440")

    # Correct change: success notice, session continuity, no secret echo.
    # Password fields never re-render submitted values, so the failed
    # attempt cleared them: fill all three again for the real change.
    page.locator("#id_old_password").fill("not-a-secret")
    page.locator("#id_new_password1").fill("brand-new-passw0rd")
    page.locator("#id_new_password2").fill("brand-new-passw0rd")
    page.get_by_role("button", name="Change password").click()
    page.wait_for_url(f"{live_server.url}/profile/")
    assert "Password changed" in page.content()
    assert "brand-new-passw0rd" not in page.content()
    assert "not-a-secret" not in page.content()
    member_user.refresh_from_db()
    assert member_user.check_password("brand-new-passw0rd")
    # The current session remains signed in on a member route.
    page.goto(f"{live_server.url}/reservations/")
    assert page.url == f"{live_server.url}/reservations/"

    # Mobile: no overflow, still branded and guided.
    page.set_viewport_size(MOBILE)
    page.goto(f"{live_server.url}/profile/password/")
    _assert_no_horizontal_overflow(page)
    _assert_no_framework_branding(page)
    _assert_help_near_control(page, "#id_new_password1", "id_new_password1-help")
    _capture(page, output_path, "member-password-change-390")

    # Privacy: the changed credential never appears on the page.
    assert "brand-new-passw0rd" not in page.content()
