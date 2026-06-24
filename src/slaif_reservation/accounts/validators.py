from __future__ import annotations

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_timezone_name(value: str) -> None:
    if not value or not value.strip():
        raise ValidationError(_("Timezone is required."), code="required")
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValidationError(_("Enter a valid IANA timezone name."), code="invalid") from exc
