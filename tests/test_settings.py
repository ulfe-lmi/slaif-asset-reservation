from __future__ import annotations

import os
import subprocess
import sys
import textwrap

import pytest
from django.core.exceptions import ImproperlyConfigured

from slaif_reservation.config.env import env_bool, env_non_negative_int, postgres_database_from_url


def clean_subprocess_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("SLAIF_") and key not in {"DATABASE_URL", "DJANGO_SETTINGS_MODULE"}
    } | {"PYTHONPATH": "src"}


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


def test_hsts_seconds_requires_non_negative_integer() -> None:
    for value in ["-1", "not-an-int"]:
        with pytest.raises(ImproperlyConfigured):
            env_non_negative_int(
                "SLAIF_SECURE_HSTS_SECONDS", default=0, env={"SLAIF_SECURE_HSTS_SECONDS": value}
            )


def test_production_settings_fail_fast_without_required_configuration() -> None:
    env = clean_subprocess_env()

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


def test_asgi_defaults_to_production_and_fails_closed_without_required_configuration() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import slaif_reservation.config.asgi"],
        env=clean_subprocess_env(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "SLAIF_DJANGO_SECRET_KEY is required" in result.stderr


def test_asgi_respects_explicit_local_settings_module() -> None:
    env = clean_subprocess_env()
    env["DJANGO_SETTINGS_MODULE"] = "slaif_reservation.config.settings.local"

    result = subprocess.run(
        [sys.executable, "-c", "import slaif_reservation.config.asgi"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_production_hsts_defaults_are_safe_and_https_controls_remain_enabled() -> None:
    env = clean_subprocess_env() | {
        "DJANGO_SETTINGS_MODULE": "slaif_reservation.config.settings.production",
        "SLAIF_DJANGO_SECRET_KEY": "test-only-production-secret",
        "SLAIF_ALLOWED_HOSTS": "reservation.example.test",
        "SLAIF_CSRF_TRUSTED_ORIGINS": "https://reservation.example.test",
        "DATABASE_URL": "postgres://slaif:slaif@localhost:5432/slaif_reservation",
        "SLAIF_PUBLIC_API_DOCS": "true",
    }

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            textwrap.dedent(
                """
                import django
                django.setup()
                from django.conf import settings
                assert settings.SECURE_HSTS_SECONDS == 0
                assert settings.SECURE_HSTS_INCLUDE_SUBDOMAINS is False
                assert settings.SECURE_HSTS_PRELOAD is False
                assert settings.SECURE_SSL_REDIRECT is True
                assert settings.SESSION_COOKIE_SECURE is True
                assert settings.CSRF_COOKIE_SECURE is True
                assert settings.API_DOCS_PUBLIC is False
                """
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_production_hsts_explicit_opt_in_is_supported() -> None:
    env = clean_subprocess_env() | {
        "DJANGO_SETTINGS_MODULE": "slaif_reservation.config.settings.production",
        "SLAIF_DJANGO_SECRET_KEY": "test-only-production-secret",
        "SLAIF_ALLOWED_HOSTS": "reservation.example.test",
        "SLAIF_CSRF_TRUSTED_ORIGINS": "https://reservation.example.test",
        "DATABASE_URL": "postgres://slaif:slaif@localhost:5432/slaif_reservation",
        "SLAIF_SECURE_HSTS_SECONDS": "31536000",
        "SLAIF_SECURE_HSTS_INCLUDE_SUBDOMAINS": "true",
        "SLAIF_SECURE_HSTS_PRELOAD": "true",
    }

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            textwrap.dedent(
                """
                import django
                django.setup()
                from django.conf import settings
                assert settings.SECURE_HSTS_SECONDS == 31536000
                assert settings.SECURE_HSTS_INCLUDE_SUBDOMAINS is True
                assert settings.SECURE_HSTS_PRELOAD is True
                """
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("value", ["-1", "not-an-int"])
def test_production_hsts_rejects_invalid_seconds(value: str) -> None:
    env = clean_subprocess_env() | {
        "DJANGO_SETTINGS_MODULE": "slaif_reservation.config.settings.production",
        "SLAIF_DJANGO_SECRET_KEY": "test-only-production-secret",
        "SLAIF_ALLOWED_HOSTS": "reservation.example.test",
        "SLAIF_CSRF_TRUSTED_ORIGINS": "https://reservation.example.test",
        "DATABASE_URL": "postgres://slaif:slaif@localhost:5432/slaif_reservation",
        "SLAIF_SECURE_HSTS_SECONDS": value,
    }

    result = subprocess.run(
        [sys.executable, "-c", "import django; django.setup()"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "SLAIF_SECURE_HSTS_SECONDS must be a non-negative integer" in result.stderr
