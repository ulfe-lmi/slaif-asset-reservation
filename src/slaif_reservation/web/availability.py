from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from django.utils import timezone

from slaif_reservation.assets.models import Asset
from slaif_reservation.reservations.exceptions import ReservationDomainError
from slaif_reservation.reservations.models import Reservation
from slaif_reservation.reservations.services import resolve_effective_policy
from slaif_reservation.reservations.time_utils import (
    LocalTimeError,
    interpret_local_wall_time,
    require_aware_utc,
)

MAX_AVAILABILITY_DAYS = 7


@dataclass(frozen=True)
class AvailabilityBusyInterval:
    start: datetime
    end: datetime
    label: str
    reservation_id: Any | None = None


@dataclass(frozen=True)
class AvailabilityFreeInterval:
    start: datetime
    end: datetime
    latest_start: datetime


@dataclass(frozen=True)
class AvailabilityResult:
    asset: Asset
    timezone: str
    start: datetime
    end: datetime
    busy: list[AvailabilityBusyInterval]
    free: list[AvailabilityFreeInterval]
    bookable: bool
    reason: str
    min_duration_minutes: int | None = None
    advisory_notice: str = (
        "Availability is advisory and does not yet model maintenance blackouts or operating hours."
    )


def availability_for_asset(
    *,
    asset: Asset,
    principal: Any,
    start_date: date,
    days: int = MAX_AVAILABILITY_DAYS,
    display_timezone: str,
    now: datetime | None = None,
) -> AvailabilityResult:
    if days < 1 or days > MAX_AVAILABILITY_DAYS:
        raise ValueError("Availability windows must be between 1 and 7 days.")

    now_utc = require_aware_utc(timezone.now() if now is None else now, field_name="now")
    window_start = _local_midnight(start_date, display_timezone)
    window_end = _local_midnight(start_date + timedelta(days=days), display_timezone)

    not_bookable = _non_bookable_reason(asset)
    policy = None
    if not_bookable is None:
        try:
            policy = resolve_effective_policy(asset)
        except ReservationDomainError:
            not_bookable = "No unambiguous active reservation policy applies to this asset."

    busy = _busy_intervals(
        asset=asset,
        principal=principal,
        window_start=window_start,
        window_end=window_end,
    )

    if not_bookable is not None or policy is None:
        return AvailabilityResult(
            asset=asset,
            timezone=display_timezone,
            start=window_start,
            end=window_end,
            busy=busy,
            free=[],
            bookable=False,
            reason=not_bookable or "This asset is not currently bookable.",
        )

    earliest_start = max(window_start, now_utc + timedelta(minutes=policy.min_lead_minutes))
    latest_policy_start = now_utc + timedelta(days=policy.booking_horizon_days)
    free = _free_intervals(
        window_start=window_start,
        window_end=window_end,
        busy=busy,
        earliest_start=earliest_start,
        latest_policy_start=latest_policy_start,
        min_duration=timedelta(minutes=policy.min_duration_minutes),
    )
    return AvailabilityResult(
        asset=asset,
        timezone=display_timezone,
        start=window_start,
        end=window_end,
        busy=busy,
        free=free,
        bookable=True,
        reason="",
        min_duration_minutes=policy.min_duration_minutes,
    )


def _non_bookable_reason(asset: Asset) -> str | None:
    if not asset.active:
        return "This asset is inactive."
    if not asset.reservable:
        return "This asset is not reservable."
    if asset.booking_mode != Asset.BOOKING_EXCLUSIVE:
        return "This asset uses an unsupported booking mode."
    return None


def _local_midnight(value: date, timezone_name: str) -> datetime:
    try:
        return interpret_local_wall_time(
            datetime.combine(value, time.min),
            timezone_name=timezone_name,
        ).instant
    except LocalTimeError:
        zone = ZoneInfo(timezone_name)
        return datetime.combine(value, time.min, tzinfo=zone).astimezone(UTC)


def _busy_intervals(
    *,
    asset: Asset,
    principal: Any,
    window_start: datetime,
    window_end: datetime,
) -> list[AvailabilityBusyInterval]:
    reservations = (
        Reservation.objects.filter(
            asset=asset,
            status__in=[Reservation.STATUS_CONFIRMED, Reservation.STATUS_RELEASED],
            start_at__lt=window_end,
            effective_end_at__gt=window_start,
        )
        .select_related("requested_by_user")
        .order_by("start_at", "effective_end_at")
    )

    intervals: list[AvailabilityBusyInterval] = []
    for reservation in reservations:
        start = max(require_aware_utc(reservation.start_at), window_start)
        end = min(require_aware_utc(reservation.effective_end_at), window_end)
        if end <= start:
            continue
        is_own = reservation.requested_by_user_id == principal.pk
        intervals.append(
            AvailabilityBusyInterval(
                start=start,
                end=end,
                label="Your reservation" if is_own else "Unavailable",
                reservation_id=reservation.id if is_own else None,
            )
        )
    return _merge_busy(intervals)


def _merge_busy(intervals: list[AvailabilityBusyInterval]) -> list[AvailabilityBusyInterval]:
    merged: list[AvailabilityBusyInterval] = []
    for interval in intervals:
        if not merged or interval.start > merged[-1].end:
            merged.append(interval)
            continue
        previous = merged[-1]
        label = previous.label
        reservation_id = previous.reservation_id
        if previous.label != interval.label or previous.reservation_id != interval.reservation_id:
            label = "Unavailable"
            reservation_id = None
        merged[-1] = AvailabilityBusyInterval(
            start=previous.start,
            end=max(previous.end, interval.end),
            label=label,
            reservation_id=reservation_id,
        )
    return merged


def _free_intervals(
    *,
    window_start: datetime,
    window_end: datetime,
    busy: list[AvailabilityBusyInterval],
    earliest_start: datetime,
    latest_policy_start: datetime,
    min_duration: timedelta,
) -> list[AvailabilityFreeInterval]:
    candidates: list[tuple[datetime, datetime]] = []
    cursor = window_start
    for interval in busy:
        if interval.start > cursor:
            candidates.append((cursor, interval.start))
        cursor = max(cursor, interval.end)
    if cursor < window_end:
        candidates.append((cursor, window_end))

    free: list[AvailabilityFreeInterval] = []
    for raw_start, raw_end in candidates:
        start = max(raw_start, earliest_start)
        end = raw_end
        latest_start = min(end - min_duration, latest_policy_start)
        if latest_start < start:
            continue
        free.append(AvailabilityFreeInterval(start=start, end=end, latest_start=latest_start))
    return free
