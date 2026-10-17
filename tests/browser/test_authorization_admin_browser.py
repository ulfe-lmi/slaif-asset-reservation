"""Browser checks for the A16 authorization foundation admin surface (048-a).

Real Chromium: the optional external identifier control on the user change
page carries visible, bound, accessible help at 1440 and 390 without
horizontal overflow and stays keyboard-reachable; an authorized
administrator can set, verify and clear the value through the existing
form; a staff session without the model permission is refused; and the
protected ApiToken surface remains read-only denied. Screenshots are
privacy-safe (synthetic identifier, safe password status; no credentials,
tokens, verifiers, CSRF or cookies captured).
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page

from slaif_reservation.accounts.models import User

DESKTOP = {"width": 1440, "height": 900}
MOBILE = {"width": 390, "height": 844}
SYNTHETIC_IDENTIFIER = "00042-BrowserExt"


@pytest.fixture
def admin_user() -> User:
    return User.objects.create_superuser(
        email="auth048-admin@example.com",
        password="not-a-secret",
        display_name="Auth 048 Admin",
    )


@pytest.fixture
def member_user() -> User:
    return User.objects.create_user(
        email="auth048-member@example.com",
        password="not-a-secret",
        display_name="Auth 048 Member",
    )


@pytest.fixture
def bare_staff_user() -> User:
    return User.objects.create_user(
        email="auth048-barestaff@example.com",
        password="not-a-secret",
        display_name="Auth 048 Bare Staff",
        is_staff=True,
    )


def _admin_login(page: Page, live_server, user: User, *, fresh_session: bool = False) -> None:
    if fresh_session:
        # Drop the previous session so the login page renders for this user.
        page.context.clear_cookies()
    page.goto(f"{live_server.url}/admin/login/")
    page.get_by_label("Email").fill(user.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/admin/")


def _assert_no_horizontal_overflow(page: Page) -> None:
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), (
        "horizontal page overflow"
    )


def _assert_help_near_control(page: Page, control_selector: str, help_id: str) -> None:
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


def _capture(page: Page, output_path, name: str, *, full_page: bool = False) -> None:
    page.screenshot(path=f"{output_path}/{name}.png", full_page=full_page)


@pytest.mark.django_db(transaction=True)
def test_browser_admin_external_identifier_guidance_and_edit(
    page: Page,
    live_server,
    output_path,
    admin_user: User,
    member_user: User,
    bare_staff_user: User,
) -> None:
    # A staff session without the model permission cannot reach the form
    # (refused before any write is possible).
    _admin_login(page, live_server, bare_staff_user)
    page.goto(f"{live_server.url}/admin/accounts/user/{member_user.pk}/change/")
    assert "403" in page.content()

    _admin_login(page, live_server, admin_user, fresh_session=True)
    page.goto(f"{live_server.url}/admin/accounts/user/{member_user.pk}/change/")

    # Desktop: visible bound help, keyboard-reachable, no overflow.
    page.set_viewport_size(DESKTOP)
    _assert_help_near_control(page, "#id_external_identifier", "id_external_identifier_helptext")
    help_text = page.locator("#id_external_identifier_helptext").inner_text()
    assert "opaque identifier for an external system" in help_text
    assert "leading zeroes" in help_text
    assert "not a credential" in help_text
    page.focus("#id_external_identifier")
    assert page.evaluate("() => document.activeElement.id") == "id_external_identifier"
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "admin-external-identifier-1440", full_page=True)

    # Mobile 390: same association, no overflow.
    page.set_viewport_size(MOBILE)
    _assert_help_near_control(page, "#id_external_identifier", "id_external_identifier_helptext")
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "admin-external-identifier-390", full_page=True)

    # Authorized administrator sets the opaque value through the existing
    # form; the value round-trips exactly (leading zeroes preserved).
    change_url = f"{live_server.url}/admin/accounts/user/{member_user.pk}/change/"
    page.set_viewport_size(DESKTOP)
    page.fill("#id_external_identifier", SYNTHETIC_IDENTIFIER)
    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_url(f"{live_server.url}/admin/accounts/user/")
    page.goto(change_url)
    assert page.locator("#id_external_identifier").input_value() == SYNTHETIC_IDENTIFIER
    assert User.objects.get(pk=member_user.pk).external_identifier == SYNTHETIC_IDENTIFIER

    # Clearing the field clears the stored value back to NULL.
    page.fill("#id_external_identifier", "")
    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_url(f"{live_server.url}/admin/accounts/user/")
    page.goto(change_url)
    assert page.locator("#id_external_identifier").input_value() == ""
    assert User.objects.get(pk=member_user.pk).external_identifier is None

    # Protected record boundary: the token surface stays denied even for
    # the superuser (read-only/service-backed mutations unchanged).
    page.goto(f"{live_server.url}/admin/accounts/apitoken/add/")
    assert "403" in page.content()
