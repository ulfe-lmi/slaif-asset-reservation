"""Authentication backend with the onboarding expiry gate (SAR-055/056).

Subclasses Django's model backend so every existing permission semantic
is retained. Two deliberate behaviors around the onboarding state:

* an account still pending its first forced change is INACTIVE on
  purpose, so the model backend's usual active check would reject it;
  such an account may authenticate with its temporary credential only
  while that credential is inside its 24-hour window (the session gate
  then allows only the password-change page);
* once the temporary credential has expired, no new member or
  Administration session can be established with it.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth.backends import ModelBackend
from django.http import HttpRequest

from slaif_reservation.accounts import onboarding
from slaif_reservation.accounts.models import User


class SlaifOnboardingAuthenticationBackend(ModelBackend):
    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> Any:
        user = super().authenticate(request, username=username, password=password, **kwargs)
        if user is not None:
            if onboarding.temporary_credential_expired(user):
                # Expired temporary credential: refuse to establish a new
                # session (member or Administration) with it.
                return None
            return user
        # The model backend's active check rejected the account. The one
        # narrow exception: an account pending its first forced change,
        # with an unexpired temporary credential and no service-account
        # flag, may authenticate here. Everything else fails exactly as
        # before (same not-found timing equalization as the base class).
        value = username if username is not None else kwargs.get(User.USERNAME_FIELD)
        if value is None or password is None:
            return None
        try:
            candidate = User._default_manager.get_by_natural_key(value)
        except User.DoesNotExist:
            User().set_password(password)
            return None
        if (
            candidate.is_service_account
            or not onboarding.is_pending_onboarding(candidate)
            or onboarding.temporary_credential_expired(candidate)
            or not candidate.check_password(password)
        ):
            return None
        return candidate

    def get_user(self, user_id: Any) -> Any:
        # The base model backend drops the session of every inactive user
        # on each request. One narrow exception (SAR-056): an account
        # pending its first forced change is inactive on purpose and must
        # keep its session so it can reach the password-change page while
        # its temporary credential is unexpired. Once the credential has
        # expired the session is dropped (flushed) exactly as for any
        # other inactive account.
        try:
            user = User._default_manager.get(pk=user_id)
        except User.DoesNotExist:
            return None
        if user.is_active:
            return user
        if (
            not user.is_service_account
            and onboarding.is_pending_onboarding(user)
            and not onboarding.temporary_credential_expired(user)
        ):
            return user
        return None
