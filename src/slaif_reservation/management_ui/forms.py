from __future__ import annotations

from datetime import datetime
from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from slaif_reservation.accounts.validators import TIMEZONE_NAME_MAX_LENGTH, validate_timezone_name
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.reservations.models import (
    Reservation,
    ReservationLifecycle,
    ReservationPolicy,
)
from slaif_reservation.reservations.time_utils import (
    LocalTimeError,
    interpret_local_wall_time,
    require_aware_utc,
)


class AwareDateTimeFilterField(forms.CharField):
    def clean(self, value: Any) -> datetime | None:
        cleaned = super().clean(value)
        if cleaned in self.empty_values:
            return None
        try:
            parsed = datetime.fromisoformat(str(cleaned).replace("Z", "+00:00"))
        except ValueError as exc:
            raise forms.ValidationError(_("Enter an aware ISO-8601 timestamp.")) from exc
        if not timezone.is_aware(parsed):
            raise forms.ValidationError(_("Enter an aware ISO-8601 timestamp."))
        try:
            return require_aware_utc(parsed, field_name=str(self.label or "timestamp"))
        except ValidationError as exc:
            raise forms.ValidationError(_("Enter an aware ISO-8601 timestamp.")) from exc


class FilterFormMixin:
    navigation_fields = {"page"}

    def has_real_filters(self) -> bool:
        data = getattr(self, "data", {})
        return any(
            key not in self.navigation_fields and str(value).strip() for key, value in data.items()
        )


class ReservationPolicyForm(forms.Form):
    name = forms.CharField(
        label=_("Name"),
        max_length=180,
        help_text=_("Short unique name for this policy, for example 'GPU A' or 'default'."),
    )
    asset = forms.ModelChoiceField(
        label=_("Asset target"),
        queryset=Asset.objects.select_related("parent").order_by("slug"),
        required=False,
        help_text=_(
            "Which asset these rules apply to; leave empty for the global "
            "policy. Bookings check the exact asset first, then its parent "
            "machine, then the global policy. If two active policies match at "
            "the same level, booking fails closed."
        ),
    )
    min_duration_minutes = forms.IntegerField(
        label=_("Minimum duration (minutes)"),
        min_value=1,
        help_text=_("Shortest allowed booking, in minutes. 1440 minutes = 24 hours = 1 day."),
    )
    max_duration_minutes = forms.IntegerField(
        label=_("Maximum duration (minutes)"),
        min_value=1,
        help_text=_(
            "Longest allowed single booking, in minutes. 2880 minutes = 48 "
            "hours = 2 days. New bookings longer than this are rejected."
        ),
    )
    booking_horizon_days = forms.IntegerField(
        label=_("Booking horizon (days)"),
        min_value=0,
        help_text=_(
            "How far into the future a booking may START. 7 means the start "
            "must be within the next 7 days from now. It limits the start "
            "time, not the end time."
        ),
    )
    min_lead_minutes = forms.IntegerField(
        label=_("Minimum lead time (minutes)"),
        min_value=0,
        help_text=_(
            "Minimum gap between booking and start. 0 allows bookings that "
            "start right now; 120 requires at least 2 hours of notice."
        ),
    )
    cancellation_cutoff_minutes = forms.IntegerField(
        label=_("Cancellation cutoff (minutes)"),
        min_value=0,
        help_text=_(
            "How many minutes before the start members stop being able to "
            "cancel. 0 means cancellation stays possible up to the start time."
        ),
    )
    max_upcoming_per_principal = forms.IntegerField(
        label=_("Maximum upcoming per principal"),
        min_value=1,
        help_text=_(
            "How many not-yet-started reservations one principal (a person and "
            "their API tokens) may hold across all assets. A new booking is "
            "rejected once the count reaches this number."
        ),
    )
    max_concurrent_per_principal = forms.IntegerField(
        label=_("Maximum overlapping records per principal"),
        min_value=1,
        help_text=_(
            "How many of a principal's existing records (confirmed or "
            "released) may intersect the proposed interval. 8 rejects a new "
            "booking when 8 or more existing records already intersect it. "
            "This counts records; it is not a simultaneous-occupancy sweep."
        ),
    )
    purpose_required = forms.BooleanField(
        label=_("Purpose required"),
        required=False,
        help_text=_("Require members to enter a purpose for new bookings under this policy."),
    )

    def __init__(
        self,
        *args: Any,
        instance: ReservationPolicy | None = None,
        **kwargs: Any,
    ) -> None:
        self.instance = instance
        if instance is not None and "initial" not in kwargs:
            kwargs["initial"] = {
                "name": instance.name,
                "asset": instance.asset_id,
                "min_duration_minutes": instance.min_duration_minutes,
                "max_duration_minutes": instance.max_duration_minutes,
                "booking_horizon_days": instance.booking_horizon_days,
                "min_lead_minutes": instance.min_lead_minutes,
                "cancellation_cutoff_minutes": instance.cancellation_cutoff_minutes,
                "max_upcoming_per_principal": instance.max_upcoming_per_principal,
                "max_concurrent_per_principal": instance.max_concurrent_per_principal,
                "purpose_required": instance.purpose_required,
            }
        super().__init__(*args, **kwargs)
        _wire_field_help(
            self,
            (
                "name",
                "asset",
                "min_duration_minutes",
                "max_duration_minutes",
                "booking_horizon_days",
                "min_lead_minutes",
                "cancellation_cutoff_minutes",
                "max_upcoming_per_principal",
                "max_concurrent_per_principal",
                "purpose_required",
            ),
        )

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        minimum = cleaned.get("min_duration_minutes")
        maximum = cleaned.get("max_duration_minutes")
        if minimum is not None and maximum is not None and maximum < minimum:
            self.add_error("max_duration_minutes", _("Maximum duration must be at least minimum."))
        asset = cleaned.get("asset")
        if asset is not None and not (asset.kind == Asset.KIND_MACHINE or asset.parent_id):
            self.add_error("asset", _("Policy target must be a machine or child asset."))
        return cleaned

    def service_values(self) -> dict[str, Any]:
        return {
            "name": self.cleaned_data["name"],
            "asset": self.cleaned_data.get("asset"),
            "min_duration_minutes": self.cleaned_data["min_duration_minutes"],
            "max_duration_minutes": self.cleaned_data["max_duration_minutes"],
            "booking_horizon_days": self.cleaned_data["booking_horizon_days"],
            "min_lead_minutes": self.cleaned_data["min_lead_minutes"],
            "cancellation_cutoff_minutes": self.cleaned_data["cancellation_cutoff_minutes"],
            "max_upcoming_per_principal": self.cleaned_data["max_upcoming_per_principal"],
            "max_concurrent_per_principal": self.cleaned_data["max_concurrent_per_principal"],
            "purpose_required": self.cleaned_data["purpose_required"],
        }


_FOLD_CHOICES = [
    ("", _("Automatic")),
    ("0", _("First occurrence")),
    ("1", _("Second occurrence")),
]


class MaintenanceBlackoutForm(forms.Form):
    asset = forms.ModelChoiceField(
        label=_("Asset"),
        queryset=Asset.objects.select_related("parent").order_by("slug"),
        help_text=_(
            "The single asset that stops accepting new bookings during the "
            "blackout. Other assets are unaffected."
        ),
    )
    timezone = forms.CharField(
        label=_("Timezone"),
        max_length=TIMEZONE_NAME_MAX_LENGTH,
        initial="Europe/Ljubljana",
        help_text=_(
            "IANA time zone name (for example Europe/Ljubljana) used to "
            "interpret the start and end you enter."
        ),
    )
    start = forms.CharField(
        label=_("Start"),
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "step": "60"}),
        help_text=_("Local start date and time in the selected timezone."),
    )
    start_fold = forms.ChoiceField(
        label=_("Start occurrence"),
        required=False,
        choices=_FOLD_CHOICES,
        help_text=_(
            "Only needed when this local time falls on a daylight-saving "
            "transition in the selected timezone. Automatic uses the system "
            "default; pick first or second to be explicit."
        ),
    )
    end = forms.CharField(
        label=_("End"),
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "step": "60"}),
        help_text=_(
            "Local end date and time, after the start. New overlapping "
            "bookings are blocked from the start until the end; the end "
            "instant itself is free again."
        ),
    )
    end_fold = forms.ChoiceField(
        label=_("End occurrence"),
        required=False,
        choices=_FOLD_CHOICES,
        help_text=_(
            "Only needed when this local time falls on a daylight-saving "
            "transition in the selected timezone. Automatic uses the system "
            "default; pick first or second to be explicit."
        ),
    )
    reason = forms.CharField(
        label=_("Reason"),
        max_length=1000,
        widget=forms.Textarea,
        help_text=_(
            "Required. Explains the maintenance; stored with the blackout and visible to staff."
        ),
    )
    confirm_overlaps = forms.BooleanField(
        label=_("Create despite overlapping reservations"),
        required=False,
        help_text=_(
            "Needed when the period overlaps existing confirmed or released "
            "reservations. Creating the blackout never cancels or releases "
            "them — it only blocks new overlapping bookings."
        ),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        _wire_field_help(
            self,
            (
                "asset",
                "timezone",
                "start",
                "start_fold",
                "end",
                "end_fold",
                "reason",
                "confirm_overlaps",
            ),
        )

    def clean_timezone(self) -> str:
        value = str(self.cleaned_data["timezone"]).strip()
        validate_timezone_name(value)
        return value

    def clean_reason(self) -> str:
        value = str(self.cleaned_data["reason"]).strip()
        if not value:
            raise forms.ValidationError(_("Reason is required."))
        return value

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        timezone_name = cleaned.get("timezone")
        start_text = cleaned.get("start")
        end_text = cleaned.get("end")
        if not timezone_name or not start_text or not end_text:
            return cleaned
        try:
            start_local = _parse_datetime_local(start_text)
            end_local = _parse_datetime_local(end_text)
        except ValueError:
            raise ValidationError(_("Enter valid local start and end times.")) from None
        try:
            start = interpret_local_wall_time(
                start_local,
                timezone_name=timezone_name,
                fold=_parse_fold(cleaned.get("start_fold")),
            )
            end = interpret_local_wall_time(
                end_local,
                timezone_name=timezone_name,
                fold=_parse_fold(cleaned.get("end_fold")),
            )
        except LocalTimeError as exc:
            raise ValidationError(str(exc)) from exc
        if end.instant <= start.instant:
            self.add_error("end", _("End must be after start."))
            return cleaned
        cleaned["start_instant"] = start.instant
        cleaned["end_instant"] = end.instant
        return cleaned


class ManagementCancellationForm(forms.Form):
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


class ReservationFilterForm(FilterFormMixin, forms.Form):
    asset = forms.ModelChoiceField(
        label=_("Asset"),
        queryset=Asset.objects.select_related("parent").order_by("slug"),
        required=False,
        help_text=_("Narrow the list to one asset (machine or child)."),
    )
    q = forms.CharField(
        label=_("Search"),
        required=False,
        max_length=120,
        help_text=_(
            "Matches the owner's email or display name, or the asset slug or "
            "name (case-insensitive)."
        ),
    )
    status = forms.ChoiceField(
        label=_("Status"),
        required=False,
        choices=[("", "Any status")] + list(Reservation.STATUS_CHOICES),
        help_text=_("Confirmed, cancelled or released."),
    )
    lifecycle = forms.ChoiceField(
        label=_("Lifecycle"),
        required=False,
        choices=[
            ("", "Any lifecycle"),
            (ReservationLifecycle.ACTIVE, "Active"),
            (ReservationLifecycle.UPCOMING, "Upcoming"),
            (ReservationLifecycle.COMPLETED, "Completed"),
            (ReservationLifecycle.CANCELLED, "Cancelled"),
            (ReservationLifecycle.RELEASED, "Released"),
        ],
        help_text=_(
            "Active = started and still running; Upcoming = not started; "
            "Completed = end passed; Cancelled; Released = ended early."
        ),
    )
    from_at = AwareDateTimeFilterField(
        label=_("From (start at or after)"),
        required=False,
        help_text=_(
            "Aware ISO-8601 timestamp, for example 2026-10-05T10:00:00+02:00. "
            "Keep reservations whose start is at or after this."
        ),
    )
    to_at = AwareDateTimeFilterField(
        label=_("To (start before)"),
        required=False,
        help_text=_(
            "Aware ISO-8601 timestamp, for example 2026-10-05T10:00:00+02:00. "
            "Keep reservations whose start is before this."
        ),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["from"] = self.fields.pop("from_at")
        self.fields["to"] = self.fields.pop("to_at")
        _wire_field_help(self, ("asset", "q", "status", "lifecycle", "from", "to"))

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        from_at = cleaned.get("from")
        to_at = cleaned.get("to")
        if from_at and to_at and from_at >= to_at:
            self.add_error("to", _("To must be after from."))
        return cleaned


class AuditFilterForm(FilterFormMixin, forms.Form):
    action = forms.ChoiceField(
        label=_("Action"),
        required=False,
        choices=[("", "Any action")] + list(AuditEvent.ACTION_CHOICES),
        help_text=_("Which operation was recorded."),
    )
    target_type = forms.CharField(
        label=_("Target type"),
        required=False,
        max_length=80,
        help_text=_(
            "The record type the action applied to, for example reservation or reservation_policy."
        ),
    )
    actor = forms.CharField(
        label=_("Actor"),
        required=False,
        max_length=120,
        help_text=_("Who performed it: part of a display name or email, or an exact user UUID."),
    )
    source = forms.ChoiceField(
        label=_("Source"),
        required=False,
        choices=[("", "Any source")] + list(AuditEvent.SOURCE_CHOICES),
        help_text=_("Where the action came from: web, API, admin service or migration."),
    )
    correlation_id = forms.UUIDField(
        label=_("Correlation ID"),
        required=False,
        help_text=_(
            "The UUID that links the events of one operation, for example a "
            "booking and its audit record."
        ),
    )
    occurred_from = AwareDateTimeFilterField(
        label=_("Occurred from"),
        required=False,
        help_text=_(
            "Aware ISO-8601 timestamp, for example 2026-10-05T10:00:00+02:00. "
            "Keep events that happened at or after this."
        ),
    )
    occurred_to = AwareDateTimeFilterField(
        label=_("Occurred to"),
        required=False,
        help_text=_(
            "Aware ISO-8601 timestamp, for example 2026-10-05T10:00:00+02:00. "
            "Keep events that happened at or before this."
        ),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        _wire_field_help(
            self,
            (
                "action",
                "target_type",
                "actor",
                "source",
                "correlation_id",
                "occurred_from",
                "occurred_to",
            ),
        )

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        occurred_from = cleaned.get("occurred_from")
        occurred_to = cleaned.get("occurred_to")
        if occurred_from and occurred_to and occurred_from > occurred_to:
            self.add_error("occurred_to", _("Occurred to must be after occurred from."))
        return cleaned


def _wire_field_help(form: Any, names: tuple[str, ...]) -> None:
    for name in names:
        field = form.fields[name]
        if field.help_text:
            field.widget.attrs["aria-describedby"] = f"id_{name}-help"


def _parse_datetime_local(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is not None:
        raise ValueError("Expected datetime-local value.")
    return parsed


def _parse_fold(value: Any) -> int | None:
    if value in ("", None):
        return None
    return int(value)
