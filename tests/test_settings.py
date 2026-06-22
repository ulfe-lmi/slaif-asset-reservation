from __future__ import annotations

import os
import subprocess
import sys

import pytest
from django.core.exceptions import ImproperlyConfigured

from slaif_reservation.config.env import env_bool, postgres_database_from_url


@pytest.mark.parametrize("value", ["false", "False", "0", "no", "off", ""])
def test_boolean_parser_does_not_enable_debug_for_false_values(value: str) -> None:
    assert env_bool("SLAIF_DEBUG", default=True, env={"SLAIF_DEBUG": value}) is False


@pytest.mark.parametrize("value", ["true", "1", "yes", "on"])
def test_boolean_parser_accepts_true_values(value: str) -> None:
    assert env_bool("SLAIF_DEBUG", default=False, env={"SLAIF_DEBUG": value}) is True


def test_boolean_parser_rejects_ambiguous_values() -> None:
    with pytest.raises(ImproperlyConfigured):
        env_bool("SLAIF_DEBUG", default=False, env={"SLAIF_DEBUG": "sometimes"})


def test_database_url_requires_postgresql() -> None:
    with pytest.raises(ImproperlyConfigured):
        postgres_database_from_url("sqlite:///db.sqlite3")


def test_production_settings_fail_fast_without_required_configuration() -> None:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("SLAIF_") and key not in {"DATABASE_URL", "DJANGO_SETTINGS_MODULE"}
    }
    env["PYTHONPATH"] = "src"

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import os; "
                "os.environ['DJANGO_SETTINGS_MODULE']="
                "'slaif_reservation.config.settings.production'; "
                "import django; django.setup()"
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "SLAIF_DJANGO_SECRET_KEY is required" in result.stderr
