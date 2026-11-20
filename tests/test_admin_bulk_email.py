"""Focused server tests for the Administration selected-user email (066-a,
SAR-058).

Synthetic accounts and the locmem/fake backends only — no real relay,
recipient or credential. Covers: action visibility exactly for the model
change permission, the selection -> compose -> single-send flow, the
per-request bound (empty, stale, forged, oversized, select-across),
CSRF/permission/method guards, subject/body validation including header
injection, per-recipient privacy (one message each, no CC/BCC, not to
unselected users, no content in URL/session/logs/action log), the
disabled-transport fail-closed boundary, partial/ambiguous delivery with
no automatic retry, the POST/Redirect/GET one-shot result (the send
redirects, the GET renders the counts, a refresh never resends and
invalid or foreign nonces are refused safely), and the uncacheable
compose/result pages.
"""

from __future__ import annotations

import logging

import pytest
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Permission
from django.core import mail
from django.test import Client, override_settings
from django.urls import reverse

from slaif_reservation.accounts import bulk_email
from slaif_reservation.accounts.models import User

COMPOSE_URL = "/admin/accounts/user/bulk-email/"
CHANGELIST_URL = "/admin/accounts/user/"

SUBJECT = "BulkNotice-ALPHA-42"
BODY = "BulkBody-ALPHA-42 plain text for the selected users."


class _FakeBackend:
    """Synthetic relay (referenced by import path in live/test backends).

    ``fail_after``: raise on the Nth message (1-based; 0 = never).
    ``zero_after``: return 0 (explicit rejection) on the Nth message.
    """

    fail_after: int = 0
    zero_after: int = 0
    calls: list[int] = []

    def __init__(self, *args, **kwargs) -> None:
        pass

    def open(self):
        return True

    def close(self):
        pass

    def send_messages(self, messages) -> int:
        for _message in messages:
            _FakeBackend.calls.append(len(_FakeBackend.calls) + 1)
            if _FakeBackend.fail_after and len(_FakeBackend.calls) >= _FakeBackend.fail_after:
                raise RuntimeError("synthetic bulk SMTP down")
            if _FakeBackend.zero_after and len(_FakeBackend.calls) >= _FakeBackend.zero_after:
                return 0
        return len(messages)


def _reset_fake() -> None:
    _FakeBackend.calls = []
    _FakeBackend.fail_after = 0
    _FakeBackend.zero_after = 0


@pytest.fixture(autouse=True)
def _clean_mail_and_fake():
    mail.outbox = []
    _reset_fake()
    yield
    mail.outbox = []
    _reset_fake()


@pytest.fixture
def admin_user() -> User:
    return User.objects.create_superuser(
        email="bulk-admin@example.test",
        password="not-a-secret",
        display_name="Bulk Admin",
    )


@pytest.fixture
def staff_change() -> User:
    user = User.objects.create_user(
        email="bulk-staff-change@example.test",
        password="not-a-secret",
        display_name="Bulk Staff Change",
        is_staff=True,
    )
    user.user_permissions.add(
        Permission.objects.get(codename="change_user", content_type__app_label="accounts")
    )
    return user


@pytest.fixture
def staff_view_only() -> User:
    user = User.objects.create_user(
        email="bulk-staff-view@example.test",
        password="not-a-secret",
        display_name="Bulk Staff View",
        is_staff=True,
    )
    user.user_permissions.add(
        Permission.objects.get(codename="view_user", content_type__app_label="accounts")
    )
    return user


@pytest.fixture
def recipients() -> list[User]:
    return [
        User.objects.create_user(
            email=f"bulk-one-{i}@example.test",
            password="not-a-secret",
            display_name=f"Bulk Recipient {i}",
        )
        for i in range(1, 4)
    ]


def _selected_action_post(client: Client, pks: list, *, select_across: bool = False):
    data = {
        "action": "email_selected_users",
        "index": "0",
        "_selected_action": [str(pk) for pk in pks],
    }
    if select_across:
        data["select_across"] = "1"
    return client.post(CHANGELIST_URL, data)


# --- action visibility ----------------------------------------------------


@pytest.mark.django_db
def test_action_visible_only_with_change_permission(
    client: Client, admin_user: User, staff_change: User, staff_view_only: User, recipients: list
) -> None:
    client.force_login(admin_user)
    html = client.get(CHANGELIST_URL).content.decode()
    assert "email_selected_users" in html

    client.force_login(staff_change)
    html = client.get(CHANGELIST_URL).content.decode()
    assert "email_selected_users" in html

    # View-only staff sees the list but NOT the action.
    client.force_login(staff_view_only)
    response = client.get(CHANGELIST_URL)
    assert response.status_code == 200
    assert "email_selected_users" not in response.content.decode()


@pytest.mark.django_db
def test_admin_admission_gates_bulk_email_surface(
    client: Client, staff_change: User, recipients: list
) -> None:
    member = User.objects.create_user(
        email="bulk-member@example.test",
        password="not-a-secret",
        display_name="Bulk Member",
    )
    inactive_staff = User.objects.create_user(
        email="bulk-staff-inactive@example.test",
        password="not-a-secret",
        display_name="Bulk Staff Inactive",
        is_staff=True,
        is_active=False,
    )
    inactive_staff.user_permissions.add(
        Permission.objects.get(codename="change_user", content_type__app_label="accounts")
    )
    service_staff = User.objects.create_user(
        email="bulk-staff-service@example.test",
        password="not-a-secret",
        display_name="Bulk Staff Service",
        is_staff=True,
        is_service_account=True,
    )
    service_staff.user_permissions.add(
        Permission.objects.get(codename="change_user", content_type__app_label="accounts")
    )

    # Active non-staff, active staff service accounts and inactive staff
    # are all terminated to the administration login by the site gate
    # (no admin route is served, nothing is sent).
    for user in (member, service_staff, inactive_staff):
        client.force_login(user)
        response = client.get(COMPOSE_URL, {"pks": str(recipients[0].pk)})
        assert response.status_code == 302
        assert response.headers["Location"].startswith("/admin/login/")
        assert mail.outbox == []

    # The selection POST is admitted by the site gate the same way.
    client.force_login(member)
    response = _selected_action_post(client, [recipients[0].pk])
    assert response.status_code in (302, 403)
    assert "/bulk-email/" not in response.headers.get("Location", "")
    assert mail.outbox == []


@pytest.mark.django_db
def test_forged_action_without_change_permission_sends_nothing(
    client: Client, staff_view_only: User, recipients: list
) -> None:
    client.force_login(staff_view_only)
    response = _selected_action_post(client, [recipients[0].pk])
    assert response.status_code == 200  # re-render with a warning, no dispatch
    assert "/bulk-email/" not in str(response.context.get("messages", ""))
    assert "Location" not in response.headers
    assert mail.outbox == []


# --- selection step ---------------------------------------------------------


@pytest.mark.django_db
def test_action_redirects_to_compose_without_sending(
    client: Client, admin_user: User, recipients: list
) -> None:
    client.force_login(admin_user)
    pks = [recipients[0].pk, recipients[2].pk]
    response = _selected_action_post(client, pks)
    assert response.status_code == 302
    location = response.headers["Location"]
    assert location.startswith(reverse("admin:accounts_user_bulk_email") + "?pks=")
    # The selection step itself never sends.
    assert mail.outbox == []


@pytest.mark.django_db
def test_action_refuses_empty_and_oversized_selection(
    client: Client, admin_user: User, recipients: list
) -> None:
    client.force_login(admin_user)
    many = [
        User.objects.create_user(
            email=f"bulk-many-{i:03d}@example.test",
            password="not-a-secret",
            display_name=f"Bulk Many {i}",
        )
        for i in range(201)
    ]
    all_pks = [u.pk for u in many]

    # An empty selection submits no ``_selected_action`` entries, so the
    # action is never dispatched: the request returns to the user list
    # and nothing is sent.
    response = _selected_action_post(client, [])
    assert response.status_code == 302
    assert response.headers["Location"].startswith(CHANGELIST_URL)
    assert mail.outbox == []

    # A selection over the bound (select across all pages): refused
    # wholesale, never truncated, no compose redirect, no send.
    response = _selected_action_post(client, all_pks, select_across=True)
    assert response.status_code == 302
    assert response.headers["Location"].startswith(CHANGELIST_URL)
    assert "/bulk-email/" not in response.headers["Location"]
    assert mail.outbox == []

    # Exactly at the bound is accepted (redirect only, still no send).
    # (Explicit per-row selection: select-across would widen the
    # selection to the whole list, which is over the bound here.)
    response = _selected_action_post(client, all_pks[:200])
    assert response.status_code == 302
    assert response.headers["Location"].startswith(
        reverse("admin:accounts_user_bulk_email") + "?pks="
    )
    assert mail.outbox == []


# --- compose GET ------------------------------------------------------------


@pytest.mark.django_db
def test_compose_get_shows_count_addresses_and_never_sends(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(admin_user)
    pks = ",".join(str(u.pk) for u in recipients[:2])
    response = client.get(COMPOSE_URL, {"pks": pks})
    assert response.status_code == 200
    html = response.content.decode()
    assert "2 users selected" in html
    assert recipients[0].email in html
    assert recipients[1].email in html
    assert recipients[2].email not in html
    assert 'name="subject"' in html
    assert 'name="body"' in html
    assert "Send email" in html
    assert "SLAIF Asset Reservation" in html
    assert "no-store" in response.headers["Cache-Control"]
    assert mail.outbox == []


@pytest.mark.django_db
def test_compose_get_refuses_empty_stale_forged_and_oversized(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(admin_user)
    stale_uuid = "0" * 32  # well-formed UUID, no such account
    cases = {
        "empty": {},
        "stale": {"pks": f"{recipients[0].pk},{stale_uuid}"},
        "forged": {"pks": f"{recipients[0].pk},not-a-uuid"},
    }
    for name, params in cases.items():
        response = client.get(COMPOSE_URL, params)
        assert response.status_code == 302, name
        assert response.headers["Location"] == CHANGELIST_URL, name
        assert mail.outbox == []

    # A direct URL with an oversized selection is refused the same way.
    many = [
        User.objects.create_user(
            email=f"bulk-oversize-{i:03d}@example.test",
            password="not-a-secret",
            display_name=f"Bulk Oversize {i}",
        )
        for i in range(201)
    ]
    response = client.get(COMPOSE_URL, {"pks": ",".join(str(u.pk) for u in many)})
    assert response.status_code == 302
    assert response.headers["Location"] == CHANGELIST_URL
    assert mail.outbox == []


@pytest.mark.django_db
def test_compose_get_requires_change_permission(
    client: Client, staff_view_only: User, recipients: list
) -> None:
    client.force_login(staff_view_only)
    assert client.get(COMPOSE_URL, {"pks": str(recipients[0].pk)}).status_code == 403
    assert mail.outbox == []


@pytest.mark.django_db
def test_compose_get_disabled_transport_offers_no_send(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = False
    client.force_login(admin_user)
    response = client.get(COMPOSE_URL, {"pks": str(recipients[0].pk)})
    assert response.status_code == 200
    html = response.content.decode()
    assert "Account email is not configured" in html
    assert "Send email" not in html
    assert 'name="subject"' not in html
    assert "no-store" in response.headers["Cache-Control"]


# --- final POST guards ------------------------------------------------------


def _compose_post(client: Client, pks, *, subject=SUBJECT, body=BODY):
    return client.post(
        COMPOSE_URL,
        {
            "selected_pks": ",".join(str(pk) for pk in pks),
            "subject": subject,
            "body": body,
        },
    )


@pytest.mark.django_db
def test_final_post_requires_csrf_token(admin_user: User, recipients: list, settings) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client = Client(enforce_csrf_checks=True)
    client.force_login(admin_user)
    response = _compose_post(client, [recipients[0].pk])
    assert response.status_code == 403
    assert mail.outbox == []


@pytest.mark.django_db
def test_final_post_requires_change_permission(
    client: Client, staff_view_only: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(staff_view_only)
    response = _compose_post(client, [recipients[0].pk])
    assert response.status_code == 403
    assert mail.outbox == []


@pytest.mark.django_db
def test_final_post_refuses_empty_stale_forged_and_duplicate_selection(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(admin_user)
    one, two = recipients[0], recipients[1]

    for selected in ("", f"{one.pk},", f"{one.pk},not-a-uuid", f"{one.pk},{'0' * 32}"):
        response = client.post(
            COMPOSE_URL, {"selected_pks": selected, "subject": SUBJECT, "body": BODY}
        )
        assert response.status_code == 302, selected
        assert response.headers["Location"] == CHANGELIST_URL, selected
        assert mail.outbox == []

    # A duplicated pk is collapsed to ONE message per account.
    response = _compose_post(client, [one.pk, one.pk, two.pk])
    assert response.status_code == 302
    result = client.get(response.headers["Location"])
    assert result.status_code == 200
    assert "2 messages accepted by the relay" in result.content.decode()
    assert len(mail.outbox) == 2
    assert {m.to[0] for m in mail.outbox} == {one.email, two.email}


@pytest.mark.django_db
def test_final_post_disabled_transport_fails_closed(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = False
    client.force_login(admin_user)
    response = _compose_post(client, [recipients[0].pk, recipients[1].pk])
    assert response.status_code == 302
    assert response.headers["Location"] == CHANGELIST_URL
    assert mail.outbox == []  # the dummy backend is never used as delivery


@pytest.mark.django_db
def test_final_post_validates_subject_and_body(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(admin_user)
    bad_cases = [
        ("empty subject", "", BODY),
        ("blank subject", "   ", BODY),
        ("subject newline", "line1\nline2", BODY),
        ("subject CR", "line1\r\nline2", BODY),
        ("subject too long", "x" * 201, BODY),
        ("empty body", SUBJECT, ""),
        ("blank body", SUBJECT, " \n "),
        ("body too long", SUBJECT, "y" * 10_001),
    ]
    for name, subject, body in bad_cases:
        response = _compose_post(client, [recipients[0].pk], subject=subject, body=body)
        assert response.status_code == 200, name  # re-render with errors
        assert mail.outbox == [], name

    # An invalid-POST page keeps the rendered, bound help.
    html = _compose_post(client, [recipients[0].pk], subject="", body=BODY).content.decode()
    assert 'id="id_subject_helptext"' in html
    assert "This field is required." in html
    # A whitespace-only subject is stripped by the field and refused as
    # empty; the bound help stays rendered on the invalid-POST page.
    html_blank = _compose_post(
        client, [recipients[0].pk], subject="   ", body=BODY
    ).content.decode()
    assert "This field is required." in html_blank
    assert 'id="id_subject_helptext"' in html_blank
    html_crlf = _compose_post(
        client, [recipients[0].pk], subject="line1\r\nline2", body=BODY
    ).content.decode()
    assert "single line without line breaks" in html_crlf


# --- delivery and privacy -----------------------------------------------------


@pytest.mark.django_db
def test_final_post_sends_one_plain_text_message_per_recipient(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(admin_user)
    entries_before = LogEntry.objects.count()
    response = _compose_post(client, [u.pk for u in recipients])
    # POST/Redirect/GET: the POST redirects to the same route's GET;
    # the result is rendered there, never as the POST response.
    assert response.status_code == 302
    location = response.headers["Location"]
    assert location.startswith(f"{COMPOSE_URL}?{bulk_email.RESULT_PARAM}=")
    assert "selected_pks" not in location
    for needle in (SUBJECT, BODY, *(u.email for u in recipients)):
        assert needle not in location

    # Only the random nonce and the nonsecret counts enter the session.
    stored = client.session[bulk_email.RESULT_SESSION_KEY]
    assert set(stored) == {"nonce", "accepted", "uncertain", "not_attempted"}
    assert isinstance(stored["nonce"], str) and len(stored["nonce"]) >= 16
    assert (stored["accepted"], stored["uncertain"], stored["not_attempted"]) == (3, 0, 0)
    for value in client.session.values():
        rendered = str(value)
        assert SUBJECT not in rendered
        assert BODY not in rendered
        for user in recipients:
            assert user.email not in rendered

    assert len(mail.outbox) == 3
    for message, user in zip(mail.outbox, recipients, strict=True):
        assert message.to == [user.email]
        assert message.cc == []
        assert message.bcc == []
        assert message.subject == SUBJECT
        assert message.body == BODY
    # Unselected users receive nothing (no other address appears).
    seen = {addr for m in mail.outbox for addr in (*m.to, *m.cc, *m.bcc)}
    assert len(seen) == 3

    # The GET result page reports counts only, never content or
    # addresses, and consumes the one-shot nonce.
    result = client.get(location)
    assert result.status_code == 200
    html = result.content.decode()
    assert "3 messages accepted by the relay" in html
    assert "0 messages unconfirmed" in html
    assert "0 recipients not attempted" in html
    assert SUBJECT not in html
    assert BODY not in html
    for user in recipients:
        assert user.email not in html
    assert "no-store" in result.headers["Cache-Control"]
    assert bulk_email.RESULT_SESSION_KEY not in client.session

    # No Admin action log entry (and no other LogEntry) records it.
    assert LogEntry.objects.count() == entries_before


# --- POST/Redirect/GET one-shot result -------------------------------------


@pytest.mark.django_db
def test_result_get_refresh_never_resends(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(admin_user)
    response = _compose_post(client, [u.pk for u in recipients[:2]])
    assert response.status_code == 302
    location = response.headers["Location"]
    assert len(mail.outbox) == 2

    # The first GET renders the result once.
    first = client.get(location)
    assert first.status_code == 200
    assert "2 messages accepted by the relay" in first.content.decode()

    # A browser refresh of the result URL is a safe refusal: it never
    # resends and lands back on the user list with a notice.
    refresh = client.get(location)
    assert refresh.status_code == 302
    assert refresh.headers["Location"] == CHANGELIST_URL
    assert len(mail.outbox) == 2
    landing = client.get(refresh.headers["Location"])
    assert landing.status_code == 200
    assert "no longer available" in landing.content.decode()


@pytest.mark.django_db
def test_result_get_refuses_invalid_and_foreign_nonces(
    client: Client, admin_user: User, staff_change: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(admin_user)
    response = _compose_post(client, [recipients[0].pk])
    assert response.status_code == 302
    location = response.headers["Location"]
    assert len(mail.outbox) == 1

    # A different session opening the same result URL is refused: no
    # counts are disclosed and nothing is sent.
    other = Client()
    other.force_login(staff_change)
    foreign = other.get(location)
    assert foreign.status_code == 302
    assert foreign.headers["Location"] == CHANGELIST_URL
    assert "1 message accepted" not in foreign.content.decode()
    assert len(mail.outbox) == 1

    # Invalid and empty nonces in the owner's own session are refused
    # the same way, without revealing whether a result exists.
    for nonce in ("deadbeef" * 8, ""):
        invalid = client.get(COMPOSE_URL, {bulk_email.RESULT_PARAM: nonce})
        assert invalid.status_code == 302, nonce
        assert invalid.headers["Location"] == CHANGELIST_URL, nonce
        assert len(mail.outbox) == 1, nonce

    # The owner's own one-shot result is still shown exactly once.
    mine = client.get(location)
    assert mine.status_code == 200
    assert "1 message accepted by the relay" in mine.content.decode()
    again = client.get(location)
    assert again.status_code == 302
    assert again.headers["Location"] == CHANGELIST_URL
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_final_post_leaves_no_content_in_urls_or_logs(
    client: Client, admin_user: User, recipients: list, settings, caplog
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    caplog.set_level(logging.DEBUG)
    client.force_login(admin_user)
    response = _compose_post(client, [u.pk for u in recipients[:2]])
    assert response.status_code == 302
    # The POST address is a fixed route; the redirect carries only the
    # one-shot nonce, never content or addresses.
    assert response.wsgi_request.get_full_path() == COMPOSE_URL
    location = response.headers["Location"]
    assert location.startswith(f"{COMPOSE_URL}?{bulk_email.RESULT_PARAM}=")
    for needle in (SUBJECT, BODY, recipients[0].email, recipients[1].email):
        assert needle not in location
    result = client.get(location)
    assert result.status_code == 200
    assert result.wsgi_request.get_full_path().split("?", 1)[0] == COMPOSE_URL
    for needle in (SUBJECT, BODY, recipients[0].email, recipients[1].email):
        assert needle not in result.wsgi_request.get_full_path()
        assert needle not in caplog.text
    html = result.content.decode()
    assert "2 messages accepted by the relay" in html
    assert "selected_pks" not in html


# --- bounded failure semantics -------------------------------------------------


@pytest.mark.django_db
def test_zero_acceptance_stops_without_retry(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    _FakeBackend.zero_after = 1
    with override_settings(EMAIL_BACKEND="test_admin_bulk_email._FakeBackend"):
        client.force_login(admin_user)
        post = _compose_post(client, [u.pk for u in recipients])
    assert post.status_code == 302
    assert len(_FakeBackend.calls) == 1  # no automatic retry
    html = client.get(post.headers["Location"]).content.decode()
    assert "0 messages accepted" in html
    assert "1 message unconfirmed" in html
    assert "2 recipients not attempted" in html
    assert SUBJECT not in html


@pytest.mark.django_db
def test_exception_after_partial_acceptance_stops(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    # Two sends are accepted, the third relay call raises.
    _FakeBackend.fail_after = 3
    with override_settings(EMAIL_BACKEND="test_admin_bulk_email._FakeBackend"):
        client.force_login(admin_user)
        post = _compose_post(client, [u.pk for u in recipients])
    assert post.status_code == 302
    assert len(_FakeBackend.calls) == 3  # the failed send is not retried
    html = client.get(post.headers["Location"]).content.decode()
    assert "2 messages accepted by the relay" in html
    assert "1 message unconfirmed" in html
    assert "0 recipients not attempted" in html
    # The failure is not echoed: no exception text or content on the page.
    assert "synthetic bulk SMTP down" not in html
    assert SUBJECT not in html
    assert BODY not in html


@pytest.mark.django_db
def test_all_accepted_reports_full_count(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(admin_user)
    post = _compose_post(client, [u.pk for u in recipients])
    assert post.status_code == 302
    html = client.get(post.headers["Location"]).content.decode()
    assert "3 messages accepted by the relay" in html
    assert "0 messages unconfirmed" in html
    assert "0 recipients not attempted" in html
