from __future__ import annotations

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

TIMEZONE_NAME_MAX_LENGTH = 64


def validate_timezone_name(value: str) -> None:
    if not value or not value.strip():
        raise ValidationError(_("Timezone is required."), code="required")
    if len(value) > TIMEZONE_NAME_MAX_LENGTH:
        raise ValidationError(
            _("Ensure this value has at most %(limit_value)d characters."),
            code="max_length",
            params={"limit_value": TIMEZONE_NAME_MAX_LENGTH},
        )
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError, OSError) as exc:
        raise ValidationError(_("Enter a valid IANA timezone name."), code="invalid") from exc
