"""Authentication backend with the onboarding expiry gate (SAR-055/056).

Subclasses Django's model backend so every existing permission semantic
is retained. The onboarding rules are deliberately narrow:

* an account whose temporary credential has NOT yet been delivered (or
  whose delivery is uncertain, for example while a reissue send is
  pending) is INACTIVE and is refused exactly like any other inactive
  account — a temporary credential may establish a session only after
  the accepted post-commit send has activated the account;
* an account activated from a delivered credential but still pending its
  first forced change is ACTIVE; it may authenticate with its temporary
  credential only while that credential is inside its 24-hour window
  (the session gate then allows only the password-change page);
* once the temporary credential has expired, no new member or
  Administration session can be established with it, and the base model
  backend's get_user (retained unchanged) drops any session of an
  inactive account — including one made inactive by a reissue.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth.backends import ModelBackend
from django.http import HttpRequest

from slaif_reservation.accounts import onboarding


class SlaifOnboardingAuthenticationBackend(ModelBackend):
    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> Any:
        user = super().authenticate(request, username=username, password=password, **kwargs)
        if user is None:
            # Inactive accounts — including pending onboarding accounts
            # whose delivery failed, is pending or was superseded by a
            # reissue — are refused here with the model backend's usual
            # (timing-equalized) failure.
            return None
        if onboarding.is_pending_onboarding(user) and onboarding.temporary_credential_expired(user):
            # Expired temporary credential: refuse to establish a new
            # session (member or Administration) with it.
            return None
        return user
