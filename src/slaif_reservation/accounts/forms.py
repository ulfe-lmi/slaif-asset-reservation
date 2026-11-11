"""Administration account-creation form (SAR-055/SAR-056).

``SlaifUserCreationForm`` is the Administration add-user form. It keeps
the standard Django user-creation contract (email plus confirmed
password, full normal validator set) and adds one narrow, signed
exception: the fresh six-character temporary credential prefilled by
the add form may be submitted as-is, proved by a short-lived signed
digest bound to the creating administrator's session. An edited,
tampered, expired or unbound six-character value is rejected, and every
manually entered password (normal length or more) is validated exactly
as before. The form never lowers the global minimum, never stores the
credential in a server session or database plaintext, and never echoes
it into errors.
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
        # The generated temporary credential (when account email is
        # enabled) is prefilled in BOTH controls: render the value and
        # explain the narrow generated-only path. Without account email
        # the form behaves exactly like the regular add form.
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
                        "Keep it as-is to create the account and email "
                        "these login details; the member must then choose "
                        "their own password within 24 hours after signing "
                        "in. Or clear the fields and enter a regular "
                        "password that satisfies the site rules:"
                    )
                    + " "
                    + password_validators_help_text_html()
                )
            else:
                password1.help_text = (
                    _(
                        "Choose the initial password for this account. The "
                        "member can later change their own password from "
                        "the profile page; an administrator can also set or "
                        "change it from this user page. It must satisfy the "
                        "site password rules:"
                    )
                    + " "
                    + password_validators_help_text_html()
                )

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
