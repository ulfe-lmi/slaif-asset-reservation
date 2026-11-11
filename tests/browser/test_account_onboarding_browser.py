"""Real Chromium/HTTP/PostgreSQL checks for administrator account onboarding (058-a).

Desktop 1440 and mobile 390 over real HTTP with a synthetic locmem SMTP
sink: the admin add form prefills a fresh six-character temporary
credential in BOTH password controls (asserted semantically only — the
add page itself is never screenshotted because the controls visibly
carry the credential); the account is committed pending and activated by
the single accepted send; a member signing in with the temporary
credential is gated to the password-change page only; the forced change
uses the normal validators, keeps the current session and invalidates
the old credential; the explicit reissue control rotates the credential
with exactly one new send. Screenshots are limited to privacy-safe
surfaces (two in this file).
"""

from __future__ import annotations

import re
from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone
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

BASE_URL = "https://reservation.example.test"
FROM_EMAIL = "no-reply@example.test"
NEW_PASSWORD = "onboard-into-safe-pw0rd"


@pytest.fixture
def admin_user() -> User:
    return User.objects.create_superuser(
        email="onb-browser-admin@example.com",
        password="not-a-secret",
        display_name="Onboarding Browser Admin",
    )


def _admin_login(page: Page, live_server, user: User) -> None:
    page.goto(f"{live_server.url}/admin/login/")
    page.get_by_label("Email").fill(user.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/admin/")


def _member_login(page: Page, live_server, email: str, password: str) -> None:
    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Log in").click()


def _assert_no_horizontal_overflow(page: Page) -> None:
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), (
        "horizontal page overflow"
    )


def _assert_no_framework_branding(page: Page) -> None:
    for marker in FRAMEWORK_MARKERS:
        assert marker not in page.content(), marker


def _capture(page: Page, output_path, name: str) -> None:
    page.screenshot(path=f"{output_path}/{name}.png")


@pytest.mark.django_db(transaction=True)
def test_browser_admin_add_onboarding_flow(
    page: Page,
    live_server,
    output_path,
    admin_user: User,
    settings,
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    settings.PUBLIC_BASE_URL = BASE_URL
    settings.DEFAULT_FROM_EMAIL = FROM_EMAIL

    page.set_viewport_size(DESKTOP)
    _admin_login(page, live_server, admin_user)

    # Add form: the fresh generated credential is prefilled in BOTH
    # controls, the temporary-path guidance is bound, the page is
    # non-cacheable. (Semantic assertions only: no screenshot of this
    # page, whose controls visibly carry the credential.)
    add_response = page.goto(f"{live_server.url}/admin/accounts/user/add/")
    assert "no-store" in add_response.headers["cache-control"]
    prefill = page.locator("#id_password1").input_value()
    assert prefill == page.locator("#id_password2").input_value()
    assert len(prefill) == 6
    assert any(ch.isalpha() for ch in prefill) and any(ch.isdigit() for ch in prefill)
    help_text = page.locator("#id_password1_helptext").inner_text()
    assert "temporary six-character password has been generated for you" in help_text
    assert "You are creating a new member account" in page.content()
    _assert_no_horizontal_overflow(page)

    # Submit unchanged: the account is created pending, the single
    # synthetic send is accepted and the account is activated.
    page.locator("#id_email").fill("onb-browser-member@example.com")
    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_url(re.compile(r"/admin/accounts/user/[\w-]+/change/"))
    user = User.objects.get(email="onb-browser-member@example.com")
    assert user.is_active is True
    assert user.onboarding_password_expires_at is not None
    assert user.check_password(prefill)

    # Exactly one synthetic message with the canonical login URL, the
    # account identifier and the temporary credential.
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ["onb-browser-member@example.com"]
    assert message.from_email == FROM_EMAIL
    assert f"{BASE_URL}/login/" in message.body
    assert prefill in message.body
    assert "testserver" not in message.body
    assert "localhost" not in message.body

    # Change page: success status plus the onboarding block with the
    # reissue control. Privacy-safe: no credential is rendered.
    assert "The account was created and its login details were delivered by email." in (
        page.content()
    )
    assert "Onboarding in progress" in page.content()
    assert "Reissue onboarding login details" in page.content()
    assert prefill not in page.content()
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "admin-onboarding-change-1440")

    # The member signs in with the temporary credential and lands on the
    # forced-change page — never the dashboard.
    page.context.clear_cookies()
    _member_login(page, live_server, "onb-browser-member@example.com", prefill)
    page.wait_for_url(f"{live_server.url}/profile/password/")
    assert "You signed in with a temporary password" in page.content()
    assert f"Change password — {BRANDING}" == page.title()
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)
    _capture(page, output_path, "member-forced-change-1440")

    # Escape attempts all land back on the forced-change page, and the
    # session survives them.
    for path in ("/", "/profile/", "/assets/", "/admin/", "/api/v1/me/"):
        page.goto(f"{live_server.url}{path}")
        assert page.url == f"{live_server.url}/profile/password/", path

    # Mobile: the forced-change page holds at 390, then the member
    # completes the change with a normal-validator password.
    page.set_viewport_size(MOBILE)
    page.goto(f"{live_server.url}/profile/password/")
    assert "You signed in with a temporary password" in page.content()
    _assert_no_horizontal_overflow(page)
    page.locator("#id_old_password").fill(prefill)
    page.locator("#id_new_password1").fill(NEW_PASSWORD)
    page.locator("#id_new_password2").fill(NEW_PASSWORD)
    page.get_by_role("button", name="Change password").click()
    page.wait_for_url(f"{live_server.url}/profile/")

    user.refresh_from_db()
    assert user.is_active is True
    assert user.onboarding_password_expires_at is None
    assert user.check_password(NEW_PASSWORD)

    # The current session stayed in; the old temporary credential is
    # dead from a fresh session.
    page.goto(f"{live_server.url}/profile/")
    assert page.url == f"{live_server.url}/profile/"
    page.context.clear_cookies()
    _member_login(page, live_server, "onb-browser-member@example.com", prefill)
    page.wait_for_url(f"{live_server.url}/login/")
    assert "Enter a valid email address and password." in page.content()


@pytest.mark.django_db(transaction=True)
def test_browser_admin_reissue_flow(
    page: Page,
    live_server,
    admin_user: User,
    settings,
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    settings.PUBLIC_BASE_URL = BASE_URL
    settings.DEFAULT_FROM_EMAIL = FROM_EMAIL

    pending = User.objects.create_user(
        email="onb-browser-reissue@example.com",
        password="Mn56yz",
        is_active=False,
    )
    pending.onboarding_password_expires_at = timezone.now() + timedelta(hours=24)
    pending.save(update_fields=["onboarding_password_expires_at"])
    stored_hash = pending.password

    page.set_viewport_size(DESKTOP)
    _admin_login(page, live_server, admin_user)

    # Confirmation page: explains rotation and ambiguous delivery,
    # never shows the current credential.
    reissue_url = f"{live_server.url}/admin/accounts/user/{pending.pk}/onboarding-reissue/"
    page.goto(reissue_url)
    content = page.content()
    assert "A NEW temporary six-character password will be generated" in content
    assert "stops working immediately" in content
    assert "Mn56yz" not in content
    _assert_no_horizontal_overflow(page)

    before = len(mail.outbox)
    page.get_by_role("button", name="Yes, reissue the onboarding login details").click()
    page.wait_for_url(f"{live_server.url}/admin/accounts/user/{pending.pk}/change/")

    pending.refresh_from_db()
    assert pending.password != stored_hash  # previous credential invalidated
    assert len(mail.outbox) - before == 1  # exactly one new send
    new_password = re.search(r"Temporary password: (\S+)", mail.outbox[-1].body).group(1)
    assert len(new_password) == 6 and new_password != "Mn56yz"
    assert pending.check_password(new_password)
    # The synthetic send was accepted: the account is active again and
    # still pending its forced change.
    assert pending.is_active is True
    assert pending.onboarding_password_expires_at is not None
    assert "The new onboarding login details were delivered by email." in page.content()
