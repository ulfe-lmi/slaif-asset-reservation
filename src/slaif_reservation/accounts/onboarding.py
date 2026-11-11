"""Administrator account onboarding (SAR-055 / SAR-056).

Implements the selected M-ACCOUNT-ONBOARDING workflow around the existing
Django account model:

* a fresh six-character temporary credential is generated with a CSPRNG
  and prefilled in the Administration add-user form on every GET (with
  clear setup guidance while the account-email transport is disabled);
* the form carries a short-lived signed digest (bound to the creating
  administrator's session) proving the submitted six-character value was
  generated, so edited, tampered, expired or unbound values are rejected
  while manually entered normal-length passwords keep the full validator
  set;
* while account email is enabled, EVERY valid add submission (the
  generated prefill or a manually entered normal-validator password)
  commits the account inactive/pending with only a password hash, and
  exactly one plain-text login-details email (canonical configured
  HTTPS base URL + login path, account email identifier, temporary
  password) is sent after the commit; the account is activated only when
  the SMTP backend reports acceptance, and stays inactive on failure,
  zero or ambiguous results (no automatic retry). While account email is
  disabled every add submission is refused before any account is
  written;
* activation is exact-generation: the post-commit send may only activate
  the account while it still holds the very password hash and pending
  expiry/generation that was sent, so a reissue supersedes a scheduled
  or in-flight send and a stale accepted callback can never activate a
  newer pending credential or claim its delivery;
* a manual, permission-checked reissue control rotates the credential
  (making the account inactive again while delivery is pending) and
  repeats the same single post-commit send;
* the temporary credential may establish a session only after the
  account is active (delivery accepted); it expires within 24 hours and
  cannot establish a new session after expiry (authentication backend),
  and a session gate allows an in-onboarding user only the
  password-change page, logout and the static/branding/health surfaces.

Nothing here persists or logs a plaintext credential, derives a URL from
the request Host, sends to a real relay in tests, or grants any group,
booking, administration or API-token permission.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import string
from collections.abc import Callable
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.core import mail
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.utils import timezone

from slaif_reservation.accounts.models import User

# --- constants -----------------------------------------------------------

#: Length of the generated onboarding credential (narrow exception only).
TEMPORARY_PASSWORD_LENGTH = 6

#: The generated credential can never establish a session after this.
TEMPORARY_PASSWORD_TTL = timedelta(hours=24)

#: The signed prefill proof expires quickly; the admin re-opens the form
#: to get a fresh value instead.
PREFILL_PROOF_MAX_AGE_SECONDS = 30 * 60

PREFILL_SIGNER_SALT = "slaif-reservation/onboarding-prefill/1"
NONCE_SESSION_KEY = "slaif_onboarding_prefill_nonce"
PREFILL_PROOF_SESSION_KEY = "slaif_onboarding_prefill_proof"
DELIVERY_STATUS_SESSION_KEY = "slaif_onboarding_delivery_status"

# Letters plus digits; the default generator additionally requires at
# least one letter and one digit.
TEMPORARY_PASSWORD_ALPHABET = string.ascii_letters + string.digits

# Login path appended to the canonical configured base URL (never derived
# from the request Host).
LOGIN_PATH = "/login/"

# Absolute path prefixes for the in-onboarding session gate (note
# the leading slash on "/static/").
_ONBOARDING_EXACT_PATHS = frozenset(
    {
        "/profile/password/",
        "/logout/",
        "/login/",
        "/health/live",
        "/health/ready",
    }
)
_ONBOARDING_STATIC_PREFIXES = ("/branding/", "/static/")


# --- temporary credential generation --------------------------------------


def _default_generate() -> str:
    random = secrets.SystemRandom()
    alphabet = TEMPORARY_PASSWORD_ALPHABET
    while True:
        value = "".join(random.choices(alphabet, k=TEMPORARY_PASSWORD_LENGTH))
        if any(ch.isalpha() for ch in value) and any(ch.isdigit() for ch in value):
            return value


def generate_temporary_password(*, generate: Callable[[], str] | None = None) -> str:
    """Return a fresh six-character mixed-alphanumeric credential.

    ``generate`` is an injection point for deterministic tests; whatever
    it returns is still required to be exactly six characters. The
    default is CSPRNG-based (``secrets``).
    """
    value = generate() if generate is not None else _default_generate()
    if not isinstance(value, str) or len(value) != TEMPORARY_PASSWORD_LENGTH:
        msg = "Onboarding credentials must be exactly six characters."
        raise ValueError(msg)
    return value


# --- signed prefill proof --------------------------------------------------


def _digest_for(value: str, nonce: str) -> str:
    return hashlib.sha256(f"{value}:{nonce}".encode()).hexdigest()


def session_nonce(session: Any) -> str:
    """Return (creating if absent) the per-administrator-session nonce."""
    nonce = session.get(NONCE_SESSION_KEY)
    if not isinstance(nonce, str) or not nonce:
        nonce = secrets.token_hex(16)
        session[NONCE_SESSION_KEY] = nonce
    return nonce


def sign_prefill_proof(value: str, nonce: str) -> str:
    """Short-lived signed digest of a generated credential.

    Only a SHA-256 digest (never the credential) is signed; the digest
    mixes in the per-session nonce, so the proof is bound to the
    creating administrator's session.
    """
    signer = TimestampSigner(salt=PREFILL_SIGNER_SALT)
    return signer.sign(_digest_for(value, nonce))


def verify_prefill_proof(proof: str | None, nonce: str | None, value: str) -> bool:
    """True only when ``value`` matches the still-valid signed digest."""
    if not proof or not nonce:
        return False
    signer = TimestampSigner(salt=PREFILL_SIGNER_SALT)
    try:
        digest = signer.unsign(proof, max_age=PREFILL_PROOF_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return False
    return bool(hmac.compare_digest(digest, _digest_for(value, nonce)))


# --- onboarding state --------------------------------------------------------


def is_pending_onboarding(user: Any) -> bool:
    """True while the account is pending its first forced change."""
    expires_at = getattr(user, "onboarding_password_expires_at", None)
    return expires_at is not None


def temporary_credential_expired(user: Any, *, now: Any | None = None) -> bool:
    """True when a pending account's temporary credential has expired."""
    expires_at = getattr(user, "onboarding_password_expires_at", None)
    if expires_at is None:
        return False
    return bool((now or timezone.now()) >= expires_at)


def start_onboarding(
    user: User,
    temporary_password: str,
    *,
    now: Any | None = None,
) -> User:
    """Mark ``user`` pending with a hashed temporary credential.

    The plaintext is used only to hash; it is never stored, logged or
    returned. The account is inactive until the credential is accepted
    and changed.
    """
    user.set_password(temporary_password)
    user.is_active = False
    user.onboarding_password_expires_at = (now or timezone.now()) + TEMPORARY_PASSWORD_TTL
    return user


def rotate_onboarding(user: User, temporary_password: str, *, now: Any | None = None) -> User:
    """Reissue: replace the stored hash and reset the expiry.

    Replacing the hash invalidates every previous temporary credential.
    """
    return start_onboarding(user, temporary_password, now=now)


def complete_onboarding(user: User) -> User:
    """Clear the temporary state after the forced change.

    The account becomes active again; the caller has already set the new
    normal-validator password and refreshed the current session hash.
    """
    user.is_active = True
    user.onboarding_password_expires_at = None
    return user


def is_onboarding_allowed_path(path: str) -> bool:
    """The only surfaces an in-onboarding session may reach."""
    if path in _ONBOARDING_EXACT_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in _ONBOARDING_STATIC_PREFIXES)


# --- email delivery -----------------------------------------------------------


def login_url_for_delivery() -> str:
    """Canonical configured HTTPS base URL + login path (never Host)."""
    base_url = settings.PUBLIC_BASE_URL
    if not base_url:
        msg = "Account email is enabled but the canonical base URL is unset."
        raise RuntimeError(msg)
    return f"{base_url}{LOGIN_PATH}"


def build_login_details_message(user: User, temporary_password: str) -> tuple[str, str]:
    """Plain-text subject/body containing only the three required parts."""
    login_url = login_url_for_delivery()
    subject = "Your SLAIF Asset Reservation login details"
    body = (
        f"A SLAIF Asset Reservation account has been created for "
        f"{user.email}.\n"
        f"Sign in here: {login_url}\n"
        f"Temporary password: {temporary_password}\n"
        f"This temporary password expires within 24 hours and you will "
        f"be asked to choose your own password after signing in. If you "
        f"did not expect this account, contact your administrator."
    )
    return subject, body


def send_login_details_email(user: User, temporary_password: str) -> int:
    """Send exactly one login-details email; return the accepted count."""
    subject, body = build_login_details_message(user, temporary_password)
    return mail.send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def _set_delivery_status(request: Any, user_pk: Any, status: str) -> None:
    """Persist the nonsecret outcome in the creating administrator's
    session, scoped to the specific account (``{str(pk): status}``).

    The single send runs after commit, so an explicit save keeps the
    status on the account page regardless of when the surrounding
    request's session would otherwise be written. The stored values are
    status words only — never a credential.
    """
    try:
        session = getattr(request, "session", None)
        if session is None:
            return
        statuses = session.get(DELIVERY_STATUS_SESSION_KEY)
        if not isinstance(statuses, dict):
            statuses = {}
        statuses[str(user_pk)] = status
        session[DELIVERY_STATUS_SESSION_KEY] = statuses
        session.save()
    except Exception:
        # Advisory UI state only; never fail the delivery path.
        pass


def delivery_status_for(request: Any, user_pk: Any) -> str | None:
    """The creating administrator's last recorded status for this account.

    The session value is the per-account mapping (``{str(pk): status}``).
    Anything else — in particular an account-unscoped single status
    string — is IGNORED, so one account's outcome can never be applied
    to (or displayed on) another account's page.
    """
    session = getattr(request, "session", None)
    if session is None:
        return None
    raw = session.get(DELIVERY_STATUS_SESSION_KEY)
    if isinstance(raw, dict):
        value = raw.get(str(user_pk))
        return value if isinstance(value, str) else None
    return None


def deliver_onboarding_email(
    user_pk: Any,
    temporary_password: str,
    request: Any,
    *,
    sent_hash: str,
    sent_expires_at: Any,
    reissue: bool = False,
) -> bool:
    """Exactly one post-commit send; exact-generation activation only.

    Registered with ``transaction.on_commit`` after the pending account
    (re)creation committed. ``sent_hash`` and ``sent_expires_at`` are the
    stored password hash and pending expiry of the EXACT credential
    generation being sent. The send is made only while the account still
    holds that generation: if a reissue (or any other change) superseded
    the credential before delivery ran, the scheduled credential is never
    emailed and the account state is left untouched. Activation is a
    conditional update matching the same generation, so even an accepted
    send whose generation moved in the meantime matches zero rows, never
    activates the newer pending credential and never claims delivery.

    SMTP acceptance is the backend returning exactly one accepted
    message; a raised error, zero or any other result leaves the account
    inactive. There is no automatic retry: the administrator uses the
    explicit reissue control instead. The admin status is nonsecret (the
    credential itself is never shown) and is scoped to this account.
    """
    status = "undelivered"
    superseded = False
    accepted = False
    try:
        user = User.objects.filter(pk=user_pk).first()
        if (
            user is None
            or user.is_active
            or not is_pending_onboarding(user)
            or user.password != sent_hash
            or user.onboarding_password_expires_at != sent_expires_at
        ):
            # The account vanished, was activated by another path or its
            # credential was reissued before this delivery ran: the
            # scheduled credential is superseded. Do not email it and do
            # not touch the current state.
            superseded = True
        else:
            accepted = send_login_details_email(user, temporary_password) == 1
    except Exception:
        accepted = False
    if accepted:
        updated = User.objects.filter(
            pk=user_pk,
            is_active=False,
            password=sent_hash,
            onboarding_password_expires_at=sent_expires_at,
        ).update(is_active=True)
        if updated:
            status = "delivered"
            if reissue:
                messages.success(
                    request,
                    "The new onboarding login details were accepted by the "
                    "email relay. The previous temporary password no longer "
                    "works.",
                )
            else:
                messages.success(
                    request,
                    "The account was created and its login details were "
                    "accepted by the email relay.",
                )
        else:
            # The send was accepted, but the account's credential changed
            # in the meantime: the scheduled credential does not work and
            # the newer pending credential has NOT been delivered.
            superseded = True
            status = "superseded"
            messages.warning(
                request,
                "The login-details email for the scheduled onboarding "
                "credential was accepted by the relay, but the account's "
                "credential changed before it was applied (for example "
                "through a reissue), so nothing was activated. The "
                "scheduled credential does not work; check the "
                "account's current onboarding state or reissue.",
            )
    elif not superseded:
        status = "undelivered"
        if reissue:
            messages.warning(
                request,
                "A new temporary password was set, but its email could "
                "not be confirmed as delivered. The account stays "
                "inactive; you can reissue again. Email delivery can be "
                "ambiguous, so do not assume the recipient has the new "
                "password.",
            )
        else:
            messages.warning(
                request,
                "The account was created but its login-details email "
                "could not be confirmed as delivered. The account stays "
                "inactive and cannot sign in yet; open it and use the "
                "onboarding reissue action to send the details again.",
            )
    else:
        status = "superseded"
        messages.warning(
            request,
            "The scheduled onboarding delivery was not made: the "
            "account's credential or state changed after it was "
            "scheduled (for example a reissue). The scheduled "
            "credential does not work; check the account's current "
            "onboarding state or reissue.",
        )
    _set_delivery_status(request, user_pk, status)
    return status == "delivered"
