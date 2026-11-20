"""Focused server tests for the Administration selected-user email
(066-a/067-a, SAR-058).

Synthetic accounts and the locmem/fake backends only — no real relay,
recipient or credential. Covers: action visibility exactly for the model
change permission, the checked-selection -> compose -> single-send flow
bound to the administrator session by a random nonce (recipients derive
ONLY from the stored checked UUIDs; a direct or forged link, an added or
swapped recipient field, a missing/foreign/stale/replaced nonce, a
deleted account, an empty or oversized selection, select-across,
permission loss between GET and POST and CSRF all fail closed before any
send), the per-request bound, subject/body validation including header
injection, per-recipient privacy (one message each, no CC/BCC, not to
unselected users, no content in URL/session/logs/action log), the
disabled-transport fail-closed boundary, partial/ambiguous delivery with
no automatic retry, the POST/Redirect/GET one-shot result (the send
redirects, the GET renders the counts, a refresh never resends and
invalid or foreign nonces are refused safely), selection consumption on
a successful send (a form resubmission never resends) and the
uncacheable compose/result pages.
"""

from __future__ import annotations

import logging
import uuid
from urllib.parse import parse_qs, urlsplit

import pytest
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Permission
from django.core import mail
from django.test import Client, override_settings

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


def _action_nonce(client: Client, pks: list) -> str:
    """Run the checkbox action and return its session-bound nonce."""
    response = _selected_action_post(client, pks)
    assert response.status_code == 302
    location = response.headers["Location"]
    assert location.startswith(COMPOSE_URL)
    params = parse_qs(urlsplit(location).query)
    assert list(params) == [bulk_email.SELECTION_PARAM]  # no pks in the URL
    return params[bulk_email.SELECTION_PARAM][0]


def _compose_get(client: Client, nonce: str | None = None, **extra):
    params = dict(extra)
    if nonce is not None:
        params[bulk_email.SELECTION_PARAM] = nonce
    return client.get(COMPOSE_URL, params)


def _compose_post(client: Client, nonce: str | None, *, subject=SUBJECT, body=BODY, **extra):
    data: dict[str, str] = {"subject": subject, "body": body, **extra}
    if nonce is not None:
        data[bulk_email.SELECTION_PARAM] = nonce
    return client.post(COMPOSE_URL, data)


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
        is_service_account=True,
    )
    service_staff.user_permissions.add(
        Permission.objects.get(codename="change_user", content_type__app_label="accounts")
    )

    # Active non-staff, active staff service accounts and inactive staff
    # are all terminated to the administration login by the site gate
    # (no admin route is served, nothing is sent), regardless of any
    # selection parameter.
    for user in (member, service_staff, inactive_staff):
        client.force_login(user)
        response = client.get(COMPOSE_URL, {bulk_email.SELECTION_PARAM: "forged-nonce"})
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
    assert "Location" not in response.headers
    assert bulk_email.SELECTION_SESSION_KEY not in client.session
    assert mail.outbox == []


# --- selection step ---------------------------------------------------------


@pytest.mark.django_db
def test_action_redirects_to_compose_binding_session_selection(
    client: Client, admin_user: User, recipients: list
) -> None:
    client.force_login(admin_user)
    pks = [recipients[0].pk, recipients[2].pk]
    response = _selected_action_post(client, pks)
    assert response.status_code == 302
    location = response.headers["Location"]
    assert location.startswith(COMPOSE_URL)
    # The redirect carries ONLY the nonce — no UUIDs, no addresses.
    params = parse_qs(urlsplit(location).query)
    assert list(params) == [bulk_email.SELECTION_PARAM]
    nonce = params[bulk_email.SELECTION_PARAM][0]
    # The selection state holds exactly the checked UUIDs and the nonce:
    # bounded UUIDs and nonce only, no addresses or content.
    stored = client.session[bulk_email.SELECTION_SESSION_KEY]
    assert set(stored) == {"nonce", "pks"}
    assert stored["nonce"] == nonce
    assert stored["pks"] == [str(pk) for pk in sorted(pks, key=str)]
    for value in (stored["nonce"], *stored["pks"]):
        assert value != ""
    for pk in stored["pks"]:
        uuid.UUID(pk)  # every stored value is a well-formed UUID
    for user in recipients:
        assert user.email not in location
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
    # action is never dispatched: the request returns to the user list,
    # no selection is bound and nothing is sent.
    response = _selected_action_post(client, [])
    assert response.status_code == 302
    assert response.headers["Location"].startswith(CHANGELIST_URL)
    assert bulk_email.SELECTION_SESSION_KEY not in client.session
    assert mail.outbox == []

    # A selection over the bound (select across all pages): refused
    # wholesale, never truncated, no compose redirect, no bound
    # selection, no send.
    response = _selected_action_post(client, all_pks, select_across=True)
    assert response.status_code == 302
    assert response.headers["Location"].startswith(CHANGELIST_URL)
    assert "/bulk-email/" not in response.headers["Location"]
    assert bulk_email.SELECTION_SESSION_KEY not in client.session
    assert mail.outbox == []

    # Exactly at the bound is accepted (redirect only, still no send).
    # (Explicit per-row selection: select-across would widen the
    # selection to the whole list, which is over the bound here.)
    response = _selected_action_post(client, all_pks[:200])
    assert response.status_code == 302
    assert response.headers["Location"].startswith(COMPOSE_URL)
    assert mail.outbox == []


@pytest.mark.django_db
def test_action_selection_supersedes_previous_pending_selection(
    client: Client, admin_user: User, recipients: list
) -> None:
    client.force_login(admin_user)
    first = _action_nonce(client, [recipients[0].pk, recipients[1].pk])
    second = _action_nonce(client, [recipients[2].pk])
    assert first != second
    stored = client.session[bulk_email.SELECTION_SESSION_KEY]
    assert stored["nonce"] == second
    assert stored["pks"] == [str(recipients[2].pk)]


# --- compose GET ------------------------------------------------------------


@pytest.mark.django_db
def test_compose_get_shows_count_addresses_and_never_sends(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(admin_user)
    nonce = _action_nonce(client, [recipients[0].pk, recipients[1].pk])
    response = _compose_get(client, nonce)
    assert response.status_code == 200
    html = response.content.decode()
    assert "2 users selected" in html
    assert recipients[0].email in html
    assert recipients[1].email in html
    assert recipients[2].email not in html
    assert 'name="subject"' in html
    assert 'name="body"' in html
    # The form carries the session nonce, never the recipient list.
    assert f'name="{bulk_email.SELECTION_PARAM}" value="{nonce}"' in html
    assert 'name="selected_pks"' not in html
    # The page must never leak template syntax: a multi-line template
    # comment (invalid in Django templates) would otherwise render as
    # literal text in the browser.
    assert "{#" not in html
    assert "The recipient list is never submitted" not in html
    assert "Send email" in html
    assert "SLAIF Asset Reservation" in html
    assert "no-store" in response.headers["Cache-Control"]
    assert mail.outbox == []


@pytest.mark.django_db
def test_compose_get_refuses_missing_forged_and_direct_url(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(admin_user)

    # No prior checkbox selection: a direct URL cannot compose, not even
    # with the historical ``pks`` parameter and a valid, UNSELECTED
    # account UUID — the browser never supplies the recipient list.
    cases = [
        ("no nonce", {}),
        ("forged nonce", {bulk_email.SELECTION_PARAM: "deadbeef" * 8}),
        ("legacy pks param with valid unselected UUID", {"pks": str(recipients[2].pk)}),
    ]
    for name, params in cases:
        response = client.get(COMPOSE_URL, params)
        assert response.status_code == 302, name
        assert response.headers["Location"] == CHANGELIST_URL, name
        assert mail.outbox == [], name
    # The refusal asks for a reselection.
    landing = client.get(CHANGELIST_URL)
    assert "select the users" in landing.content.decode()


@pytest.mark.django_db
def test_compose_get_refuses_superseded_and_deleted_selection(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(admin_user)
    stale = _action_nonce(client, [recipients[0].pk])
    # A new checked selection replaces the pending one: the older
    # compose tab is refused with a reselect notice and sends nothing.
    current = _action_nonce(client, [recipients[1].pk])
    response = _compose_get(client, stale)
    assert response.status_code == 302
    assert response.headers["Location"] == CHANGELIST_URL
    assert mail.outbox == []
    # The current selection still composes.
    ok = _compose_get(client, current)
    assert ok.status_code == 200
    assert "1 user selected" in ok.content.decode()
    assert mail.outbox == []

    # A selected account deleted after the selection is a stale
    # selection: refused, and the pending selection is cleared.
    third = _action_nonce(client, [recipients[2].pk])
    recipients[2].delete()
    response = _compose_get(client, third)
    assert response.status_code == 302
    assert response.headers["Location"] == CHANGELIST_URL
    assert bulk_email.SELECTION_SESSION_KEY not in client.session
    assert mail.outbox == []


@pytest.mark.django_db
def test_compose_get_requires_change_permission(
    client: Client, staff_view_only: User, recipients: list
) -> None:
    client.force_login(staff_view_only)
    assert client.get(COMPOSE_URL, {bulk_email.SELECTION_PARAM: "nonce"}).status_code == 403
    assert mail.outbox == []


@pytest.mark.django_db
def test_compose_get_disabled_transport_offers_no_send(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = False
    client.force_login(admin_user)
    nonce = _action_nonce(client, [recipients[0].pk])
    response = _compose_get(client, nonce)
    assert response.status_code == 200
    html = response.content.decode()
    assert "Account email is not configured" in html
    assert "Send email" not in html
    assert 'name="subject"' not in html
    assert "no-store" in response.headers["Cache-Control"]


# --- final POST guards ------------------------------------------------------


@pytest.mark.django_db
def test_final_post_requires_csrf_token(admin_user: User, recipients: list, settings) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    plain = Client()
    plain.force_login(admin_user)
    nonce = _action_nonce(plain, [recipients[0].pk])
    # The CSRF-enforcing client shares the bound selection session but
    # presents no CSRF token.
    client = Client(enforce_csrf_checks=True)
    client.cookies["sessionid"] = plain.cookies["sessionid"].value
    response = _compose_post(client, nonce)
    assert response.status_code == 403
    assert mail.outbox == []


@pytest.mark.django_db
def test_final_post_requires_change_permission(
    client: Client, staff_view_only: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(staff_view_only)
    response = _compose_post(
        client,
        "nonce",
    )
    assert response.status_code == 403
    assert mail.outbox == []


@pytest.mark.django_db
def test_final_post_refuses_missing_forged_foreign_and_stale_nonce(
    client: Client, admin_user: User, staff_change: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(admin_user)
    nonce = _action_nonce(client, [recipients[0].pk, recipients[1].pk])

    # Missing nonce, forged nonce: refused before any send.
    for bad in (None, "deadbeef" * 8):
        response = _compose_post(client, bad)
        assert response.status_code == 302, bad
        assert response.headers["Location"] == CHANGELIST_URL, bad
        assert mail.outbox == [], bad

    # A different administrator's session presenting the nonce: refused
    # (the nonce binds to the session that checked the users).
    other = Client()
    other.force_login(staff_change)
    response = _compose_post(other, nonce)
    assert response.status_code == 302
    assert response.headers["Location"] == CHANGELIST_URL
    assert mail.outbox == []

    # A stale nonce after the selection was replaced: refused with a
    # reselect notice, the current selection is untouched.
    stale = nonce
    fresh = _action_nonce(client, [recipients[2].pk])
    response = _compose_post(client, stale)
    assert response.status_code == 302
    assert response.headers["Location"] == CHANGELIST_URL
    assert mail.outbox == []
    stored = client.session[bulk_email.SELECTION_SESSION_KEY]
    assert stored["nonce"] == fresh
    # The replacement selection still sends exactly its checked set.
    response = _compose_post(client, fresh)
    assert response.status_code == 302
    assert [m.to[0] for m in mail.outbox] == [recipients[2].email]


@pytest.mark.django_db
def test_final_post_never_mails_forged_or_unselected_uuids(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    """ICA F-1: recipients derive ONLY from the stored checked
    selection, never from a browser-provided UUID list."""
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(admin_user)
    one, two, three = recipients

    # A valid, unselected account UUID added into the browser fields of
    # an otherwise legitimate send: the forged field is ignored and the
    # unchecked user receives nothing.
    nonce = _action_nonce(client, [one.pk, two.pk])
    response = _compose_post(client, nonce, selected_pks=str(three.pk))
    assert response.status_code == 302
    assert response.headers["Location"].startswith(f"{COMPOSE_URL}?")
    assert len(mail.outbox) == 2
    assert {m.to[0] for m in mail.outbox} == {one.email, two.email}
    assert three.email not in {addr for m in mail.outbox for addr in m.to}

    # Swapping the checked set entirely through a forged field: the
    # stored (consumed-after-send) selection still wins; the forged
    # recipient receives nothing.
    nonce = _action_nonce(client, [two.pk])
    response = _compose_post(client, nonce, selected_pks=str(three.pk))
    assert response.status_code == 302
    assert len(mail.outbox) == 3
    assert {m.to[0] for m in mail.outbox} == {one.email, two.email}
    assert three.email not in {addr for m in mail.outbox for addr in m.to}

    # No checkbox selection at all: even a valid existing UUID in a
    # forged field sends nothing.
    response = _compose_post(client, None, selected_pks=str(three.pk))
    assert response.status_code == 302
    assert response.headers["Location"] == CHANGELIST_URL
    assert len(mail.outbox) == 3
    assert three.email not in {addr for m in mail.outbox for addr in m.to}


@pytest.mark.django_db
def test_final_post_refuses_deleted_selected_account(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(admin_user)
    nonce = _action_nonce(client, [recipients[0].pk, recipients[1].pk])
    recipients[0].delete()
    response = _compose_post(client, nonce)
    assert response.status_code == 302
    assert response.headers["Location"] == CHANGELIST_URL
    # The stale selection is cleared; nothing was sent.
    assert bulk_email.SELECTION_SESSION_KEY not in client.session
    assert mail.outbox == []


@pytest.mark.django_db
def test_final_post_collapses_duplicate_stored_pks(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(admin_user)
    one, two = recipients[0], recipients[1]
    # Defensive resolver behaviour: a duplicate stored pk collapses to
    # ONE message per account.
    nonce = bulk_email.new_selection_nonce()
    session = client.session
    session[bulk_email.SELECTION_SESSION_KEY] = {
        "nonce": nonce,
        "pks": [str(one.pk), str(one.pk), str(two.pk)],
    }
    session.save()
    response = _compose_post(client, nonce)
    assert response.status_code == 302
    assert len(mail.outbox) == 2
    assert {m.to[0] for m in mail.outbox} == {one.email, two.email}


@pytest.mark.django_db
def test_final_post_disabled_transport_fails_closed(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = False
    client.force_login(admin_user)
    nonce = _action_nonce(client, [recipients[0].pk, recipients[1].pk])
    response = _compose_post(client, nonce)
    assert response.status_code == 302
    assert response.headers["Location"] == CHANGELIST_URL
    assert mail.outbox == []  # the dummy backend is never used as delivery


@pytest.mark.django_db
def test_final_post_validates_subject_and_body(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(admin_user)
    nonce = _action_nonce(client, [recipients[0].pk])
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
        response = _compose_post(client, nonce, subject=subject, body=body)
        assert response.status_code == 200, name  # re-render with errors
        assert mail.outbox == [], name

    # An invalid-POST page keeps the rendered, bound help.
    html = _compose_post(client, nonce, subject="", body=BODY).content.decode()
    assert 'id="id_subject_helptext"' in html
    assert "This field is required." in html
    # A whitespace-only subject is stripped by the field and refused as
    # empty; the bound help stays rendered on the invalid-POST page.
    html_blank = _compose_post(client, nonce, subject="   ", body=BODY).content.decode()
    assert "This field is required." in html_blank
    assert 'id="id_subject_helptext"' in html_blank
    html_crlf = _compose_post(client, nonce, subject="line1\r\nline2", body=BODY).content.decode()
    assert "single line without line breaks" in html_crlf

    # An invalid form does not consume the pending selection: the
    # corrected resubmission sends.
    assert bulk_email.SELECTION_SESSION_KEY in client.session
    response = _compose_post(client, nonce)
    assert response.status_code == 302
    assert response.headers["Location"].startswith(f"{COMPOSE_URL}?")
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [recipients[0].email]


# --- delivery and privacy -----------------------------------------------------


@pytest.mark.django_db
def test_final_post_sends_one_plain_text_message_per_recipient(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(admin_user)
    entries_before = LogEntry.objects.count()
    nonce = _action_nonce(client, [u.pk for u in recipients])
    response = _compose_post(client, nonce)
    # POST/Redirect/GET: the POST redirects to the same route's GET;
    # the result is rendered there, never as the POST response.
    assert response.status_code == 302
    location = response.headers["Location"]
    assert location.startswith(f"{COMPOSE_URL}?{bulk_email.RESULT_PARAM}=")
    for needle in (SUBJECT, BODY, *(u.email for u in recipients)):
        assert needle not in location

    # Only the one-shot nonce and the nonsecret counts enter the
    # session after the send; the pending selection (UUIDs + nonce
    # only) is consumed, so a form resubmission can never resend.
    stored = client.session[bulk_email.RESULT_SESSION_KEY]
    assert set(stored) == {"nonce", "accepted", "uncertain", "not_attempted"}
    assert isinstance(stored["nonce"], str) and len(stored["nonce"]) >= 16
    assert (stored["accepted"], stored["uncertain"], stored["not_attempted"]) == (3, 0, 0)
    assert bulk_email.SELECTION_SESSION_KEY not in client.session
    for value in client.session.values():
        rendered = str(value)
        assert SUBJECT not in rendered
        assert BODY not in rendered
        for user in recipients:
            assert user.email not in rendered

    # One plain-text message per checked recipient, exact set, no
    # CC/BCC.
    assert len(mail.outbox) == 3
    assert {tuple(m.to) for m in mail.outbox} == {(user.email,) for user in recipients}
    for message in mail.outbox:
        assert len(message.to) == 1
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

    # A form resubmission with the consumed selection nonce is refused:
    # nothing is resent.
    resubmit = _compose_post(client, nonce)
    assert resubmit.status_code == 302
    assert resubmit.headers["Location"] == CHANGELIST_URL
    assert len(mail.outbox) == 3

    # No Admin action log entry (and no other LogEntry) records it.
    assert LogEntry.objects.count() == entries_before


# --- POST/Redirect/GET one-shot result -------------------------------------


@pytest.mark.django_db
def test_result_get_refresh_never_resends(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    client.force_login(admin_user)
    nonce = _action_nonce(client, [u.pk for u in recipients[:2]])
    response = _compose_post(client, nonce)
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
    nonce = _action_nonce(client, [recipients[0].pk])
    response = _compose_post(client, nonce)
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
    for result_nonce in ("deadbeef" * 8, ""):
        invalid = client.get(COMPOSE_URL, {bulk_email.RESULT_PARAM: result_nonce})
        assert invalid.status_code == 302, result_nonce
        assert invalid.headers["Location"] == CHANGELIST_URL, result_nonce
        assert len(mail.outbox) == 1, result_nonce

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
    nonce = _action_nonce(client, [u.pk for u in recipients[:2]])
    # The action redirect carries only the nonce — no UUIDs or
    # addresses — and the session selection state holds UUIDs only.
    for value in client.session[bulk_email.SELECTION_SESSION_KEY].values():
        assert recipients[0].email not in str(value)
        assert recipients[1].email not in str(value)
    response = _compose_post(client, nonce)
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


# --- bounded failure semantics -------------------------------------------------


@pytest.mark.django_db
def test_zero_acceptance_stops_without_retry(
    client: Client, admin_user: User, recipients: list, settings
) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    _FakeBackend.zero_after = 1
    client.force_login(admin_user)
    nonce = _action_nonce(client, [u.pk for u in recipients])
    with override_settings(EMAIL_BACKEND="test_admin_bulk_email._FakeBackend"):
        post = _compose_post(client, nonce)
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
    client.force_login(admin_user)
    nonce = _action_nonce(client, [u.pk for u in recipients])
    with override_settings(EMAIL_BACKEND="test_admin_bulk_email._FakeBackend"):
        post = _compose_post(client, nonce)
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
    nonce = _action_nonce(client, [u.pk for u in recipients])
    post = _compose_post(client, nonce)
    assert post.status_code == 302
    html = client.get(post.headers["Location"]).content.decode()
    assert "3 messages accepted by the relay" in html
    assert "0 messages unconfirmed" in html
    assert "0 recipients not attempted" in html
