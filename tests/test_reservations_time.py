from __future__ import annotations

from datetime import datetime

import pytest

from slaif_reservation.reservations.time_utils import LocalTimeError, interpret_local_wall_time

OVERLONG_TIMEZONE = "A" * 1000


def test_unambiguous_local_wall_time_returns_aware_utc_instant() -> None:
    result = interpret_local_wall_time(
        datetime(2026, 2, 1, 12, 0),
        timezone_name="Europe/Ljubljana",
    )

    assert result.instant.tzinfo is not None
    assert result.instant.isoformat() == "2026-02-01T11:00:00+00:00"


def test_nonexistent_dst_wall_time_is_rejected() -> None:
    with pytest.raises(LocalTimeError, match="does not exist"):
        interpret_local_wall_time(
            datetime(2026, 3, 29, 2, 30),
            timezone_name="Europe/Ljubljana",
        )


def test_ambiguous_dst_wall_time_requires_explicit_fold() -> None:
    with pytest.raises(LocalTimeError, match="ambiguous"):
        interpret_local_wall_time(
            datetime(2026, 10, 25, 2, 30),
            timezone_name="Europe/Ljubljana",
        )

    first = interpret_local_wall_time(
        datetime(2026, 10, 25, 2, 30),
        timezone_name="Europe/Ljubljana",
        fold=0,
    )
    second = interpret_local_wall_time(
        datetime(2026, 10, 25, 2, 30),
        timezone_name="Europe/Ljubljana",
        fold=1,
    )

    assert first.instant.isoformat() == "2026-10-25T00:30:00+00:00"
    assert second.instant.isoformat() == "2026-10-25T01:30:00+00:00"


def test_aware_local_wall_time_is_rejected() -> None:
    aware = datetime.fromisoformat("2026-02-01T12:00:00+01:00")

    with pytest.raises(LocalTimeError, match="must be naive"):
        interpret_local_wall_time(aware, timezone_name="Europe/Ljubljana")


@pytest.mark.parametrize(
    "timezone_name",
    ["/etc/passwd", "../UTC", "a/../UTC", "Mars/Base", "", OVERLONG_TIMEZONE, "UTC\x00"],
)
def test_malformed_timezone_key_is_rejected_cleanly(timezone_name: str) -> None:
    with pytest.raises(LocalTimeError, match="Timezone must resolve"):
        interpret_local_wall_time(datetime(2026, 2, 1, 12, 0), timezone_name=timezone_name)
