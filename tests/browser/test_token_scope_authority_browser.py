"""Browser qualification for token-scope authority (order 051-a).

The token creation form offers only the scopes the server-request owner
can currently issue: a reader without booking sees the new read-only
read-all scope but not create; a booker without read-all sees create but
not read-all; an owner with both capabilities sees both, each with
meaningful accessible help. Forged or GET->POST-revoked scope selections
cannot create a token. Screenshots are privacy-safe (safe form pages only,
before any one-time token is issued) and limited to two.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from django.contrib.auth.models import Permission
from django.test import override_settings
from playwright.sync_api import Page

from slaif_reservation.accounts.models import ApiToken, User
from slaif_reservation.accounts.services import issue_api_token

REPO_ROOT = Path(__file__).resolve().parents[2]
CUSTOM = REPO_ROOT / "tests" / "fixtures" / "branding" / "custom"

DESKTOP = {"width": 1440, "height": 900}
MOBILE = {"width": 390, "height": 844}

READ_ALL = "reservations:read_all"
READ_ALL_LABEL = "Read other people's reservations (read-only)"
CREATE_LABEL = "Create reservations"
FRAMEWORK_MARKERS = ("Django", "Powered by Django")


@pytest.fixture
def reader() -> User:
    target = User.objects.create_user(
        email="scopebrowser-reader@example.com",
        password="not-a-secret",
        display_name="Scope Reader",
    )
    target.user_permissions.add(
        Permission.objects.get(
            codename="view_all_reservations", content_type__app_label="reservations"
        )
    )
    return target


@pytest.fixture
def booker() -> User:
    target = User.objects.create_user(
        email="scopebrowser-booker@example.com",
        password="not-a-secret",
        display_name="Scope Booker",
    )
    target.user_permissions.add(
        Permission.objects.get(codename="book_assets", content_type__app_label="reservations")
    )
    return target


@pytest.fixture
def both_caps() -> User:
    target = User.objects.create_user(
        email="scopebrowser-both@example.com",
        password="not-a-secret",
        display_name="Scope Both",
    )
    target.user_permissions.add(
        Permission.objects.get(codename="book_assets", content_type__app_label="reservations"),
        Permission.objects.get(
            codename="view_all_reservations", content_type__app_label="reservations"
        ),
    )
    return target


def _login(page: Page, live_server, user: User) -> None:
    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Email").fill(user.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/")


def _logout(page: Page, live_server) -> None:
    # Logout is POST-only (SAR-011); the real UI path is the nav form button.
    page.get_by_role("button", name="Logout").click()
    page.wait_for_url(f"{live_server.url}/login/")


def _open_form(page: Page, live_server) -> None:
    page.goto(f"{live_server.url}/tokens/new/")
    page.get_by_role("group", name="Scopes (what the token may do)").wait_for()


def _assert_no_framework_branding(page: Page) -> None:
    content = page.content()
    for marker in FRAMEWORK_MARKERS:
        assert marker not in content


def _assert_no_horizontal_overflow(page: Page) -> None:
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), (
        "horizontal page overflow"
    )


@pytest.mark.django_db(transaction=True)
def test_browser_token_scope_choices_follow_current_capabilities(
    page: Page,
    live_server,
    output_path,
    reader: User,
    booker: User,
    both_caps: User,
) -> None:
    page.set_viewport_size(DESKTOP)

    # Reader without booking: the new read-only scope is offered, create is not.
    _login(page, live_server, reader)
    _open_form(page, live_server)
    assert page.get_by_label(READ_ALL_LABEL).is_visible()
    assert page.get_by_label(CREATE_LABEL).count() == 0
    read_all_effect = "Read-only: lets the token list and inspect other people's reservations"
    assert read_all_effect in page.content()
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)
    _logout(page, live_server)

    # Booker without read-all: create is offered, the new scope is not.
    _login(page, live_server, booker)
    _open_form(page, live_server)
    assert page.get_by_label(CREATE_LABEL).is_visible()
    assert page.get_by_label(READ_ALL_LABEL).count() == 0
    _logout(page, live_server)

    # Both capabilities: both options with clear, meaningful, associated help.
    _login(page, live_server, both_caps)
    _open_form(page, live_server)
    assert page.get_by_label(READ_ALL_LABEL).is_visible()
    assert page.get_by_label(CREATE_LABEL).is_visible()
    read_all_help = page.locator(".scope-option", has_text=READ_ALL_LABEL).locator("p.choice-help")
    assert read_all_help.inner_text().startswith("Read-only:")
    create_help = page.locator(".scope-option", has_text=CREATE_LABEL).locator("p.choice-help")
    assert "current policy and limits" in create_help.inner_text()
    assert "currently has the booking" in create_help.inner_text()
    # The fieldset-level help stays bound to the group (accessible label/aria).
    assert page.locator("fieldset.scope-group").get_attribute("aria-describedby")
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)
    # Screenshot 1 (of max 2): the safe both-capabilities form, default branding.
    page.screenshot(path=f"{output_path}/token-scope-choices-both-1440.png")

    page.set_viewport_size(MOBILE)
    _assert_no_horizontal_overflow(page)
    # The nav collapses behind the menu toggle below 64rem; logout through
    # the real UI path at desktop size.
    page.set_viewport_size(DESKTOP)
    _logout(page, live_server)


@pytest.mark.django_db(transaction=True)
def test_browser_token_scope_choices_custom_branding_mobile(
    page: Page,
    live_server,
    output_path,
    reader: User,
) -> None:
    with override_settings(BRANDING_DIR=str(CUSTOM)):
        page.set_viewport_size(MOBILE)
        _login(page, live_server, reader)
        _open_form(page, live_server)
        assert page.get_by_label(READ_ALL_LABEL).is_visible()
        assert page.get_by_label(CREATE_LABEL).count() == 0
        _assert_no_horizontal_overflow(page)
        # Screenshot 2 (of max 2): the safe reader form at 390, custom branding.
        page.screenshot(path=f"{output_path}/token-scope-choices-reader-390-custom.png")


@pytest.mark.django_db(transaction=True)
def test_browser_forged_and_revoked_scope_post_denied(
    page: Page,
    live_server,
    both_caps: User,
) -> None:
    page.set_viewport_size(DESKTOP)
    _login(page, live_server, both_caps)
    _open_form(page, live_server)
    assert page.get_by_label(READ_ALL_LABEL).is_visible()

    # Forged POST (valid CSRF, unavailable + unknown scope values): no token.
    csrf = page.locator('#content form input[name="csrfmiddlewaretoken"]').get_attribute("value")
    response = page.request.post(
        f"{live_server.url}/tokens/new/",
        form={"name": "Forged", "scopes": [READ_ALL, "admin:*"], "lifetime_days": "7"},
        headers={"X-CSRFToken": csrf},
    )
    assert response.status == 200
    assert "Check the highlighted fields" in response.text()
    assert ApiToken.objects.count() == 0
    # The re-rendered form shows the scopes field error.
    page.reload()
    assert page.get_by_role("group", name="Scopes (what the token may do)").is_visible()
    assert page.locator("#id_scopes-help").is_visible()

    # GET -> POST revocation race: the capability is removed after the form
    # was rendered; the same now-unavailable selection cannot create a token.
    both_caps.user_permissions.clear()
    response = page.request.post(
        f"{live_server.url}/tokens/new/",
        form={"name": "Revoked race", "scopes": [READ_ALL], "lifetime_days": "7"},
        headers={"X-CSRFToken": csrf},
    )
    assert response.status == 200
    assert "Check the highlighted fields" in response.text()
    assert ApiToken.objects.count() == 0

    # The owner's own list/revoke lifecycle still works after losing rights.
    issued = issue_api_token(
        owner=User.objects.get(pk=both_caps.pk),
        name="Lost rights token",
        scopes=["reservations:read"],
        lifetime_days=7,
    )
    page.goto(f"{live_server.url}/tokens/")
    assert page.get_by_role("heading", name="API tokens").is_visible()
    assert issued.token.display_prefix in page.content()
    assert issued.bearer_token not in page.content()
    page.get_by_role("button", name="Revoke").click()
    page.wait_for_url(f"{live_server.url}/tokens/")
    issued.token.refresh_from_db()
    assert issued.token.revoked_at is not None
    assert page.get_by_text("No action").first.is_visible()
    assert issued.bearer_token not in page.content()
