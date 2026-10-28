from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast
from zoneinfo import ZoneInfo

from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.core.validators import MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from slaif_reservation.accounts.authorization import (
    SCOPE_ISSUANCE_CAPABILITIES,
    issuable_token_scopes,
)
from slaif_reservation.accounts.models import User
from slaif_reservation.accounts.tokens import ALLOWED_API_TOKEN_SCOPES
from slaif_reservation.accounts.validators import TIMEZONE_NAME_MAX_LENGTH, validate_timezone_name
from slaif_reservation.reservations.models import ReservationPolicy
from slaif_reservation.reservations.services import earliest_reservation_start
from slaif_reservation.reservations.time_utils import LocalTimeError, interpret_local_wall_time


class HumanAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
        help_text=_(
            "The email address of your account. Accounts are created by an "
            "administrator; self-registration is not available."
        ),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        _wire_field_help(self, ("username",))

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
    display_name = forms.CharField(
        label=_("Display name"),
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={"autocomplete": "name"}),
        help_text=_(
            "Shown to staff in management views and on reservation records. "
            "Leave blank to show only your email."
        ),
    )
    timezone = forms.CharField(
        label=_("Timezone"),
        required=False,
        max_length=TIMEZONE_NAME_MAX_LENGTH,
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
        help_text=_(
            "Required. IANA time zone name (for example Europe/Ljubljana) used "
            "for every time you enter and see. Blank or unknown names are rejected."
        ),
    )

    class Meta:
        model = User
        fields = ["display_name", "timezone"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        _wire_field_help(self, ("display_name", "timezone"))

    def clean_timezone(self) -> str:
        value = str(self.cleaned_data["timezone"]).strip()
        validate_timezone_name(value)
        return value


_FOLD_CHOICES = [
    ("", _("Automatic")),
    ("0", _("First occurrence")),
    ("1", _("Second occurrence")),
]


class ReservationForm(forms.Form):
    start = forms.CharField(
        label=_("Start"),
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "step": "60"}),
        help_text=_(
            "Local date and time the asset is needed, within the booking horizon. "
            "Without a required lead time, starts up to 10 minutes ago are allowed."
        ),
    )
    start_fold = forms.ChoiceField(
        label=_("Start occurrence"),
        required=False,
        choices=_FOLD_CHOICES,
        help_text=_(
            "Only relevant on a daylight-saving transition day in your "
            "timezone. On fall-back the clock time repeats and Automatic is "
            "then rejected: choose First occurrence (the earlier one) or "
            "Second occurrence (the later one). A time inside the "
            "spring-forward gap does not exist and is always rejected, "
            "whatever you choose."
        ),
    )
    duration = forms.ChoiceField(
        label=_("Duration"),
        required=False,
        initial="custom",
        choices=[
            ("60", _("1 hour")),
            ("120", _("2 hours")),
            ("240", _("4 hours")),
            ("custom", _("Custom end time")),
        ],
        widget=forms.RadioSelect,
        help_text=_(
            "Choose elapsed reservation time, or enter a custom end below. "
            "Quick durations are calculated from your start instant, "
            "including daylight-saving changes."
        ),
    )
    end = forms.CharField(
        label=_("End"),
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "step": "60"}),
        help_text=_(
            "Local end date and time, in the future. The asset is held from the "
            "start until the end; the end instant itself is free again."
        ),
    )
    end_fold = forms.ChoiceField(
        label=_("End occurrence"),
        required=False,
        choices=_FOLD_CHOICES,
        help_text=_(
            "Only relevant on a daylight-saving transition day in your "
            "timezone. On fall-back the clock time repeats and Automatic is "
            "then rejected: choose First occurrence (the earlier one) or "
            "Second occurrence (the later one). A time inside the "
            "spring-forward gap does not exist and is always rejected, "
            "whatever you choose."
        ),
    )
    purpose = forms.CharField(
        label=_("Purpose"),
        required=False,
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text=_(
            "Optional unless the policy for this asset requires it. Staff can "
            "read it on the reservation."
        ),
    )

    def __init__(
        self,
        *args: Any,
        timezone_name: str,
        policy: ReservationPolicy | None = None,
        now: datetime | None = None,
        **kwargs: Any,
    ) -> None:
        self.timezone_name = timezone_name
        super().__init__(*args, **kwargs)
        self.order_fields(["start", "duration", "start_fold", "end", "end_fold", "purpose"])
        self.fields["start"].help_text = _(
            "Local date and time the asset is needed, in %(timezone)s (your profile timezone). "
            "Without a required lead time, starts up to 10 minutes ago are allowed."
        ) % {"timezone": timezone_name}
        self.fields["end"].help_text = _(
            "Local end date and time, in %(timezone)s, after the start and in the future. The "
            "asset is held from the start until the end; the end instant itself "
            "is free again."
        ) % {"timezone": timezone_name}
        # Only rendering uses the policy snapshot. POST choices stay the fixed
        # 1/2/4-hour vocabulary; create_reservation rechecks the current policy.
        choices = [
            (str(minutes), label)
            for minutes, label in ((60, _("1 hour")), (120, _("2 hours")), (240, _("4 hours")))
            if policy is not None
            and policy.min_duration_minutes <= minutes <= policy.max_duration_minutes
        ]
        cast(forms.RadioSelect, self.fields["duration"].widget).choices = [
            *choices,
            ("custom", _("Custom end time")),
        ]
        if policy is not None:
            current = (timezone.now() if now is None else now).astimezone(UTC)
            earliest = earliest_reservation_start(policy, now=current)
            latest = current + timedelta(days=policy.booking_horizon_days)
            # The picker uses whole minutes. Round inward so it never suggests
            # a start outside the current instant-based domain bounds.
            first_minute = earliest.replace(second=0, microsecond=0)
            if first_minute < earliest:
                first_minute += timedelta(minutes=1)
            last_minute = latest.replace(second=0, microsecond=0)
            zone = ZoneInfo(timezone_name)
            first_local, last_local = first_minute.astimezone(zone), last_minute.astimezone(zone)
            self.fields["start"].widget.attrs.update(
                {
                    "min": first_local.strftime("%Y-%m-%dT%H:%M"),
                    "max": last_local.strftime("%Y-%m-%dT%H:%M"),
                }
            )
            initial_start = max(first_minute, current.replace(second=0, microsecond=0))
            if not self.is_bound and "start" not in self.initial and initial_start <= last_minute:
                # Defaults come from real instants, in the member's timezone.
                # Never replace submitted values, even after validation errors.
                minutes = max(policy.min_duration_minutes, min(60, policy.max_duration_minutes))
                end_local = (initial_start + timedelta(minutes=minutes)).astimezone(zone)
                for name, value in (("start", initial_start.astimezone(zone)), ("end", end_local)):
                    if name not in self.initial:
                        self.initial[name] = value.strftime("%Y-%m-%dT%H:%M")
                        # At fall-back this exact instant already determines
                        # which occurrence to use; ordinary times stay Automatic.
                        ambiguous = (
                            value.utcoffset() != value.replace(fold=1 - value.fold).utcoffset()
                        )
                        self.initial.setdefault(
                            f"{name}_fold", str(value.fold) if ambiguous else ""
                        )
            self.fields["start"].help_text += " " + _(
                "Reservations may start between %(earliest)s and %(latest)s. "
                "This picker range is guidance; checked again on submission."
            ) % {
                "earliest": first_local.strftime("%Y-%m-%d %H:%M"),
                "latest": last_local.strftime("%Y-%m-%d %H:%M"),
                "timezone": timezone_name,
            }
        _wire_field_help(self, ("start", "start_fold", "duration", "end", "end_fold", "purpose"))

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        start_text = cleaned.get("start")
        end_text = cleaned.get("end")
        if not start_text:
            return cleaned

        try:
            start_local = _parse_datetime_local(start_text)
        except ValueError:
            self.add_error("start", _("Enter a valid local start date and time."))
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

        duration = cleaned.get("duration") or "custom"
        if "duration" in self.errors:
            return cleaned
        if duration != "custom":
            # start.instant is UTC: elapsed time, not local wall-clock arithmetic.
            try:
                end_instant = start.instant + timedelta(minutes=int(duration))
                end_local = end_instant.astimezone(ZoneInfo(self.timezone_name)).replace(
                    tzinfo=None
                )
            except OverflowError:
                self.add_error(
                    "start", _("The selected duration is outside the supported date range.")
                )
                return cleaned
        else:
            if not end_text:
                self.add_error("end", _("Enter a custom end date and time."))
                return cleaned
            try:
                end_local = _parse_datetime_local(end_text)
            except ValueError:
                self.add_error("end", _("Enter a valid local end date and time."))
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
            end_instant = end.instant

        if end_instant <= start.instant:
            self.add_error("end", _("End must be after start."))
            return cleaned

        cleaned["start_instant"] = start.instant
        cleaned["end_instant"] = end_instant
        cleaned["start_local"] = start.local
        cleaned["end_local"] = end_local
        return cleaned


class CancellationForm(forms.Form):
    reason = forms.CharField(
        label=_("Reason"),
        required=False,
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_("Optional. Recorded with the cancellation and visible to staff."),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        _wire_field_help(self, ("reason",))


def _scope_label(scope: str) -> str:
    from slaif_reservation.web.templatetags.form_guidance import SCOPE_LABELS

    return str(SCOPE_LABELS.get(scope, scope))


class ApiTokenCreationForm(forms.Form):
    name = forms.CharField(
        label=_("Token name"),
        max_length=100,
        help_text=_("A label for your own records. It never changes what the token can do."),
    )
    scopes = forms.MultipleChoiceField(
        label=_("Scopes (what the token may do)"),
        choices=[(scope, _scope_label(scope)) for scope in ALLOWED_API_TOKEN_SCOPES],
        widget=forms.CheckboxSelectMultiple,
        help_text=_(
            "Choose the API operations this token may perform under /api/v1/. "
            "Every tick adds one permission; revoke the token at any time to "
            "remove all of them."
        ),
    )
    lifetime_days = forms.IntegerField(
        label=_("Lifetime in days"),
        min_value=1,
        help_text=_("Days until the token expires on its own."),
    )

    def __init__(self, *args: Any, owner: Any = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        maximum = int(settings.API_TOKEN_MAX_LIFETIME_DAYS)
        default_lifetime = min(30, maximum)
        lifetime_field = cast(forms.IntegerField, self.fields["lifetime_days"])
        lifetime_field.max_value = maximum
        lifetime_field.validators.append(MaxValueValidator(maximum))
        lifetime_field.initial = default_lifetime
        lifetime_field.widget.attrs["max"] = str(maximum)
        lifetime_field.help_text = _(
            "Days until the token expires on its own, between 1 and "
            "%(days)s. A shorter lifetime limits the damage if the token leaks."
        ) % {"days": maximum}
        _wire_field_help(self, ("name", "lifetime_days"))
        scopes_widget = cast(forms.CheckboxSelectMultiple, self.fields["scopes"].widget)
        scopes_widget.attrs["aria-describedby"] = "id_scopes-help"
        # Issuance ceilings (order 051-a): offer only the scopes the
        # SERVER-REQUEST owner can currently issue. Read-all requires the
        # current view_all_reservations capability; create requires the
        # current booking capability. A context without an owner is
        # conservative and never defaults to the privileged choices. The
        # service remains authoritative at issuance (fresh locked owner).
        if owner is not None:
            issuable = set(issuable_token_scopes(owner))
        else:
            issuable = {
                scope
                for scope in ALLOWED_API_TOKEN_SCOPES
                if scope not in SCOPE_ISSUANCE_CAPABILITIES
            }
        scopes_field = cast(forms.MultipleChoiceField, self.fields["scopes"])
        scopes_field.choices = [
            (scope, _scope_label(scope)) for scope in ALLOWED_API_TOKEN_SCOPES if scope in issuable
        ]

    def clean_name(self) -> str:
        value = str(self.cleaned_data["name"]).strip()
        if not value:
            raise forms.ValidationError(_("Token name is required."))
        return value

    def clean_lifetime_days(self) -> int:
        value = int(self.cleaned_data["lifetime_days"])
        maximum = int(settings.API_TOKEN_MAX_LIFETIME_DAYS)
        if value > maximum:
            raise forms.ValidationError(
                _("Ensure this value is less than or equal to %(limit_value)s."),
                params={"limit_value": maximum},
            )
        return value


def _wire_field_help(form: Any, names: tuple[str, ...]) -> None:
    for name in names:
        field = form.fields[name]
        if field.help_text:
            field.widget.attrs["aria-describedby"] = f"id_{name}-help"


def _parse_datetime_local(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is not None:
        raise ValueError("Expected naive datetime-local value.")
    return parsed


def _parse_fold(value: Any) -> int | None:
    if value in ("", None):
        return None
    return int(value)
