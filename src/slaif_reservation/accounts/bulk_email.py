"""Administration selected-user plain-text email (SAR-058).

A bounded, administrator-initiated message to the users checked on the
Administration user list. It reuses the existing operator-enabled
account-email transport (``settings.ACCOUNT_EMAIL_ENABLED`` plus the
Django email backend resolved by ``config/email.py``) and adds no
parallel transport, queue, template engine, HTML, attachments or
address export.

Boundaries:

* one plain-text message per selected recipient — no CC/BCC, no visible
  recipient list, no HTML, attachments or template execution;
* one request is bounded to at most ``MAX_BULK_RECIPIENTS`` recipients;
  an empty, stale, forged or oversized selection fails with a useful
  message and sends nothing;
* the final POST revalidates the exact selected accounts, the editor's
  ``accounts.change_user`` model permission, the enabled transport and
  the bounded plain-text form before any send;
* while the account-email transport is disabled the compose surface
  offers no send and the POST refuses before any send — the dummy
  backend is never reported as delivery;
* the first explicit rejection or exception stops the batch without
  automatic retry; the result reports nonsecret
  accepted/uncertain/not-attempted counts only (never the subject,
  body or any address);
* the subject, body and recipient addresses never enter URLs, session
  state, application logs, exception screens or the Admin action log.

The onboarding send/activation path (SAR-055) and every account,
reservation, authorization and transport setting are unchanged.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from django import forms
from django.conf import settings
from django.core import mail
from django.utils.translation import gettext_lazy as _

from slaif_reservation.accounts.models import User

#: One request may email at most this many selected users.
MAX_BULK_RECIPIENTS = 200

SUBJECT_MAX_LENGTH = 200
BODY_MAX_LENGTH = 10_000


def selected_pks(raw: str | None) -> list[str]:
    """Split the raw comma-separated selection into tokens (no trimming).

    Empty tokens (including a bare separator) are kept so the resolver
    can refuse a malformed selection instead of silently dropping it.
    """
    if not raw:
        return []
    return raw.split(",")


def resolve_selected_users(tokens: Sequence[str]) -> list[User] | None:
    """Resolve the exact selected primary keys to existing accounts.

    Returns ``None`` when the selection is empty, when any token is not
    a stored account UUID, or when any UUID no longer matches a stored
    account (a stale or forged selection) — the caller must then refuse
    the whole operation and send nothing. Duplicate pks are collapsed
    (one message per account) while the selection order is preserved.
    """
    ordered: dict[uuid.UUID, uuid.UUID] = {}
    for token in tokens:
        try:
            pk = uuid.UUID(token)
        except (ValueError, AttributeError, TypeError):
            return None
        ordered.setdefault(pk, pk)
    if not ordered:
        return None
    found = User.objects.filter(pk__in=list(ordered)).in_bulk()
    if len(found) != len(ordered):
        return None
    return [found[pk] for pk in ordered]


class BulkEmailForm(forms.Form):
    """The compose form: bounded plain-text subject and body only."""

    subject = forms.CharField(
        label=_("Subject"),
        max_length=SUBJECT_MAX_LENGTH,
        widget=forms.TextInput(attrs={"maxlength": SUBJECT_MAX_LENGTH}),
    )
    body = forms.CharField(
        label=_("Message"),
        max_length=BODY_MAX_LENGTH,
        # A modest initial height keeps the single Send action inside the
        # first desktop viewport; the textarea stays user-resizable.
        widget=forms.Textarea(attrs={"rows": 4, "maxlength": BODY_MAX_LENGTH}),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["subject"].help_text = _(
            "Plain text, one line, at most 200 characters. Line breaks are "
            "not allowed because the subject travels as a mail header."
        )
        self.fields["body"].help_text = _(
            "Plain text, at most 10,000 characters. Each selected recipient "
            "receives this same message separately, with no CC/BCC and no "
            "visible recipient list. No HTML, attachments or formatting."
        )
        self.fields["subject"].widget.attrs["aria-describedby"] = "id_subject_helptext"
        self.fields["body"].widget.attrs["aria-describedby"] = "id_body_helptext"

    def clean_subject(self) -> str:
        # The field is required and stripped by the framework; the extra
        # guard is the header-injection boundary: the subject travels as a
        # mail header, so it must stay on one line.
        subject = str(self.cleaned_data.get("subject") or "")
        if "\r" in subject or "\n" in subject:
            raise forms.ValidationError(_("The subject must be a single line without line breaks."))
        return subject

    def clean_body(self) -> str:
        # Required and stripped by the framework; the body may span lines.
        return str(self.cleaned_data.get("body") or "")


@dataclass(frozen=True)
class BulkSendCounts:
    """Nonsecret outcome of one bounded send batch (counts only)."""

    accepted: int
    uncertain: int
    not_attempted: int


def send_selected_user_emails(users: Sequence[User], subject: str, body: str) -> BulkSendCounts:
    """Send one plain-text message per recipient through the existing
    configured Django email backend.

    Relay acceptance (the backend reporting exactly one accepted
    message) is counted as accepted; it is NOT proof of inbox delivery.
    The first explicit rejection (the backend reports no accepted
    message) or the first exception stops the batch: that message is
    counted as uncertain (an exception may follow an already-accepted
    relay transaction) and no remaining recipient is attempted. There
    is no automatic retry. Only nonsecret counts are returned.
    """
    accepted = 0
    uncertain = 0
    for user in users:
        try:
            sent = mail.send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception:
            uncertain += 1
            break
        if sent != 1:
            uncertain += 1
            break
        accepted += 1
    total = len(users)
    return BulkSendCounts(
        accepted=accepted,
        uncertain=uncertain,
        not_attempted=total - accepted - uncertain,
    )
