from __future__ import annotations

from datetime import datetime
from typing import Any

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _

from slaif_reservation.accounts.models import User
from slaif_reservation.accounts.validators import validate_timezone_name
from slaif_reservation.reservations.time_utils import LocalTimeError, interpret_local_wall_time


class HumanAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": _("Enter a valid email address and password."),
        "inactive": _("Enter a valid email address and password."),
    }

    def confirm_login_allowed(self, user: User) -> None:
        if not user.is_active or user.is_service_account:
            raise forms.ValidationError(
                self.error_messages["invalid_login"],
                code="invalid_login",
                params={"username": self.username_field.verbose_name},
            )


class ProfileForm(forms.ModelForm):  # type: ignore[type-arg]
    timezone = forms.CharField(
        label=_("Timezone"),
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )

    class Meta:
        model = User
        fields = ["display_name", "timezone"]
        widgets = {
            "display_name": forms.TextInput(attrs={"autocomplete": "name"}),
        }

    def clean_timezone(self) -> str:
        value = str(self.cleaned_data["timezone"]).strip()
        validate_timezone_name(value)
        return value


class ReservationForm(forms.Form):
    start = forms.CharField(
        label=_("Start"),
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "step": "60"}),
    )
    start_fold = forms.ChoiceField(
        label=_("Start occurrence"),
        required=False,
        choices=[("", _("Automatic")), ("0", _("First occurrence")), ("1", _("Second occurrence"))],
    )
    end = forms.CharField(
        label=_("End"),
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "step": "60"}),
    )
    end_fold = forms.ChoiceField(
        label=_("End occurrence"),
        required=False,
        choices=[("", _("Automatic")), ("0", _("First occurrence")), ("1", _("Second occurrence"))],
    )
    purpose = forms.CharField(
        label=_("Purpose"),
        required=False,
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, *args: Any, timezone_name: str, **kwargs: Any) -> None:
        self.timezone_name = timezone_name
        super().__init__(*args, **kwargs)

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        start_text = cleaned.get("start")
        end_text = cleaned.get("end")
        if not start_text or not end_text:
            return cleaned

        try:
            start_local = _parse_datetime_local(start_text)
        except ValueError:
            self.add_error("start", _("Enter a valid local start date and time."))
            return cleaned

        try:
            end_local = _parse_datetime_local(end_text)
        except ValueError:
            self.add_error("end", _("Enter a valid local end date and time."))
            return cleaned

        try:
            start = interpret_local_wall_time(
                start_local,
                timezone_name=self.timezone_name,
                fold=_parse_fold(cleaned.get("start_fold")),
            )
        except LocalTimeError as exc:
            self.add_error("start", str(exc))
            return cleaned

        try:
            end = interpret_local_wall_time(
                end_local,
                timezone_name=self.timezone_name,
                fold=_parse_fold(cleaned.get("end_fold")),
            )
        except LocalTimeError as exc:
            self.add_error("end", str(exc))
            return cleaned

        if end.instant <= start.instant:
            self.add_error("end", _("End must be after start."))
            return cleaned

        cleaned["start_instant"] = start.instant
        cleaned["end_instant"] = end.instant
        cleaned["start_local"] = start.local
        cleaned["end_local"] = end.local
        return cleaned


class CancellationForm(forms.Form):
    reason = forms.CharField(
        label=_("Reason"),
        required=False,
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


def _parse_datetime_local(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is not None:
        raise ValueError("Expected naive datetime-local value.")
    return parsed


def _parse_fold(value: Any) -> int | None:
    if value in ("", None):
        return None
    return int(value)
