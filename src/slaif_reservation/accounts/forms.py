"""Administration account-creation form (SAR-055/SAR-056).

``SlaifUserCreationForm`` is the Administration add-user form. It keeps
the standard Django user-creation contract (email plus confirmed
password, full normal validator set) and adds one narrow, signed
exception: the fresh six-character temporary credential prefilled by
the add form may be submitted as-is, proved by a short-lived signed
digest bound to the creating administrator's session. An edited,
tampered, expired or unbound six-character value is rejected, and every
manually entered password (normal length or more) is validated exactly
as before.

While account email is enabled, EVERY valid submission — the generated
prefill or a manually entered normal-validator password — is an
onboarding credential: the account commits inactive/pending and is
activated only by the accepted post-commit send. While account email is
disabled, every submission is refused with clear setup guidance before
any account is written. The form never lowers the global minimum, never
stores the credential in a server session or database plaintext, and
never echoes it into errors.
"""

from __future__ import annotations

from typing import Any

from django import forms
from django.conf import settings
from django.contrib.auth.forms import BaseUserCreationForm, UserCreationForm
from django.contrib.auth.password_validation import (
    password_validators_help_text_html,
)
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from slaif_reservation.accounts import onboarding
from slaif_reservation.accounts.models import User

PREFILL_MISMATCH_MESSAGE = (
    "The temporary password no longer matches the generated value. It may "
    "have been edited, expired or copied from another session. Reload the "
    "add-user form to get a fresh temporary password, or enter your own "
    "password that satisfies the site rules."
)


class SlaifUserCreationForm(UserCreationForm):  # type: ignore[type-arg]
    """Add-user form with the narrow generated-only length exception."""

    class Meta:
        model = User
        fields = ("email",)

    def __init__(
        self,
        *args: Any,
        onboarding_nonce: str | None = None,
        onboarding_prefill_proof: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._onboarding_nonce = onboarding_nonce
        self._onboarding_prefill_proof = onboarding_prefill_proof
        self.onboarding_generated = False
        # The generated temporary credential is prefilled in BOTH
        # controls on every add GET (account email enabled or not):
        # render the value and explain the narrow generated-only path /
        # the disabled-state refusal below.
        for name in ("password1", "password2"):
            field = self.fields.get(name)
            if field is None:
                continue
            widget = field.widget
            if isinstance(widget, forms.PasswordInput) and not widget.render_value:
                field.widget = forms.PasswordInput(
                    attrs=dict(getattr(widget, "attrs", {}) or {}),
                    render_value=True,
                )
        password1 = self.fields.get("password1")
        if password1 is not None:
            if settings.ACCOUNT_EMAIL_ENABLED:
                password1.help_text = (
                    _(
                        "A temporary six-character password has been "
                        "generated for you and prefilled in both fields. "
                        "Keep it as-is, or clear the fields and enter a "
                        "regular password that satisfies the site rules: "
                        "either way the account is created inactive "
                        "pending onboarding, its login details are "
                        "emailed only after the account is saved, the "
                        "account is activated only once delivery is "
                        "confirmed, and the member must choose their own "
                        "password within 24 hours after signing in."
                    )
                    + " "
                    + password_validators_help_text_html()
                )
            else:
                password1.help_text = _(
                    "Creating accounts from this form requires the "
                    "account email (SMTP) transport to be configured "
                    "and enabled. Both fields are prefilled with a "
                    "generated six-character temporary password, but "
                    "while account email is disabled every submission "
                    "here is refused and NO account is created. "
                    "Configure the account email transport, reload "
                    "this form, and create the account then."
                )

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        if not settings.ACCOUNT_EMAIL_ENABLED:
            # Without the account-email transport, Administration-created
            # accounts could not be delivered and could not be onboarded:
            # refuse EVERY add submission (generated or manually entered)
            # before any account is written. CLI createsuperuser and
            # existing accounts are unaffected.
            self.add_error(
                None,
                _(
                    "Creating accounts from this form requires the "
                    "account email (SMTP) transport to be enabled and "
                    "configured. Configure it, reload this form and try "
                    "again; no account has been created."
                ),
            )
        return cleaned

    def _verify_generated(self, password: str) -> bool:
        return onboarding.verify_prefill_proof(
            self._onboarding_prefill_proof,
            self._onboarding_nonce,
            password,
        )

    def clean_password1(self) -> str | None:
        password1 = self.cleaned_data.get("password1")
        if password1 is None:
            return None
        password1 = str(password1)
        if len(password1) == onboarding.TEMPORARY_PASSWORD_LENGTH:
            # Six characters are accepted ONLY as the generated, signed
            # prefill. Any other six-character value (edited, tampered,
            # expired or unbound) is rejected; the normal validators
            # never apply to a six-character value.
            if self._verify_generated(password1):
                self.onboarding_generated = True
                return password1
            raise ValidationError(PREFILL_MISMATCH_MESSAGE)
        return password1

    def _post_clean(self) -> None:
        # The generated-only exception: the six-character credential is an
        # enrollment value, so the normal password validator set applies
        # only to manually entered passwords. The model's own validation
        # (instance full_clean and uniqueness) still runs in both cases;
        # the global minimum and every other validator are unchanged for
        # all other paths (member forced change, admin password set).
        if self.onboarding_generated:
            super(BaseUserCreationForm, self)._post_clean()  # type: ignore[misc]
            return
        super()._post_clean()  # type: ignore[misc]
