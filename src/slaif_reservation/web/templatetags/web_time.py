from __future__ import annotations

from datetime import datetime

from django import template

from slaif_reservation.reservations.time_utils import InstantError, require_aware_utc

register = template.Library()


@register.filter
def utc_datetime(value: datetime | None) -> str:
    if value is None:
        return ""
    try:
        utc_value = require_aware_utc(value)
    except InstantError:
        return ""
    return utc_value.isoformat().replace("+00:00", "Z")
