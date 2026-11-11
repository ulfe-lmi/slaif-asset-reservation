"""Administrator account onboarding (orders 058-a/058-b, SAR-055/SAR-056).

Focused positive/negative coverage on real PostgreSQL and real admin
HTTP: add-form prefill on every GET (enabled AND disabled, with
setup guidance when disabled), the short-lived signed prefill proof
(edited/tampered/expired/unbound rejection, manual normal-length
passwords unaffected), disabled-email fail closed (every add POST
refused before any account is written, CLI createsuperuser unchanged),
exactly-one post-commit synthetic delivery with activation only on
SMTP acceptance of the EXACT credential generation, failed/zero/
ambiguous delivery leaving the account inactive and unable to sign in,
account-scoped nonsecret failure status and no auto retry, manual
permission-checked reissue with rotation (inactive again while the new
delivery is pending), stale/superseded callbacks that neither send nor
activate nor claim delivery, the 24-hour temporary lifecycle (member
and Administration login denial after expiry, forced-change routing,
session termination), forced-change completion (session semantics, old
credential invalidation), the onboarding session-gate path allowlist
(including the "/static/" prefix), privacy (no plaintext in
DB/LogEntry/session/rendered pages), the unchanged createsuperuser
baseline, retained permission boundaries and the shared login abuse
budget. All mail is synthetic (locmem or in-test backends); no real
relay or recipient is used.
"""

from __future__ import annotations

import hashlib
import re
import string
import time
from datetime import timedelta
from typing import Any

import pytest
from django.contrib.admin.models import LogEntry
from django.contrib.auth import authenticate
from django.core import mail
from django.core.management import call_command
from django.core.signing import Signer, TimestampSigner, b62_encode
from django.test import Client, override_settings
from django.utils import timezone

from slaif_reservation.accounts import onboarding
from slaif_reservation.accounts.models import User

ADD_URL = "/admin/accounts/user/add/"
BASE_URL = "https://reservation.example.test"
FROM_EMAIL = "no-reply@example.test"
LOGIN_URL = "/login/"
ADMIN_LOGIN_URL = "/admin/login/"
PW_URL = "/profile/password/"


def _input_value(html: str, control_id: str) -> str:
    match = re.search(rf'<input[^>]*id="{control_id}"[^>]*>', html)
    assert match, f"missing control {control_id}"
    value = re.search(r'value="([^"]*)"', match.group(0))
    return value.group(1) if value else ""


# --- fixtures --------------------------------------------------------------


@pytest.fixture
def admin_user() -> User:
    return User.objects.create_superuser(
        email="onb-admin@example.com",
        password="admin-pass-058",
        display_name="Onboarding Admin",
    )


@pytest.fixture
def admin_client(admin_user: User) -> Client:
    client = Client()
    client.force_login(admin_user)
    return client


@pytest.fixture
def email_enabled(settings: Any) -> None:
    settings.ACCOUNT_EMAIL_ENABLED = True
    settings.PUBLIC_BASE_URL = BASE_URL
    settings.DEFAULT_FROM_EMAIL = FROM_EMAIL
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    mail.outbox = []


@pytest.fixture
def fixed_generator(monkeypatch: pytest.MonkeyPatch) -> None:
    """Deterministic generator injection (no probabilistic inequality)."""
    values = iter(["Ab12cd", "Zz98ab", "Kp34wx"])
    monkeypatch.setattr(onboarding, "generate_temporary_password", lambda: next(values))


@pytest.fixture
def monkey_value(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Set the generated value to exactly one explicit constant."""

    def _set(value: str) -> None:
        monkeypatch.setattr(onboarding, "generate_temporary_password", lambda: value)

    return _set


class _FailingSMTPBackend:
    calls = 0

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def send_messages(self, messages: list[Any]) -> int:
        type(self).calls += 1
        raise RuntimeError("synthetic SMTP down")


class _ZeroAcceptBackend:
    calls = 0

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def send_messages(self, messages: list[Any]) -> int:
        type(self).calls += 1
        return 0


class _MidSendReissueBackend:
    """Accepts the send, but rotates the credential while the send is
    "in flight" — a reissue landing between acceptance and activation."""

    calls = 0

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def send_messages(self, messages: list[Any]) -> int:
        type(self).calls += 1
        user = User.objects.get(email="member@example.com")
        onboarding.rotate_onboarding(user, "Rq67tv")
        user.save()
        return 1  # the relay accepted the (now stale) credential


# ``django.core.mail.get_connection`` resolves the configured backend with
# ``import_string``, so the synthetic backends are referenced by import
# path, not by class object. Pytest imports this module as
# ``test_account_onboarding`` (no package ``__init__``), and the class-level
# ``calls`` counters above are shared because that is the same module
# object.
FAILING_BACKEND = "test_account_onboarding._FailingSMTPBackend"
ZERO_ACCEPT_BACKEND = "test_account_onboarding._ZeroAcceptBackend"
MID_SEND_BACKEND = "test_account_onboarding._MidSendReissueBackend"


def _pending_user(email: str, temporary: str, *, hours: float = 24.0, active: bool = True) -> User:
    """A pending onboarding account with a known temporary credential.

    ``active=True`` models an ACCEPTED delivery (the account was activated
    by the post-commit send and is pending its forced change);
    ``active=False`` models a failed/pending delivery that must not be
    able to sign in.
    """
    user = User.objects.create_user(email=email, password=temporary, is_active=active)
    user.onboarding_password_expires_at = timezone.now() + timedelta(hours=hours)
    user.save(update_fields=["onboarding_password_expires_at"])
    return user


def _stale_signed(digest: str, age_seconds: int) -> str:
    """A valid-signature token carrying an embedded OLD timestamp."""
    signer = TimestampSigner(salt=onboarding.PREFILL_SIGNER_SALT)
    old_ts = int(time.time()) - age_seconds
    inner = f"{digest}{signer.sep}{b62_encode(old_ts)}"
    return Signer.sign(signer, inner)


def _login(client: Client, email: str, password: str) -> Any:
    return client.post(LOGIN_URL, {"username": email, "password": password})


def _reissue_url(user: User) -> str:
    return f"/admin/accounts/user/{user.pk}/onboarding-reissue/"


# --- temporary credential generation ----------------------------------------


def test_default_generator_produces_six_char_mixed_alphanumeric() -> None:
    for _ in range(5):
        value = onboarding.generate_temporary_password()
        assert len(value) == onboarding.TEMPORARY_PASSWORD_LENGTH
        assert value.isalnum()
        assert any(ch.isalpha() for ch in value)
        assert any(ch.isdigit() for ch in value)
        assert set(value) <= set(string.ascii_letters + string.digits)


def test_generate_rejects_wrong_length_injection() -> None:
    with pytest.raises(ValueError):
        onboarding.generate_temporary_password(generate=lambda: "short")
    with pytest.raises(ValueError):
        onboarding.generate_temporary_password(generate=lambda: "toolong1")


# --- add-form prefill ---------------------------------------------------------


@pytest.mark.django_db
def test_add_get_prefills_both_controls_with_same_generated_value(
    admin_client: Client, email_enabled: None, fixed_generator: None
) -> None:
    response = admin_client.get(ADD_URL)
    assert response.status_code == 200
    html = response.content.decode()
    assert _input_value(html, "id_password1") == "Ab12cd"
    assert _input_value(html, "id_password2") == "Ab12cd"
    # No-store: the add form carries the generated credential.
    assert "no-store" in response["Cache-Control"]
    # The rendered help explains the temporary credential.
    assert "temporary six-character password" in html
    # The server session holds only the signed digest, never plaintext.
    session = admin_client.session
    assert onboarding.PREFILL_PROOF_SESSION_KEY in session
    assert "Ab12cd" not in str(session)
    assert "Ab12cd" not in str(session[onboarding.PREFILL_PROOF_SESSION_KEY])

    # A fresh GET generates a fresh value (deterministic injection).
    second = admin_client.get(ADD_URL)
    html2 = second.content.decode()
    assert _input_value(html2, "id_password1") == "Zz98ab"
    assert _input_value(html2, "id_password2") == "Zz98ab"


@pytest.mark.django_db
def test_add_get_without_email_still_prefills_with_setup_guidance(
    admin_client: Client, fixed_generator: None
) -> None:
    """Disabled transport: the prefill is still shown on every GET, with
    clear nearby guidance that user creation requires SMTP setup."""
    response = admin_client.get(ADD_URL)
    assert response.status_code == 200
    html = response.content.decode()
    assert _input_value(html, "id_password1") == "Ab12cd"
    assert _input_value(html, "id_password2") == "Ab12cd"
    assert "no-store" in response["Cache-Control"]
    assert "account email (SMTP) transport" in html
    assert "every submission on this page is refused and no account is created" in html
    # The signed digest (never plaintext) is still session-bound.
    session = admin_client.session
    assert onboarding.PREFILL_PROOF_SESSION_KEY in session
    assert "Ab12cd" not in str(session)


# --- proof negative paths -----------------------------------------------------


@pytest.mark.django_db
def test_add_post_edited_six_char_value_rejected(
    admin_client: Client, email_enabled: None, fixed_generator: None
) -> None:
    admin_client.get(ADD_URL)
    response = admin_client.post(
        ADD_URL,
        {"email": "member@example.com", "password1": "Xb12cd", "password2": "Xb12cd"},
    )
    assert response.status_code == 200
    assert "no longer matches the generated value" in response.content.decode()
    assert not User.objects.filter(email="member@example.com").exists()
    assert mail.outbox == []


@pytest.mark.django_db
def test_add_post_tampered_proof_rejected(
    admin_client: Client, email_enabled: None, fixed_generator: None
) -> None:
    admin_client.get(ADD_URL)
    session = admin_client.session
    session[onboarding.PREFILL_PROOF_SESSION_KEY] = "tampered-proof"
    session.save()
    response = admin_client.post(
        ADD_URL,
        {"email": "member@example.com", "password1": "Ab12cd", "password2": "Ab12cd"},
    )
    assert response.status_code == 200
    assert not User.objects.filter(email="member@example.com").exists()


@pytest.mark.django_db
def test_add_post_expired_proof_rejected(
    admin_client: Client, email_enabled: None, fixed_generator: None
) -> None:
    admin_client.get(ADD_URL)
    session = admin_client.session
    nonce = session[onboarding.NONCE_SESSION_KEY]
    digest = hashlib.sha256(f"Ab12cd:{nonce}".encode()).hexdigest()
    old = _stale_signed(digest, age_seconds=2 * 3600)
    session[onboarding.PREFILL_PROOF_SESSION_KEY] = old
    session.save()
    response = admin_client.post(
        ADD_URL,
        {"email": "member@example.com", "password1": "Ab12cd", "password2": "Ab12cd"},
    )
    assert response.status_code == 200
    assert not User.objects.filter(email="member@example.com").exists()


@pytest.mark.django_db
def test_add_post_unbound_proof_rejected(
    admin_client: Client, email_enabled: None, fixed_generator: None
) -> None:
    admin_client.get(ADD_URL)
    session = admin_client.session
    # A valid signature over a DIFFERENT session nonce: unbound.
    other_nonce = "0" * 32
    digest = hashlib.sha256(f"Ab12cd:{other_nonce}".encode()).hexdigest()
    session[onboarding.PREFILL_PROOF_SESSION_KEY] = TimestampSigner(
        salt=onboarding.PREFILL_SIGNER_SALT
    ).sign(digest)
    session.save()
    response = admin_client.post(
        ADD_URL,
        {"email": "member@example.com", "password1": "Ab12cd", "password2": "Ab12cd"},
    )
    assert response.status_code == 200
    assert not User.objects.filter(email="member@example.com").exists()


# --- disabled email: every add POST refused, nothing written -------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("password1", "password2"),
    [("Ab12cd", "Ab12cd"), ("ManualSecret123", "ManualSecret123"), ("short", "short")],
    ids=["generated", "manual-normal", "manual-weak"],
)
def test_add_post_refused_when_email_disabled_creates_no_account(
    admin_client: Client, fixed_generator: None, password1: str, password2: str
) -> None:
    """Without account email the Administration add is refused for
    generated or manually entered (normal or weak) credentials, before
    any account is written; nothing is sent."""
    admin_client.get(ADD_URL)
    response = admin_client.post(
        ADD_URL, {"email": "member@example.com", "password1": password1, "password2": password2}
    )
    assert response.status_code == 200
    html = response.content.decode()
    assert "requires the account email" in html
    assert not User.objects.filter(email="member@example.com").exists()
    assert mail.outbox == []


# --- enabled email: generated AND manual adds deliver --------------------------


@pytest.mark.django_db
def test_add_post_generated_commits_inactive_then_single_send_activates(
    admin_client: Client,
    email_enabled: None,
    fixed_generator: None,
    django_capture_on_commit_callbacks: Any,
) -> None:
    admin_client.get(ADD_URL)
    with django_capture_on_commit_callbacks(execute=True):
        response = admin_client.post(
            ADD_URL,
            {
                "email": "member@example.com",
                "password1": "Ab12cd",
                "password2": "Ab12cd",
                "is_staff": "on",
            },
        )
        assert response.status_code == 302
        # Committed BEFORE any send: the account is pending/inactive with
        # only the password hash and nonsecret metadata, and no message
        # has been handed to the backend yet.
        user = User.objects.get(email="member@example.com")
        assert user.is_active is False
        assert user.is_staff is True
        assert user.check_password("Ab12cd")
        assert "Ab12cd" not in user.password
        assert user.onboarding_password_expires_at is not None
        assert timezone.now() + timedelta(hours=23) < user.onboarding_password_expires_at
        assert user.onboarding_password_expires_at <= timezone.now() + timedelta(
            hours=24, seconds=1
        )
        assert mail.outbox == []
        # The session proof is consumed.
        assert onboarding.PREFILL_PROOF_SESSION_KEY not in admin_client.session

    # Exactly one post-commit send, then activation.
    user.refresh_from_db()
    assert user.is_active is True
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.from_email == FROM_EMAIL
    assert message.to == ["member@example.com"]
    body = message.body
    assert f"{BASE_URL}/login/" in body
    assert "member@example.com" in body
    assert "Ab12cd" in body


@pytest.mark.django_db
def test_add_post_manual_normal_password_is_onboarding_credential(
    admin_client: Client,
    email_enabled: None,
    fixed_generator: None,
    django_capture_on_commit_callbacks: Any,
) -> None:
    """With account email enabled a manually entered normal-validator
    password is ALSO an onboarding credential: inactive pending account,
    exactly one post-commit send, activation only on acceptance, forced
    first change."""
    admin_client.get(ADD_URL)
    with django_capture_on_commit_callbacks(execute=True):
        response = admin_client.post(
            ADD_URL,
            {
                "email": "member@example.com",
                "password1": "ManualSecret123",
                "password2": "ManualSecret123",
            },
        )
        assert response.status_code == 302
        # Committed BEFORE the send: inactive/pending with the manual
        # credential (hashed) and nonsecret expiry metadata.
        user = User.objects.get(email="member@example.com")
        assert user.is_active is False
        assert user.check_password("ManualSecret123")
        assert "ManualSecret123" not in user.password
        assert user.onboarding_password_expires_at is not None
        assert mail.outbox == []
    # The accepted send activates; the manual credential (never rendered
    # by the app) is the emailed login detail.
    user.refresh_from_db()
    assert user.is_active is True
    assert len(mail.outbox) == 1
    assert "ManualSecret123" in mail.outbox[0].body
    # Forced first change: the manual credential is a temporary one.
    client = Client()
    assert _login(client, "member@example.com", "ManualSecret123").status_code == 302
    assert client.get("/profile/").status_code == 302
    assert client.get(PW_URL).status_code == 200
    response = client.post(
        PW_URL,
        {
            "old_password": "ManualSecret123",
            "new_password1": "brand-new-passw0rd",
            "new_password2": "brand-new-passw0rd",
        },
    )
    assert response.status_code == 302
    user.refresh_from_db()
    assert user.check_password("brand-new-passw0rd")
    assert user.onboarding_password_expires_at is None


@pytest.mark.django_db
def test_add_post_weak_manual_password_still_rejected(
    admin_client: Client, email_enabled: None, fixed_generator: None
) -> None:
    admin_client.get(ADD_URL)
    response = admin_client.post(
        ADD_URL,
        {"email": "member@example.com", "password1": "short", "password2": "short"},
    )
    assert response.status_code == 200
    assert not User.objects.filter(email="member@example.com").exists()


# --- post-commit delivery ------------------------------------------------------


@pytest.mark.django_db
def test_add_post_delivery_failure_leaves_inactive_denied_and_scoped(
    admin_client: Client,
    fixed_generator: None,
    django_capture_on_commit_callbacks: Any,
) -> None:
    _FailingSMTPBackend.calls = 0
    backend = _FailingSMTPBackend
    with override_settings(
        ACCOUNT_EMAIL_ENABLED=True,
        PUBLIC_BASE_URL=BASE_URL,
        DEFAULT_FROM_EMAIL=FROM_EMAIL,
        EMAIL_BACKEND=FAILING_BACKEND,
    ):
        mail.outbox = []
        admin_client.get(ADD_URL)
        with django_capture_on_commit_callbacks(execute=True):
            response = admin_client.post(
                ADD_URL,
                {
                    "email": "member@example.com",
                    "password1": "Ab12cd",
                    "password2": "Ab12cd",
                },
            )
        assert response.status_code == 302
        user = User.objects.get(email="member@example.com")
        assert user.is_active is False
        assert backend.calls == 1  # no automatic retry
        # The correct temporary credential CANNOT establish a session
        # while the account is inactive after a failed send.
        assert authenticate(username=user.email, password="Ab12cd") is None
        denied = _login(Client(), user.email, "Ab12cd")
        assert denied.status_code == 200
        assert "Enter a valid email address and password." in denied.content.decode()
        assert denied.wsgi_request.user.is_anonymous
        # The change page (redirect target) shows a nonsecret warning.
        change_page = admin_client.get(response["Location"])
        html = change_page.content.decode()
        assert "could not be confirmed as delivered" in html
        assert "cannot sign in yet" in html
        assert "Ab12cd" not in html
        # The status is scoped to THIS account: another pending account's
        # page shows no delivery-failure warning.
        other = _pending_user("other@example.com", "Zz98ab")
        other_page = admin_client.get(f"/admin/accounts/user/{other.pk}/change/")
        assert "could not be confirmed as delivered" not in other_page.content.decode()


@pytest.mark.django_db
def test_add_post_zero_acceptance_leaves_inactive(
    admin_client: Client,
    fixed_generator: None,
    django_capture_on_commit_callbacks: Any,
) -> None:
    _ZeroAcceptBackend.calls = 0
    backend = _ZeroAcceptBackend
    with override_settings(
        ACCOUNT_EMAIL_ENABLED=True,
        PUBLIC_BASE_URL=BASE_URL,
        DEFAULT_FROM_EMAIL=FROM_EMAIL,
        EMAIL_BACKEND=ZERO_ACCEPT_BACKEND,
    ):
        admin_client.get(ADD_URL)
        with django_capture_on_commit_callbacks(execute=True):
            admin_client.post(
                ADD_URL,
                {
                    "email": "member@example.com",
                    "password1": "Ab12cd",
                    "password2": "Ab12cd",
                },
            )
        user = User.objects.get(email="member@example.com")
        assert user.is_active is False
        assert authenticate(username=user.email, password="Ab12cd") is None
        assert backend.calls == 1  # no automatic retry
        change_page = admin_client.get(f"/admin/accounts/user/{user.pk}/change/")
        assert "could not be confirmed as delivered" in change_page.content.decode()


@pytest.mark.django_db
def test_delivery_url_never_derived_from_request_host(
    admin_client: Client,
    email_enabled: None,
    fixed_generator: None,
    django_capture_on_commit_callbacks: Any,
) -> None:
    admin_client.get(ADD_URL)
    with django_capture_on_commit_callbacks(execute=True):
        # The request Host is the test server, which must NOT appear in
        # the emailed login URL (canonical configured base URL only).
        admin_client.post(
            ADD_URL,
            {
                "email": "member@example.com",
                "password1": "Ab12cd",
                "password2": "Ab12cd",
            },
        )
    assert len(mail.outbox) == 1
    assert "testserver" not in mail.outbox[0].body
    assert f"{BASE_URL}/login/" in mail.outbox[0].body


@pytest.mark.django_db
def test_cli_createsuperuser_baseline_unaffected(
    admin_client: Client, email_enabled: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    mail.outbox = []
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "CliAdminPass123")
    call_command(
        "createsuperuser",
        "--noinput",
        email="cli-admin@example.com",
    )
    user = User.objects.get(email="cli-admin@example.com")
    assert user.is_active is True
    assert user.is_superuser is True
    assert user.onboarding_password_expires_at is None
    assert user.check_password("CliAdminPass123")
    assert mail.outbox == []


# --- reissue -------------------------------------------------------------------


@pytest.mark.django_db
def test_reissue_rotates_credential_and_sends_once(
    admin_client: Client,
    email_enabled: None,
    monkey_value: Any,
    django_capture_on_commit_callbacks: Any,
) -> None:
    user = _pending_user("member@example.com", "Ab12cd")
    reissue_url = _reissue_url(user)
    # GET: confirmation page, no secret.
    page = admin_client.get(reissue_url)
    assert page.status_code == 200
    html = page.content.decode()
    assert "member@example.com" in html
    assert "NEW temporary six-character password" in html
    assert "Ab12cd" not in html

    # POST: rotate + exactly one send of the new credential. The account
    # is active (accepted delivery) until the rotation commits; the
    # accepted send activates it for the NEW generation.
    monkey_value("Zz98ab")
    with django_capture_on_commit_callbacks(execute=True):
        response = admin_client.post(reissue_url)
    assert response.status_code == 302
    user.refresh_from_db()
    assert user.is_active is True  # accepted by the locmem backend
    assert user.check_password("Zz98ab")
    assert not user.check_password("Ab12cd")  # old credential invalidated
    assert len(mail.outbox) == 1
    assert "Zz98ab" in mail.outbox[0].body
    assert "Ab12cd" not in mail.outbox[0].body
    # Audit entry without the secret.
    entries = LogEntry.objects.filter(object_id=str(user.pk))
    assert any("Reissued onboarding login details" in (e.change_message or "") for e in entries)
    assert all(
        "Ab12cd" not in (e.change_message or "") and "Zz98ab" not in (e.change_message or "")
        for e in entries
    )


@pytest.mark.django_db
def test_reissue_requires_change_permission(admin_client: Client, email_enabled: None) -> None:
    user = _pending_user("member@example.com", "Ab12cd")
    reissue_url = _reissue_url(user)
    staff_only = User.objects.create_user(
        email="staff-only@example.com",
        password="staff-pass-058",
        is_staff=True,
    )
    plain_client = Client()
    plain_client.force_login(staff_only)
    assert plain_client.get(reissue_url).status_code == 403
    assert plain_client.post(reissue_url).status_code == 403
    user.refresh_from_db()
    assert user.check_password("Ab12cd")  # untouched
    assert mail.outbox == []


@pytest.mark.django_db
def test_reissue_refused_for_non_pending_account(admin_client: Client, email_enabled: None) -> None:
    normal = User.objects.create_user(email="normal@example.com", password="NormalPass123")
    reissue_url = _reissue_url(normal)
    response = admin_client.get(reissue_url)
    assert response.status_code == 302
    assert response["Location"] == f"/admin/accounts/user/{normal.pk}/change/"
    normal.refresh_from_db()
    assert normal.is_active is True
    assert normal.onboarding_password_expires_at is None
    assert mail.outbox == []


@pytest.mark.django_db
def test_reissue_failure_keeps_inactive_denied_and_allows_retry(
    admin_client: Client,
    monkey_value: Any,
    django_capture_on_commit_callbacks: Any,
) -> None:
    _ZeroAcceptBackend.calls = 0
    backend = _ZeroAcceptBackend
    with override_settings(
        ACCOUNT_EMAIL_ENABLED=True,
        PUBLIC_BASE_URL=BASE_URL,
        DEFAULT_FROM_EMAIL=FROM_EMAIL,
        EMAIL_BACKEND=ZERO_ACCEPT_BACKEND,
    ):
        user = _pending_user("member@example.com", "Ab12cd")
        reissue_url = _reissue_url(user)
        monkey_value("Mn56yz")
        with django_capture_on_commit_callbacks(execute=True):
            response = admin_client.post(reissue_url)
        assert response.status_code == 302
        user.refresh_from_db()
        # The new failed delivery leaves the account INACTIVE: even the
        # freshly issued credential cannot establish a session.
        assert user.is_active is False
        assert user.check_password("Mn56yz")
        assert authenticate(username=user.email, password="Mn56yz") is None
        assert backend.calls == 1  # no automatic retry
        change_page = admin_client.get(response["Location"])
        html = change_page.content.decode()
        assert "could not be confirmed as delivered" in html
        assert "reissue again" in html
        # Recovery: an explicit second reissue rotates again; the failed
        # delivery keeps the account inactive.
        monkey_value("Qr78kt")
        with django_capture_on_commit_callbacks(execute=True):
            admin_client.post(reissue_url)
        user.refresh_from_db()
        assert user.is_active is False
        assert user.check_password("Qr78kt")
        assert not user.check_password("Mn56yz")
        assert backend.calls == 2


# --- stale / superseded callbacks (exact-generation activation) -----------------


@pytest.mark.django_db
def test_stale_callback_after_reissue_does_not_send_activate_or_claim(
    admin_client: Client,
    email_enabled: None,
    fixed_generator: None,
    monkey_value: Any,
    django_capture_on_commit_callbacks: Any,
) -> None:
    """Out-of-order delivery: the original add's post-commit send runs
    only AFTER an explicit reissue rotated the credential. The stale
    callback must not email the stale credential, must not touch the
    newer generation and must not claim delivery."""
    admin_client.get(ADD_URL)
    # Capture the add's on_commit callback WITHOUT executing it.
    with django_capture_on_commit_callbacks(execute=False) as stale:
        response = admin_client.post(
            ADD_URL,
            {"email": "member@example.com", "password1": "Ab12cd", "password2": "Ab12cd"},
        )
    assert response.status_code == 302
    assert len(stale) == 1
    user = User.objects.get(email="member@example.com")
    assert user.is_active is False
    assert user.check_password("Ab12cd")

    # The administrator reissues BEFORE the original delivery ran: the
    # reissue's own send runs and activates the NEW generation.
    monkey_value("Zz98ab")
    with django_capture_on_commit_callbacks(execute=True):
        admin_client.post(_reissue_url(user))
    user.refresh_from_db()
    assert user.check_password("Zz98ab")
    assert user.is_active is True
    assert len(mail.outbox) == 1  # only the reissue send
    assert "Ab12cd" not in mail.outbox[0].body

    # Now the stale callback runs: superseded -> no send, no state
    # change, no delivery claim.
    before = len(mail.outbox)
    stale[0]()
    user.refresh_from_db()
    assert len(mail.outbox) == before
    assert user.check_password("Zz98ab")
    assert user.is_active is True
    # The stale callback reported superseded, scoped to this account —
    # it did not claim delivery for the newer credential.
    session = admin_client.session
    assert session[onboarding.DELIVERY_STATUS_SESSION_KEY][str(user.pk)] == "superseded"


@pytest.mark.django_db
def test_accepted_send_superseded_by_reissue_in_flight_does_not_activate(
    admin_client: Client,
    fixed_generator: None,
    django_capture_on_commit_callbacks: Any,
) -> None:
    """The relay accepts the send, but a reissue lands between
    acceptance and activation: the conditional exact-generation update
    matches zero rows — no activation of the newer credential, no
    delivery claim, old credential invalid."""
    _MidSendReissueBackend.calls = 0
    backend = _MidSendReissueBackend
    with override_settings(
        ACCOUNT_EMAIL_ENABLED=True,
        PUBLIC_BASE_URL=BASE_URL,
        DEFAULT_FROM_EMAIL=FROM_EMAIL,
        EMAIL_BACKEND=MID_SEND_BACKEND,
    ):
        admin_client.get(ADD_URL)
        with django_capture_on_commit_callbacks(execute=True):
            admin_client.post(
                ADD_URL,
                {
                    "email": "member@example.com",
                    "password1": "Ab12cd",
                    "password2": "Ab12cd",
                },
            )
        assert backend.calls == 1
        user = User.objects.get(email="member@example.com")
        # The in-flight reissue rotated the credential; the accepted
        # (stale) send did NOT activate the newer generation.
        assert user.is_active is False
        assert user.check_password("Rq67tv")
        assert not user.check_password("Ab12cd")  # old credential invalid
        assert authenticate(username=user.email, password="Rq67tv") is None
        # The status is recorded as superseded, scoped to this account:
        # the accepted (stale) send claimed nothing for the newer
        # credential.
        session = admin_client.session
        statuses = session[onboarding.DELIVERY_STATUS_SESSION_KEY]
        assert statuses[str(user.pk)] == "superseded"
        # No delivery claim is rendered on the account page.
        change_page = admin_client.get(f"/admin/accounts/user/{user.pk}/change/")
        assert "login details were delivered by email" not in change_page.content.decode()


# --- temporary lifecycle and enforcement --------------------------------------


@pytest.mark.django_db
def test_expired_temporary_cannot_establish_member_session() -> None:
    # Accepted long ago (active), now expired.
    user = _pending_user("member@example.com", "Ab12cd", hours=-1, active=True)
    assert authenticate(username=user.email, password="Ab12cd") is None
    client = Client()
    response = _login(client, user.email, "Ab12cd")
    assert response.status_code == 200
    assert "Enter a valid email address and password." in response.content.decode()
    # No session was established.
    assert response.wsgi_request.user.is_anonymous


@pytest.mark.django_db
def test_expired_temporary_cannot_establish_admin_session() -> None:
    user = User.objects.create_user(
        email="staff-pending@example.com",
        password="Ab12cd",
        is_active=True,  # accepted delivery, now expired
        is_staff=True,
    )
    user.onboarding_password_expires_at = timezone.now() - timedelta(hours=1)
    user.save(update_fields=["onboarding_password_expires_at"])
    assert authenticate(username=user.email, password="Ab12cd") is None
    client = Client()
    response = client.post(ADMIN_LOGIN_URL, {"username": user.email, "password": "Ab12cd"})
    assert response.status_code == 200
    assert response.wsgi_request.user.is_anonymous


@pytest.mark.django_db
def test_failed_delivery_inactive_cannot_establish_admin_session() -> None:
    # A pending account whose delivery failed is inactive; even a staff
    # account with the CORRECT unexpired credential is refused at the
    # Administration login.
    user = User.objects.create_user(
        email="staff-undelivered@example.com",
        password="Ab12cd",
        is_active=False,
        is_staff=True,
    )
    user.onboarding_password_expires_at = timezone.now() + timedelta(hours=24)
    user.save(update_fields=["onboarding_password_expires_at"])
    assert authenticate(username=user.email, password="Ab12cd") is None
    client = Client()
    response = client.post(ADMIN_LOGIN_URL, {"username": user.email, "password": "Ab12cd"})
    assert response.status_code == 200
    assert response.wsgi_request.user.is_anonymous


@pytest.mark.django_db
def test_within_expiry_login_restricted_to_password_page() -> None:
    user = _pending_user("member@example.com", "Ab12cd")  # accepted: active
    client = Client()
    response = _login(client, user.email, "Ab12cd")
    assert response.status_code == 302
    # The forced-change gate routes everything to the password page.
    for path in ["/", "/profile/", "/assets/", "/reservations/", "/tokens/"]:
        denied = client.get(path)
        assert denied.status_code == 302, path
        assert denied["Location"] == PW_URL, path
    # Escape attempts on mutations are blocked the same way.
    blocked = client.post("/tokens/new/")
    assert blocked.status_code == 302
    assert blocked["Location"] == PW_URL
    # The password page itself is admitted and shows the temporary notice.
    page = client.get(PW_URL)
    assert page.status_code == 200
    assert "temporary password" in page.content.decode()
    # Necessary static/branding/health surfaces stay reachable —
    # including the absolute "/static/" prefix.
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 200
    branding = client.get("/branding/logo")
    assert branding.status_code in (200, 404)
    static_js = client.get("/static/web/admin-form-guidance.js")
    assert static_js.status_code == 200
    # A path merely STARTING with "static" must still be gated.
    fake = client.get("/staticlike/")
    assert fake.status_code == 302
    # The session-authenticated API is not reachable.
    api = client.get("/api/v1/me/")
    assert api.status_code == 302
    assert api["Location"] == PW_URL


def test_onboarding_allowed_path_allowlist() -> None:
    assert onboarding.is_onboarding_allowed_path("/profile/password/")
    assert onboarding.is_onboarding_allowed_path("/logout/")
    assert onboarding.is_onboarding_allowed_path("/login/")
    assert onboarding.is_onboarding_allowed_path("/health/live")
    assert onboarding.is_onboarding_allowed_path("/health/ready")
    assert onboarding.is_onboarding_allowed_path("/branding/logo")
    assert onboarding.is_onboarding_allowed_path("/static/web/site.css")
    assert not onboarding.is_onboarding_allowed_path("/staticlike/")
    assert not onboarding.is_onboarding_allowed_path("/")
    assert not onboarding.is_onboarding_allowed_path("/profile/")


@pytest.mark.django_db
def test_expired_session_is_terminated() -> None:
    user = _pending_user("member@example.com", "Ab12cd")  # accepted: active
    client = Client()
    assert _login(client, user.email, "Ab12cd").status_code == 302
    # The session outlives the credential: expiry arrives mid-session.
    user.onboarding_password_expires_at = timezone.now() - timedelta(minutes=5)
    user.save(update_fields=["onboarding_password_expires_at"])
    response = client.get(PW_URL)
    assert response.status_code == 302
    assert response["Location"].startswith(LOGIN_URL)
    # The session is terminated: even the password page is no longer admitted.
    again = client.get(PW_URL)
    assert again.status_code == 302
    assert again["Location"].startswith(LOGIN_URL)


@pytest.mark.django_db
def test_successful_change_clears_state_keeps_session_and_invalidates_others() -> None:
    user = _pending_user("member@example.com", "Ab12cd")  # accepted: active
    client = Client()
    other = Client()
    _login(client, user.email, "Ab12cd")
    _login(other, user.email, "Ab12cd")
    assert other.get("/profile/").status_code == 302  # gate, not a data page
    response = client.post(
        PW_URL,
        {
            "old_password": "Ab12cd",
            "new_password1": "brand-new-passw0rd",
            "new_password2": "brand-new-passw0rd",
        },
    )
    assert response.status_code == 302
    assert response["Location"] == "/profile/"
    user.refresh_from_db()
    assert user.is_active is True
    assert user.onboarding_password_expires_at is None
    assert user.check_password("brand-new-passw0rd")
    # The old temporary credential is gone.
    assert authenticate(username=user.email, password="Ab12cd") is None
    # Current session continues with full access.
    assert client.get("/profile/").status_code == 200
    assert client.get("/assets/").status_code == 200
    # The other session for the account is no longer admitted (the stored
    # session hash no longer matches the rotated password hash).
    denied = other.get("/profile/")
    assert denied.status_code == 302
    assert denied["Location"].startswith(LOGIN_URL)


@pytest.mark.django_db
def test_forced_change_uses_normal_validators_no_weakened_path() -> None:
    user = _pending_user("member@example.com", "Ab12cd")  # accepted: active
    client = Client()
    _login(client, user.email, "Ab12cd")
    for weak in ["short", "password", "12345678"]:
        response = client.post(
            PW_URL,
            {
                "old_password": "Ab12cd",
                "new_password1": weak,
                "new_password2": weak,
            },
        )
        assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password("Ab12cd")  # unchanged
    assert user.is_active is True  # still pending (delivery was accepted)


@pytest.mark.django_db
def test_no_auto_grants_on_onboarding_creation(
    admin_client: Client,
    email_enabled: None,
    fixed_generator: None,
    django_capture_on_commit_callbacks: Any,
) -> None:
    admin_client.get(ADD_URL)
    with django_capture_on_commit_callbacks(execute=True):
        admin_client.post(
            ADD_URL,
            {
                "email": "member@example.com",
                "password1": "Ab12cd",
                "password2": "Ab12cd",
                "is_staff": "on",
                "is_superuser": "on",
            },
        )
    user = User.objects.get(email="member@example.com")
    assert user.groups.count() == 0
    assert user.user_permissions.count() == 0
    assert user.api_tokens.count() == 0
    assert user.is_staff is True  # exactly as submitted
    assert user.is_superuser is True
    assert user.is_service_account is False


@pytest.mark.django_db
def test_shared_login_abuse_budget_still_applies_to_onboarding_logins() -> None:
    user = _pending_user("member@example.com", "Ab12cd")  # accepted: active
    client = Client()
    statuses = [_login(client, user.email, "Ab12cd").status_code for _ in range(11)]
    # The existing per-identity login budget (10/window) trips.
    assert 429 in statuses
    assert all(status in (200, 302, 429) for status in statuses)
    user.refresh_from_db()
    assert user.is_active is True  # unchanged by repeated logins
