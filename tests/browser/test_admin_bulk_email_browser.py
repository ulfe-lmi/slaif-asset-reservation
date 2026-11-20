"""Real Chromium/HTTP/PostgreSQL checks for the Administration
selected-user email (066-a, SAR-058).

Desktop 1440 and mobile 390 over real HTTP with a synthetic locmem SMTP
sink (never a real relay or recipient): the user-list checkbox action is
visible to the change-permission holder, the selection opens the
branded compose page (exact count, protected address list, editable
subject/body, no send), one **Send email** click performs the final
POST and redirects to the same route's GET, which reports the
nonsecret counts once — a browser refresh of the result never resends.
Each selected user receives one separate plain-text message (no
CC/BCC) and unselected users receive nothing; a disabled transport
offers no send and never reports a delivery. Screenshots are limited
to privacy-safe surfaces (three in this file, synthetic addresses
only).
"""

from __future__ import annotations

import re

import pytest
from django.core import mail
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

SUBJECT = "Lab maintenance notice"
BODY = "The shared cluster is offline on Friday for maintenance."


@pytest.fixture
def admin_user() -> User:
    return User.objects.create_superuser(
        email="bulk-browser-admin@example.test",
        password="not-a-secret",
        display_name="Bulk Browser Admin",
    )


@pytest.fixture
def recipients() -> list[User]:
    return [
        User.objects.create_user(
            email=f"bulk-browser-{i}@example.test",
            password="not-a-secret",
            display_name=f"Bulk Browser Recipient {i}",
        )
        for i in range(1, 4)
    ]


def _admin_login(page: Page, live_server, user: User) -> None:
    page.goto(f"{live_server.url}/admin/login/")
    page.get_by_label("Email").fill(user.email)
    page.get_by_label("Password").fill("not-a-secret")
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server.url}/admin/")


def _assert_no_horizontal_overflow(page: Page) -> None:
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), (
        "horizontal page overflow"
    )


def _assert_no_framework_branding(page: Page) -> None:
    for marker in FRAMEWORK_MARKERS:
        assert marker not in page.content(), marker


def _select_users_and_apply(page: Page, emails: list[str]) -> None:
    for email in emails:
        page.locator(f"tr:has-text('{email}') input[name=_selected_action]").check()
    # The administration renders the action form at the top AND bottom
    # of the list: address the first of each.
    page.locator("select[name=action]").first.select_option("email_selected_users")
    page.get_by_role("button", name="Go").first.click()


@pytest.mark.django_db(transaction=True)
def test_browser_admin_bulk_email_desktop_flow(
    page: Page,
    live_server,
    output_path,
    admin_user: User,
    recipients: list[User],
    settings,
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    page.set_viewport_size(DESKTOP)
    _admin_login(page, live_server, admin_user)

    # User list: the action is offered and the selection opens the
    # compose page (never a send).
    page.goto(f"{live_server.url}/admin/accounts/user/")
    assert "Send a plain-text email to the selected users" in page.content()
    _select_users_and_apply(page, [recipients[0].email, recipients[2].email])
    page.wait_for_url(re.compile(r"/admin/accounts/user/bulk-email/"))

    compose = page.content()
    assert "2 users selected" in compose
    assert recipients[0].email in compose
    assert recipients[2].email in compose
    assert recipients[1].email not in compose
    assert "Send email" in compose
    assert "Each recipient receives this message separately as plain text" in compose
    assert BRANDING in compose
    _assert_no_framework_branding(page)
    _assert_no_horizontal_overflow(page)
    page.screenshot(path=f"{output_path}/bulk-email-compose-1440.png")
    # The single Send action stays inside the first desktop viewport
    # (the compose page must not push it below the fold).
    send_box = page.get_by_role("button", name="Send email").bounding_box()
    assert send_box is not None
    assert send_box["y"] + send_box["height"] <= page.viewport_size["height"]

    # One click performs the final POST; the result reports counts only.
    page.get_by_label("Subject").fill(SUBJECT)
    page.get_by_label("Message").fill(BODY)
    page.get_by_role("button", name="Send email").click()
    # The POST redirects to the same route's GET; the result is a
    # one-shot GET, so reloading it can never resend the batch.
    page.wait_for_url(re.compile(r"/admin/accounts/user/bulk-email/\?result="))
    result = page.content()
    assert "2 messages accepted by the relay" in result
    assert "0 messages unconfirmed" in result
    assert "0 recipients not attempted" in result
    assert SUBJECT not in result
    assert BODY not in result
    for user in recipients:
        assert user.email not in result
    page.screenshot(path=f"{output_path}/bulk-email-result-1440.png")

    # Refreshing the result page is safely refused (the one-shot nonce
    # was already consumed): the browser returns to the user list and
    # no further message is sent.
    assert len(mail.outbox) == 2
    page.reload()
    page.wait_for_url(re.compile(r"/admin/accounts/user/$"))
    assert len(mail.outbox) == 2
    assert "no longer available" in page.content()

    # Delivery: one plain-text message per selected user, no CC/BCC.
    assert len(mail.outbox) == 2
    for message, user in zip(mail.outbox, (recipients[0], recipients[2]), strict=True):
        assert message.to == [user.email]
        assert message.cc == []
        assert message.bcc == []
        assert message.subject == SUBJECT
        assert message.body == BODY


@pytest.mark.django_db(transaction=True)
def test_browser_admin_bulk_email_mobile_flow(
    page: Page,
    live_server,
    output_path,
    admin_user: User,
    recipients: list[User],
    settings,
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    page.set_viewport_size(MOBILE)
    _admin_login(page, live_server, admin_user)

    page.goto(f"{live_server.url}/admin/accounts/user/")
    _select_users_and_apply(page, [recipients[0].email])
    page.wait_for_url(re.compile(r"/admin/accounts/user/bulk-email/"))
    assert "1 user selected" in page.content()
    _assert_no_horizontal_overflow(page)
    # Narrow width: no page overflow and the single Send action is
    # reachable and usable after a normal scroll.
    send = page.get_by_role("button", name="Send email")
    page.screenshot(path=f"{output_path}/bulk-email-compose-390.png")
    send.scroll_into_view_if_needed()
    assert send.is_visible()
    send_box = send.bounding_box()
    assert send_box is not None
    assert 0 <= send_box["y"] <= page.viewport_size["height"]

    page.get_by_label("Subject").fill(SUBJECT)
    page.get_by_label("Message").fill(BODY)
    page.get_by_role("button", name="Send email").click()
    page.wait_for_url(re.compile(r"/admin/accounts/user/bulk-email/\?result="))
    assert "1 message accepted by the relay" in page.content()
    _assert_no_horizontal_overflow(page)
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [recipients[0].email]

    # The result refresh is refused and never resends (narrow width).
    page.reload()
    page.wait_for_url(re.compile(r"/admin/accounts/user/$"))
    assert len(mail.outbox) == 1
    assert "no longer available" in page.content()


@pytest.mark.django_db(transaction=True)
def test_browser_admin_bulk_email_disabled_transport(
    page: Page,
    live_server,
    admin_user: User,
    recipients: list[User],
    settings,
) -> None:
    # The default test settings leave account email disabled: the
    # compose page offers no send and the dummy backend is never used.
    settings.ACCOUNT_EMAIL_ENABLED = False
    page.set_viewport_size(DESKTOP)
    _admin_login(page, live_server, admin_user)

    page.goto(f"{live_server.url}/admin/accounts/user/")
    _select_users_and_apply(page, [recipients[0].email])
    page.wait_for_url(re.compile(r"/admin/accounts/user/bulk-email/"))
    content = page.content()
    assert "Account email is not configured" in content
    assert "Send email" not in content
    assert mail.outbox == []
