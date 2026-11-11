"""Forced first password-change gate for onboarding accounts (SAR-056).

While an account is pending its first forced change (temporary
credential still inside its 24-hour window) its session may reach only
the member password-change page, logout, the login page, the health
surfaces and static/branding assets. Every other path is redirected to
the password-change page (never a loop: that path is always allowed).
Once the temporary credential has expired, the session is terminated and
the user is sent to the login page; the authentication backend
separately refuses any new session with the expired credential.
"""

from __future__ import annotations

from collections.abc import Callable

from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils import timezone

from slaif_reservation.accounts import onboarding


class OnboardingForcedChangeMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        user = request.user
        if user.is_authenticated and onboarding.is_pending_onboarding(user):
            if onboarding.temporary_credential_expired(user, now=timezone.now()):
                # An existing session outlived the temporary credential:
                # terminate it safely instead of allowing any work.
                logout(request)
                return redirect(settings.LOGIN_URL)
            if not onboarding.is_onboarding_allowed_path(request.path):
                return redirect("web:password-change")
        return self.get_response(request)
