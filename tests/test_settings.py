from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap

import pytest
from django.core.exceptions import ImproperlyConfigured

from slaif_reservation.accounts.tokens import UNSAFE_API_TOKEN_PEPPERS
from slaif_reservation.config.env import (
    UNSAFE_SECRET_KEYS,
    env_bool,
    env_non_negative_int,
    postgres_database_from_url,
    validate_allowed_host_entry,
    validate_csrf_origin,
)

TEST_PRODUCTION_API_TOKEN_PEPPER = "valid-production-test-api-token-pepper-32-bytes"
TEST_PRODUCTION_SECRET_KEY = "valid-production-secret-key-for-tests-32-bytes"


def clean_subprocess_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("SLAIF_") and key not in {"DATABASE_URL", "DJANGO_SETTINGS_MODULE"}
    } | {"PYTHONPATH": "src"}


def production_settings_env() -> dict[str, str]:
    return clean_subprocess_env() | {
        "DJANGO_SETTINGS_MODULE": "slaif_reservation.config.settings.production",
        "SLAIF_DJANGO_SECRET_KEY": TEST_PRODUCTION_SECRET_KEY,
        "SLAIF_ALLOWED_HOSTS": "reservation.example.test",
        "SLAIF_CSRF_TRUSTED_ORIGINS": "https://reservation.example.test",
        "SLAIF_TRUSTED_PROXY_PEERS": "127.0.0.1,::1",
        "DATABASE_URL": "postgres://slaif:slaif@localhost:5432/slaif_reservation",
        "SLAIF_API_TOKEN_PEPPER": TEST_PRODUCTION_API_TOKEN_PEPPER,
    }


def run_django_setup(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", "import django; django.setup()"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


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


@pytest.mark.parametrize(
    "secret_key",
    [
        "unsafe-local-development-key",
        "test-only-secret-key",
        "too-short",
    ],
)
def test_production_settings_reject_placeholder_or_short_secret_key(secret_key: str) -> None:
    env = production_settings_env() | {"SLAIF_DJANGO_SECRET_KEY": secret_key}

    result = run_django_setup(env)

    assert result.returncode != 0
    assert "SLAIF_DJANGO_SECRET_KEY is invalid for production settings" in result.stderr
    assert secret_key not in result.stderr


@pytest.mark.parametrize(
    "secret_key",
    [
        "REPLACE_WITH_AT_LEAST_32_BYTES_FROM_A_PROTECTED_SECRET_STORE",
        "  REPLACE_WITH_AT_LEAST_32_BYTES_FROM_A_PROTECTED_SECRET_STORE\n",
    ],
)
def test_production_settings_reject_committed_secret_key_placeholders(secret_key: str) -> None:
    env = production_settings_env() | {"SLAIF_DJANGO_SECRET_KEY": secret_key}

    result = run_django_setup(env)

    assert result.returncode != 0
    assert "SLAIF_DJANGO_SECRET_KEY is invalid for production settings" in result.stderr
    assert secret_key.strip() not in result.stderr


@pytest.mark.parametrize(
    "pepper",
    [
        "REPLACE_WITH_DISTINCT_AT_LEAST_32_BYTE_PEPPER",
        "  REPLACE_WITH_DISTINCT_AT_LEAST_32_BYTE_PEPPER\n",
    ],
)
def test_production_settings_reject_committed_api_token_pepper_placeholders(
    pepper: str,
) -> None:
    env = production_settings_env() | {"SLAIF_API_TOKEN_PEPPER": pepper}

    result = run_django_setup(env)

    assert result.returncode != 0
    assert "SLAIF_API_TOKEN_PEPPER is invalid for production settings" in result.stderr
    assert pepper.strip() not in result.stderr


def test_production_settings_placeholder_sets_cover_committed_production_examples() -> None:
    assert "REPLACE_WITH_AT_LEAST_32_BYTES_FROM_A_PROTECTED_SECRET_STORE" in UNSAFE_SECRET_KEYS
    assert "REPLACE_WITH_DISTINCT_AT_LEAST_32_BYTE_PEPPER" in UNSAFE_API_TOKEN_PEPPERS


def test_production_settings_accept_valid_distinct_non_placeholder_secrets() -> None:
    result = run_django_setup(production_settings_env())

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "missing_name",
    ["SLAIF_ALLOWED_HOSTS", "SLAIF_CSRF_TRUSTED_ORIGINS"],
)
def test_production_settings_require_hosts_and_csrf_origins(missing_name: str) -> None:
    env = production_settings_env()
    env.pop(missing_name)

    result = subprocess.run(
        [sys.executable, "-c", "import django; django.setup()"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert missing_name in result.stderr


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


def test_local_settings_honor_custom_allowed_hosts_and_csrf_origins() -> None:
    env = clean_subprocess_env() | {
        "DJANGO_SETTINGS_MODULE": "slaif_reservation.config.settings.local",
        "SLAIF_ALLOWED_HOSTS": "example.test,localhost",
        "SLAIF_CSRF_TRUSTED_ORIGINS": "https://example.test,http://localhost:8000",
    }

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            textwrap.dedent(
                """
                import json
                import django
                django.setup()
                from django.conf import settings
                print(json.dumps({
                    "allowed_hosts": settings.ALLOWED_HOSTS,
                    "csrf_trusted_origins": settings.CSRF_TRUSTED_ORIGINS,
                }))
                """
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["allowed_hosts"] == ["example.test", "localhost"]
    assert payload["csrf_trusted_origins"] == ["https://example.test", "http://localhost:8000"]


def test_local_settings_honor_custom_api_docs_flags() -> None:
    env = clean_subprocess_env() | {
        "DJANGO_SETTINGS_MODULE": "slaif_reservation.config.settings.local",
        "SLAIF_ENABLE_API_DOCS": "false",
        "SLAIF_PUBLIC_API_DOCS": "false",
    }

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            textwrap.dedent(
                """
                import json
                import django
                django.setup()
                from django.conf import settings
                print(json.dumps({
                    "api_docs_enabled": settings.API_DOCS_ENABLED,
                    "api_docs_public": settings.API_DOCS_PUBLIC,
                }))
                """
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {"api_docs_enabled": False, "api_docs_public": False}


def test_local_settings_preserve_safe_defaults_when_environment_absent() -> None:
    env = clean_subprocess_env() | {
        "DJANGO_SETTINGS_MODULE": "slaif_reservation.config.settings.local",
    }

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            textwrap.dedent(
                """
                import json
                import django
                django.setup()
                from django.conf import settings
                print(json.dumps({
                    "allowed_hosts": settings.ALLOWED_HOSTS,
                    "csrf_trusted_origins": settings.CSRF_TRUSTED_ORIGINS,
                    "api_docs_enabled": settings.API_DOCS_ENABLED,
                    "api_docs_public": settings.API_DOCS_PUBLIC,
                }))
                """
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {
        "allowed_hosts": ["localhost", "127.0.0.1", "0.0.0.0"],
        "csrf_trusted_origins": ["http://localhost:8000", "http://127.0.0.1:8000"],
        "api_docs_enabled": True,
        "api_docs_public": True,
    }


def test_production_hsts_defaults_are_safe_and_https_controls_remain_enabled() -> None:
    env = clean_subprocess_env() | {
        "DJANGO_SETTINGS_MODULE": "slaif_reservation.config.settings.production",
        "SLAIF_DJANGO_SECRET_KEY": TEST_PRODUCTION_SECRET_KEY,
        "SLAIF_ALLOWED_HOSTS": "reservation.example.test",
        "SLAIF_CSRF_TRUSTED_ORIGINS": "https://reservation.example.test",
        "SLAIF_TRUSTED_PROXY_PEERS": "127.0.0.1,::1",
        "DATABASE_URL": "postgres://slaif:slaif@localhost:5432/slaif_reservation",
        "SLAIF_API_TOKEN_PEPPER": TEST_PRODUCTION_API_TOKEN_PEPPER,
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
        "SLAIF_DJANGO_SECRET_KEY": TEST_PRODUCTION_SECRET_KEY,
        "SLAIF_ALLOWED_HOSTS": "reservation.example.test",
        "SLAIF_CSRF_TRUSTED_ORIGINS": "https://reservation.example.test",
        "SLAIF_TRUSTED_PROXY_PEERS": "127.0.0.1,::1",
        "DATABASE_URL": "postgres://slaif:slaif@localhost:5432/slaif_reservation",
        "SLAIF_API_TOKEN_PEPPER": TEST_PRODUCTION_API_TOKEN_PEPPER,
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
        "SLAIF_DJANGO_SECRET_KEY": TEST_PRODUCTION_SECRET_KEY,
        "SLAIF_ALLOWED_HOSTS": "reservation.example.test",
        "SLAIF_CSRF_TRUSTED_ORIGINS": "https://reservation.example.test",
        "SLAIF_TRUSTED_PROXY_PEERS": "127.0.0.1,::1",
        "DATABASE_URL": "postgres://slaif:slaif@localhost:5432/slaif_reservation",
        "SLAIF_API_TOKEN_PEPPER": TEST_PRODUCTION_API_TOKEN_PEPPER,
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


@pytest.mark.parametrize(
    "peers",
    [
        "0.0.0.0/0",
        "::/0",
        "172.16.0.0/12",
        "10.0.0.0/8",
        "192.168.0.0/24",
        "192.168.0.0/30",
        "192.168.0.1/33",
        "not-an-ip",
    ],
)
def test_production_settings_reject_wildcard_or_broad_proxy_trust(peers: str) -> None:
    env = production_settings_env() | {"SLAIF_TRUSTED_PROXY_PEERS": peers}

    result = run_django_setup(env)

    assert result.returncode != 0
    assert "SLAIF_TRUSTED_PROXY_PEERS" in result.stderr


def test_production_settings_require_trusted_proxy_peers() -> None:
    env = production_settings_env()
    env.pop("SLAIF_TRUSTED_PROXY_PEERS")

    result = run_django_setup(env)

    assert result.returncode != 0
    assert "SLAIF_TRUSTED_PROXY_PEERS is required" in result.stderr


def test_production_settings_accept_explicit_host_and_point_to_point_peers() -> None:
    env = production_settings_env() | {
        "SLAIF_TRUSTED_PROXY_PEERS": "127.0.0.1,172.17.0.1,172.17.0.2/31,::1"
    }

    result = run_django_setup(env)

    assert result.returncode == 0, result.stderr


def test_production_settings_reject_wildcard_allowed_host() -> None:
    env = production_settings_env() | {"SLAIF_ALLOWED_HOSTS": "*"}

    result = run_django_setup(env)

    assert result.returncode != 0
    assert "SLAIF_ALLOWED_HOSTS" in result.stderr


def test_production_settings_reject_http_origin_while_ssl_redirect_enabled() -> None:
    env = production_settings_env() | {
        "SLAIF_CSRF_TRUSTED_ORIGINS": "http://reservation.example.test"
    }

    result = run_django_setup(env)

    assert result.returncode != 0
    assert "SLAIF_CSRF_TRUSTED_ORIGINS" in result.stderr


def test_production_settings_allow_http_origin_only_without_ssl_redirect() -> None:
    # The disposable loopback rehearsal uses production settings with the
    # redirect explicitly disabled; http origins are the consistent pair.
    env = production_settings_env() | {
        "SLAIF_SECURE_SSL_REDIRECT": "false",
        "SLAIF_CSRF_TRUSTED_ORIGINS": "http://127.0.0.1",
    }

    result = run_django_setup(env)

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "origin",
    [
        "https://reservation.example.test/path",
        "https://user:pass@reservation.example.test",
        "ftp://reservation.example.test",
        "https://",
        "https://reservation.example.test?x=1",
    ],
)
def test_production_settings_reject_malformed_csrf_origins(origin: str) -> None:
    env = production_settings_env() | {"SLAIF_CSRF_TRUSTED_ORIGINS": origin}

    result = run_django_setup(env)

    assert result.returncode != 0
    assert "SLAIF_CSRF_TRUSTED_ORIGINS" in result.stderr


def test_production_settings_do_not_reintroduce_blanket_proxy_header_trust() -> None:
    env = production_settings_env()

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            textwrap.dedent(
                """
                import json
                import django
                django.setup()
                from django.conf import settings
                print(json.dumps({
                    "proxy_ssl_header": getattr(settings, "SECURE_PROXY_SSL_HEADER", None),
                    "referrer_policy": settings.SECURE_REFERRER_POLICY,
                }))
                """
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["proxy_ssl_header"] is None
    assert payload["referrer_policy"] == "strict-origin-when-cross-origin"


# ---------------------------------------------------------------------------
# ALLOWED_HOSTS entry validation (explicit bare hosts only)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "entry",
    [
        "reservation.example.test",
        "127.0.0.1",
        "192.168.4.10",
        "::1",
        "2001:db8::5",
        "[2001:db8::5]",
        "a-b.example.test",
    ],
)
def test_allowed_host_entry_accepts_explicit_bare_hosts(entry: str) -> None:
    expected = f"[{entry}]" if ":" in entry and not entry.startswith("[") else entry
    assert validate_allowed_host_entry(entry) == expected


@pytest.mark.parametrize(
    "entry,category",
    [
        ("https://reservation.example.test", "scheme"),
        ("//cdn.example.test", "scheme"),
        ("reservation.example.test:8443", "ports"),
        ("[2001:db8::5]:8443", "IP literal"),
        ("user:pass@reservation.example.test", "userinfo"),
        ("res ervation.example.test", "whitespace"),
        ("reservation.example.test/path", "hostnames or IP"),
        ("reservation.example.test?x=1", "hostnames or IP"),
        ("reservation.example.test#frag", "hostnames or IP"),
        ("*.example.org", "hostnames or IP"),
        ("example.org*", "hostnames or IP"),
        ("*.*.example.org", "hostnames or IP"),
        (".example.org", "without wildcards"),
        (".example.org:8443", "without wildcards"),
        (".10.0.0.1", "without wildcards"),
        ("a..b.example.test", "hostnames or IP"),
        ("-bad.example.test", "hostnames or IP"),
        ("bad-.example.test", "hostnames or IP"),
        ("a" * 64 + ".example.test", "hostnames or IP"),
    ],
)
def test_allowed_host_entry_rejects_malformed_fail_closed(entry: str, category: str) -> None:
    with pytest.raises(ImproperlyConfigured, match=category):
        validate_allowed_host_entry(entry)


@pytest.mark.parametrize(
    "hosts,needle",
    [
        ("https://reservation.example.test", "scheme"),
        ("reservation.example.test:8443", "ports"),
        ("user:pass@reservation.example.test", "userinfo"),
        ("res ervation.example.test", "whitespace"),
        ("*.example.org", "hostnames or IP"),
    ],
)
def test_production_settings_reject_malformed_allowed_hosts(hosts: str, needle: str) -> None:
    env = production_settings_env() | {"SLAIF_ALLOWED_HOSTS": hosts}
    result = run_django_setup(env)
    assert result.returncode != 0
    assert needle in result.stderr
    # Fail-closed without echoing the raw configured value.
    assert hosts not in result.stderr


def test_production_settings_accept_valid_allowed_hosts() -> None:
    env = production_settings_env() | {
        "SLAIF_ALLOWED_HOSTS": "reservation.example.test,127.0.0.1,[2001:db8::5]"
    }
    result = run_django_setup(env)
    assert result.returncode == 0, result.stderr


# ---------------------------------------------------------------------------
# HSTS combination contract (supported explicit HTTPS contract)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "extra,needle",
    [
        (
            {"SLAIF_SECURE_SSL_REDIRECT": "false", "SLAIF_SECURE_HSTS_SECONDS": "3600"},
            "only supported while",
        ),
        (
            {"SLAIF_SECURE_HSTS_INCLUDE_SUBDOMAINS": "true"},
            "require a non-zero",
        ),
        ({"SLAIF_SECURE_HSTS_PRELOAD": "true"}, "require a non-zero"),
        (
            {"SLAIF_SECURE_HSTS_INCLUDE_SUBDOMAINS": "true", "SLAIF_SECURE_HSTS_PRELOAD": "true"},
            "require a non-zero",
        ),
    ],
)
def test_production_settings_reject_out_of_contract_hsts_combinations(
    extra: dict[str, str], needle: str
) -> None:
    result = run_django_setup(production_settings_env() | extra)
    assert result.returncode != 0
    assert needle in result.stderr


def test_production_settings_accept_in_contract_hsts_combination() -> None:
    extra = {
        "SLAIF_SECURE_HSTS_SECONDS": "31536000",
        "SLAIF_SECURE_HSTS_INCLUDE_SUBDOMAINS": "true",
        "SLAIF_SECURE_HSTS_PRELOAD": "true",
    }
    result = run_django_setup(production_settings_env() | extra)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "origin",
    [
        "https://*.example.test",
        "https://.example.test",
        "https://example.test:abc",
        "https://example.test:99999",
        "https://example.test:0",
        "https://example.test:",
        "https://[fe80::1%zone]",
        "https://exa\nmple.test",
    ],
)
def test_csrf_origin_rejects_wildcards_invalid_ports_and_scoped_addresses(origin: str) -> None:
    with pytest.raises(ImproperlyConfigured):
        validate_csrf_origin(origin)


def test_uppercase_http_origin_cannot_bypass_production_https_requirement() -> None:
    result = run_django_setup(
        production_settings_env() | {"SLAIF_CSRF_TRUSTED_ORIGINS": "HTTP://example.test"}
    )
    assert result.returncode != 0
    assert "must be https origins" in result.stderr
