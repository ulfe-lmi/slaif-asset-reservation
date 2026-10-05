"""Product identity and human-boundary admission for the SLAIF admin site.

Only the administrative identity and the login admission rule change here:
autodiscovered model registrations, permission checks and the protected
read-only mutation boundaries remain exactly as registered by each app.
"""

from __future__ import annotations

from typing import Any

from django import forms
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import SESSION_KEY
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _

from slaif_reservation.web.auth import is_active_human


class SlaifAdminAuthenticationForm(AuthenticationForm):
    """Administration sign-in with the product identifier and human boundary.

    The identifier is the account email address, and invalid, inactive or
    service-account identities are rejected with the same generic message
    as the member login.
    """

    username = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": _("Enter a valid email address and password."),
        "inactive": _("Enter a valid email address and password."),
    }

    def confirm_login_allowed(self, user: Any) -> None:
        if not user.is_active or user.is_service_account:
            raise forms.ValidationError(
                self.error_messages["invalid_login"],
                code="invalid_login",
                params={"username": self.username_field.verbose_name},
            )


class SlaifAdminSite(AdminSite):
    """The SLAIF Asset Reservation administration site.

    Identity-only customization: site title/header, index title, login form
    and templates. Registration, permission and protected-boundary behavior
    is inherited unchanged.
    """

    site_title = "SLAIF Asset Reservation administration"
    site_header = "SLAIF Asset Reservation administration"
    index_title = "SLAIF Asset Reservation site administration"
    login_form = SlaifAdminAuthenticationForm
    login_template = "admin/login.html"

    def login(self, request: HttpRequest, extra_context: Any = None) -> HttpResponse:
        # Same human boundary as the member login: a disallowed
        # authenticated session (inactive or service-account) is terminated
        # before the login page renders, so no redirect loop and no member
        # workflow remains reachable.
        if (
            request.user.is_authenticated or SESSION_KEY in request.session
        ) and not is_active_human(request.user):
            auth_logout(request)
        return super().login(request, extra_context=extra_context)
