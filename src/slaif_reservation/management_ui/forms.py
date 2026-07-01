from __future__ import annotations

from datetime import datetime
from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from slaif_reservation.accounts.validators import TIMEZONE_NAME_MAX_LENGTH, validate_timezone_name
from slaif_reservation.assets.models import Asset
from slaif_reservation.reservations.models import Reservation, ReservationPolicy
from slaif_reservation.reservations.time_utils import LocalTimeError, interpret_local_wall_time


class ReservationPolicyForm(forms.Form):
    name = forms.CharField(label=_("Name"), max_length=180)
    asset = forms.ModelChoiceField(
        label=_("Asset target"),
        queryset=Asset.objects.select_related("parent").order_by("slug"),
        required=False,
        help_text=_("Leave empty for the global policy."),
    )
    min_duration_minutes = forms.IntegerField(label=_("Minimum duration"), min_value=1)
    max_duration_minutes = forms.IntegerField(label=_("Maximum duration"), min_value=1)
    booking_horizon_days = forms.IntegerField(label=_("Booking horizon days"), min_value=0)
    min_lead_minutes = forms.IntegerField(label=_("Minimum lead minutes"), min_value=0)
    cancellation_cutoff_minutes = forms.IntegerField(
        label=_("Cancellation cutoff minutes"),
        min_value=0,
    )
    max_upcoming_per_principal = forms.IntegerField(
        label=_("Maximum upcoming per principal"),
        min_value=1,
    )
    max_concurrent_per_principal = forms.IntegerField(
        label=_("Maximum concurrent per principal"),
        min_value=1,
    )
    purpose_required = forms.BooleanField(label=_("Purpose required"), required=False)

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


class MaintenanceBlackoutForm(forms.Form):
    asset = forms.ModelChoiceField(
        label=_("Asset"),
        queryset=Asset.objects.select_related("parent").order_by("slug"),
    )
    timezone = forms.CharField(
        label=_("Timezone"),
        max_length=TIMEZONE_NAME_MAX_LENGTH,
        initial="Europe/Ljubljana",
    )
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
    reason = forms.CharField(label=_("Reason"), max_length=1000, widget=forms.Textarea)
    confirm_overlaps = forms.BooleanField(
        label=_("Create despite overlapping reservations"),
        required=False,
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
    )


class ReservationFilterForm(forms.Form):
    asset = forms.ModelChoiceField(
        queryset=Asset.objects.select_related("parent").order_by("slug"),
        required=False,
    )
    q = forms.CharField(required=False, max_length=120)
    status = forms.ChoiceField(
        required=False,
        choices=[("", "Any status")] + list(Reservation.STATUS_CHOICES),
    )


def _parse_datetime_local(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is not None:
        raise ValueError("Expected datetime-local value.")
    return parsed


def _parse_fold(value: Any) -> int | None:
    if value in ("", None):
        return None
    return int(value)
