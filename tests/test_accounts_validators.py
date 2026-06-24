from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError

from slaif_reservation.accounts.validators import validate_timezone_name


@pytest.mark.parametrize(
    "timezone_name",
    ["/etc/passwd", "../UTC", "a/../UTC", "Mars/Base", ""],
)
def test_validate_timezone_name_rejects_malformed_unknown_and_blank_values(
    timezone_name: str,
) -> None:
    with pytest.raises(ValidationError):
        validate_timezone_name(timezone_name)


def test_validate_timezone_name_accepts_valid_non_default_timezone() -> None:
    validate_timezone_name("America/New_York")
