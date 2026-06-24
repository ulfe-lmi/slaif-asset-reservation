from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError
from django.utils import timezone

from slaif_reservation.accounts.validators import validate_timezone_name


class LocalTimeError(ValueError):
    pass


class InstantError(ValueError):
    pass


@dataclass(frozen=True)
class LocalTimeResult:
    local: datetime
    instant: datetime
    timezone: str
    fold: int


def require_aware_utc(value: datetime, *, field_name: str = "datetime") -> datetime:
    if not isinstance(value, datetime) or not timezone.is_aware(value):
        raise InstantError(f"{field_name} must be timezone-aware.")
    return value.astimezone(UTC)


def interpret_local_wall_time(
    local_time: datetime,
    *,
    timezone_name: str,
    fold: int | None = None,
) -> LocalTimeResult:
    if local_time.tzinfo is not None:
        raise LocalTimeError("Local wall time must be naive.")
    if fold not in (None, 0, 1):
        raise LocalTimeError("Fold must be 0, 1, or omitted.")

    try:
        validate_timezone_name(timezone_name)
        zone = ZoneInfo(timezone_name)
    except (ValidationError, ZoneInfoNotFoundError, ValueError) as exc:
        raise LocalTimeError("Timezone must resolve through zoneinfo.") from exc

    candidates = []
    for candidate_fold in (0, 1):
        aware = local_time.replace(tzinfo=zone, fold=candidate_fold)
        round_trip = aware.astimezone(UTC).astimezone(zone).replace(tzinfo=None)
        if round_trip == local_time:
            candidates.append((candidate_fold, aware, aware.utcoffset()))

    if not candidates:
        raise LocalTimeError("Local wall time does not exist in this timezone.")

    unique_offsets = {candidate[2] for candidate in candidates}
    if len(unique_offsets) > 1:
        if fold is None:
            raise LocalTimeError("Local wall time is ambiguous; specify fold.")
        for candidate_fold, aware, _offset in candidates:
            if candidate_fold == fold:
                return LocalTimeResult(
                    local=local_time,
                    instant=aware.astimezone(UTC),
                    timezone=timezone_name,
                    fold=candidate_fold,
                )
        raise LocalTimeError("Requested fold is not valid for this local time.")

    candidate_fold, aware, _offset = candidates[0]
    return LocalTimeResult(
        local=local_time,
        instant=aware.astimezone(UTC),
        timezone=timezone_name,
        fold=candidate_fold,
    )
