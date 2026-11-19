"""Focused settings/transport tests for the opt-in account email capability.

Order 057-a scope (SAR-055, no account-creation email in this objective):
- the canonical https base URL validator (fail-closed, category-only
  error messages);
- the resolver positive mapping and the fail-closed negative matrix
  (in-process, no relay, no network);
- production settings load: the disabled default preserves startup with
  the dummy backend and no outbound SMTP backend; a valid enabled
  configuration selects Django's built-in SMTP backend with the exact
  mapped values; invalid combinations fail closed without echoing raw
  values or credentials;
- a synthetic local SMTP sink (stdlib socket, loopback only) proves the
  Django SMTP backend can send one simple message under test overrides
  with no real recipient or relay; a disabled configuration sends
  nothing.

Order 057-b corrections (same objective, fail-closed closure):
- empty URL userinfo (``https://@host``) is rejected instead of being
  normalized away, and surrounding base-URL whitespace is rejected by the
  resolver instead of being silently stripped;
- ``SLAIF_SMTP_FROM`` must be a valid bare email address (malformed,
  whitespace and CRLF/header-injection forms are rejected with a
  category-only message);
- ``AccountEmailSettings`` never exposes the SMTP password through
  repr/str/equality while keeping the value attribute-accessible.

No user model or migration change; no real SMTP relay/recipient/credential
is used or required.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading

import pytest
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from slaif_reservation.config.email import (
    DISABLED_EMAIL_BACKEND,
    SMTP_EMAIL_BACKEND,
    AccountEmailSettings,
    resolve_account_email_settings,
)
from slaif_reservation.config.env import validate_canonical_service_url

# Synthetic canaries only; never real relay/recipient/credential values.
TEST_SMTP_HOST = "smtp.example.test"
TEST_SMTP_USERNAME = "synthetic-relay-user"
TEST_SMTP_PASSWORD = "synthetic-smtp-password-057a"
TEST_SMTP_FROM = "no-reply@example.test"
TEST_BASE_URL = "https://reservation.example.test"

ALLOWED_HOSTS = ("reservation.example.test",)
CSRF_ORIGINS = ("https://reservation.example.test",)


# --- canonical service URL validator -------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://reservation.example.test", "https://reservation.example.test"),
        ("https://res.sub.example.test:8443", "https://res.sub.example.test:8443"),
        ("https://10.1.2.3", "https://10.1.2.3"),
        ("https://[2001:db8::1]", "https://[2001:db8::1]"),
        ("HTTPS://Reservation.Example.test/", "https://reservation.example.test"),
    ],
)
def test_canonical_service_url_accepts_https_origins(raw: str, expected: str) -> None:
    assert validate_canonical_service_url(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "http://reservation.example.test",
        "ftp://reservation.example.test",
        "//reservation.example.test",
        "https://",
        "https://reservation.example.test/path",
        "https://reservation.example.test/?next=1",
        "https://reservation.example.test#anchor",
        # Empty userinfo must be rejected, not normalized away.
        "https://@reservation.example.test",
        "https://:@reservation.example.test",
        "https://user:pass@reservation.example.test",
        "https://reservation.example.test:0",
        "https://reservation.example.test:99999",
        "https://res ervation.example.test",
        "https://*.example.test",
        "https://res..ervation.example.test",
    ],
)
def test_canonical_service_url_rejects_non_canonical_urls(raw: str) -> None:
    with pytest.raises(ImproperlyConfigured):
        validate_canonical_service_url(raw)


# --- resolver --------------------------------------------------------------


def enabled_env(**overrides: str) -> dict[str, str]:
    env = {
        "SLAIF_ACCOUNT_EMAIL_ENABLED": "true",
        "SLAIF_PUBLIC_BASE_URL": TEST_BASE_URL,
        "SLAIF_SMTP_HOST": TEST_SMTP_HOST,
        "SLAIF_SMTP_PORT": "587",
        "SLAIF_SMTP_USERNAME": TEST_SMTP_USERNAME,
        "SLAIF_SMTP_PASSWORD": TEST_SMTP_PASSWORD,
        "SLAIF_SMTP_FROM": TEST_SMTP_FROM,
        "SLAIF_SMTP_USE_SSL": "false",
        "SLAIF_SMTP_STARTTLS": "true",
        "SLAIF_SMTP_TIMEOUT_SECONDS": "30",
    }
    env.update(overrides)
    return env


def resolve_production(env: dict[str, str]):
    return resolve_account_email_settings(
        env,
        production=True,
        allowed_hosts=ALLOWED_HOSTS,
        csrf_trusted_origins=CSRF_ORIGINS,
    )


def test_resolver_disabled_default_selects_dummy_backend() -> None:
    resolved = resolve_production({})

    assert resolved.enabled is False
    assert resolved.email_backend == DISABLED_EMAIL_BACKEND
    assert resolved.public_base_url is None


def test_resolver_disabled_ignores_configured_transport_values() -> None:
    resolved = resolve_production(
        enabled_env(
            SLAIF_ACCOUNT_EMAIL_ENABLED="false",
            SLAIF_SMTP_PORT="0",
            SLAIF_SMTP_USE_SSL="true",
            SLAIF_SMTP_STARTTLS="true",
        )
    )

    assert resolved.enabled is False
    assert resolved.email_backend == DISABLED_EMAIL_BACKEND


def test_resolver_enabled_production_maps_django_smtp_settings() -> None:
    resolved = resolve_production(enabled_env())

    assert resolved.enabled is True
    assert resolved.email_backend == SMTP_EMAIL_BACKEND
    assert resolved.public_base_url == TEST_BASE_URL
    assert resolved.host == TEST_SMTP_HOST
    assert resolved.port == 587
    assert resolved.host_user == TEST_SMTP_USERNAME
    assert resolved.host_password == TEST_SMTP_PASSWORD
    assert resolved.default_from_email == TEST_SMTP_FROM
    assert resolved.use_ssl is False
    assert resolved.use_tls is True
    assert resolved.timeout == 30


def test_resolver_enabled_without_credentials_is_pair_consistent() -> None:
    resolved = resolve_production(enabled_env(SLAIF_SMTP_USERNAME="", SLAIF_SMTP_PASSWORD=""))

    assert resolved.enabled is True
    assert resolved.host_user is None
    assert resolved.host_password is None


def test_resolver_local_permits_plaintext_synthetic_sink() -> None:
    resolved = resolve_account_email_settings(
        enabled_env(
            SLAIF_PUBLIC_BASE_URL="https://localhost:8443",
            SLAIF_SMTP_USE_SSL="false",
            SLAIF_SMTP_STARTTLS="false",
        ),
        production=False,
    )

    assert resolved.enabled is True
    assert resolved.use_ssl is False
    assert resolved.use_tls is False
    assert resolved.public_base_url == "https://localhost:8443"


def test_resolver_local_still_rejects_ambiguous_tls_modes() -> None:
    with pytest.raises(ImproperlyConfigured):
        resolve_account_email_settings(
            enabled_env(SLAIF_SMTP_USE_SSL="true", SLAIF_SMTP_STARTTLS="true"),
            production=False,
        )


# --- secret representation canaries (057-b) -------------------------------


def _settings_with_secret(password: str) -> AccountEmailSettings:
    return AccountEmailSettings(
        enabled=True,
        public_base_url=TEST_BASE_URL,
        email_backend=SMTP_EMAIL_BACKEND,
        host=TEST_SMTP_HOST,
        port=587,
        host_user=TEST_SMTP_USERNAME,
        host_password=password,
        default_from_email=TEST_SMTP_FROM,
        use_ssl=False,
        use_tls=True,
        timeout=30,
    )


def test_account_email_settings_repr_and_str_exclude_smtp_secret() -> None:
    settings_ = _settings_with_secret(TEST_SMTP_PASSWORD)

    rendered = f"{repr(settings_)} {str(settings_)}"
    assert TEST_SMTP_PASSWORD not in rendered
    # A failed assertion on this object must not echo the secret either.
    with pytest.raises(AssertionError) as excinfo:
        assert settings_.port == 25, f"unexpected settings: {settings_!r}"
    assert TEST_SMTP_PASSWORD not in str(excinfo.value)


def test_account_email_settings_keeps_secret_attribute_accessible() -> None:
    settings_ = _settings_with_secret(TEST_SMTP_PASSWORD)

    # Django's SMTP backend mapping still receives the real value.
    assert settings_.host_password == TEST_SMTP_PASSWORD
    # Equality must not be driven by the excluded field.
    other = _settings_with_secret("another-synthetic-secret")
    assert settings_ == other


FAILING_PRODUCTION_CASES: list[tuple[str, dict[str, str], str]] = [
    ("missing-host", {"SLAIF_SMTP_HOST": ""}, "SLAIF_SMTP_HOST is required"),
    (
        "missing-from",
        {"SLAIF_SMTP_FROM": ""},
        "SLAIF_SMTP_FROM is required",
    ),
    (
        "from-malformed",
        {"SLAIF_SMTP_FROM": "bad-address"},
        "SLAIF_SMTP_FROM must be a valid bare email address",
    ),
    (
        "from-surrounding-whitespace",
        {"SLAIF_SMTP_FROM": " no-reply@example.test"},
        "SLAIF_SMTP_FROM must be a valid bare email address",
    ),
    (
        "from-header-injection",
        {"SLAIF_SMTP_FROM": "no-reply@example.test\r\nBCC: other@example.test"},
        "SLAIF_SMTP_FROM must be a valid bare email address",
    ),
    ("missing-port", {"SLAIF_SMTP_PORT": ""}, "SLAIF_SMTP_PORT is required"),
    (
        "missing-base-url",
        {"SLAIF_PUBLIC_BASE_URL": ""},
        "SLAIF_PUBLIC_BASE_URL is required",
    ),
    (
        "non-https-base-url",
        {"SLAIF_PUBLIC_BASE_URL": "http://reservation.example.test"},
        "SLAIF_PUBLIC_BASE_URL must be an https origin",
    ),
    (
        "base-url-path",
        {"SLAIF_PUBLIC_BASE_URL": "https://reservation.example.test/onboarding"},
        "must be a bare origin",
    ),
    (
        "base-url-userinfo",
        {"SLAIF_PUBLIC_BASE_URL": "https://user@reservation.example.test"},
        "must not include userinfo",
    ),
    (
        "base-url-empty-userinfo",
        {"SLAIF_PUBLIC_BASE_URL": "https://@reservation.example.test"},
        "must not include userinfo",
    ),
    (
        "base-url-surrounding-whitespace",
        {"SLAIF_PUBLIC_BASE_URL": " https://reservation.example.test"},
        "SLAIF_PUBLIC_BASE_URL must not include whitespace",
    ),
    (
        "base-url-trailing-whitespace",
        {"SLAIF_PUBLIC_BASE_URL": "https://reservation.example.test "},
        "SLAIF_PUBLIC_BASE_URL must not include whitespace",
    ),
    (
        "base-url-host-not-allowed",
        {"SLAIF_PUBLIC_BASE_URL": "https://other.example.test"},
        "must be listed in SLAIF_ALLOWED_HOSTS",
    ),
    (
        "base-url-origin-not-csrf-trusted",
        {"SLAIF_PUBLIC_BASE_URL": "https://reservation.example.test:8443"},
        "SLAIF_CSRF_TRUSTED_ORIGINS",
    ),
    (
        "port-zero",
        {"SLAIF_SMTP_PORT": "0"},
        "must be an integer from 1 through 65535",
    ),
    (
        "port-above-range",
        {"SLAIF_SMTP_PORT": "65536"},
        "must be an integer from 1 through 65535",
    ),
    (
        "port-not-integer",
        {"SLAIF_SMTP_PORT": "abc"},
        "must be an integer from 1 through 65535",
    ),
    (
        "timeout-zero",
        {"SLAIF_SMTP_TIMEOUT_SECONDS": "0"},
        "must be an integer from 1 through 60",
    ),
    (
        "timeout-above-range",
        {"SLAIF_SMTP_TIMEOUT_SECONDS": "61"},
        "must be an integer from 1 through 60",
    ),
    (
        "timeout-not-integer",
        {"SLAIF_SMTP_TIMEOUT_SECONDS": "soon"},
        "must be an integer from 1 through 60",
    ),
    (
        "username-without-password",
        {"SLAIF_SMTP_USERNAME": TEST_SMTP_USERNAME, "SLAIF_SMTP_PASSWORD": ""},
        "must be set together",
    ),
    (
        "password-without-username",
        {"SLAIF_SMTP_USERNAME": "", "SLAIF_SMTP_PASSWORD": TEST_SMTP_PASSWORD},
        "must be set together",
    ),
    (
        "both-tls-modes",
        {"SLAIF_SMTP_USE_SSL": "true", "SLAIF_SMTP_STARTTLS": "true"},
        "mutually exclusive",
    ),
    (
        "neither-tls-mode",
        {"SLAIF_SMTP_USE_SSL": "false", "SLAIF_SMTP_STARTTLS": "false"},
        "required for production account email",
    ),
    (
        "host-with-port",
        {"SLAIF_SMTP_HOST": "smtp.example.test:25"},
        "SLAIF_SMTP_HOST must be a valid bare host",
    ),
    (
        "ambiguous-enabled-flag",
        {"SLAIF_ACCOUNT_EMAIL_ENABLED": "sometimes"},
        "SLAIF_ACCOUNT_EMAIL_ENABLED must be a boolean value",
    ),
]


@pytest.mark.parametrize(
    "case", FAILING_PRODUCTION_CASES, ids=[case[0] for case in FAILING_PRODUCTION_CASES]
)
def test_resolver_production_matrix_fails_closed(case: tuple[str, dict[str, str], str]) -> None:
    _name, mutation, needle = case

    with pytest.raises(ImproperlyConfigured) as excinfo:
        resolve_production(enabled_env(**mutation))

    message = str(excinfo.value)
    assert needle in message
    # Category-only: raw transport values and credentials are never echoed.
    assert TEST_SMTP_PASSWORD not in message
    assert TEST_SMTP_USERNAME not in message
    assert TEST_SMTP_FROM not in message


# --- production settings load (real settings module in a subprocess) ------

TEST_PRODUCTION_SECRET_KEY = "valid-production-secret-key-for-tests-32-bytes"
TEST_PRODUCTION_API_TOKEN_PEPPER = "valid-production-test-api-token-pepper-32-bytes"

SETTINGS_REPORT_CODE = (
    "import django, json\n"
    "django.setup()\n"
    "from django.conf import settings\n"
    "print(json.dumps({\n"
    '    "ACCOUNT_EMAIL_ENABLED": settings.ACCOUNT_EMAIL_ENABLED,\n'
    '    "PUBLIC_BASE_URL": settings.PUBLIC_BASE_URL,\n'
    '    "EMAIL_BACKEND": settings.EMAIL_BACKEND,\n'
    '    "EMAIL_HOST": settings.EMAIL_HOST,\n'
    '    "EMAIL_PORT": settings.EMAIL_PORT,\n'
    '    "EMAIL_HOST_USER": settings.EMAIL_HOST_USER,\n'
    '    "EMAIL_HOST_PASSWORD_SET": bool(settings.EMAIL_HOST_PASSWORD),\n'
    '    "DEFAULT_FROM_EMAIL": settings.DEFAULT_FROM_EMAIL,\n'
    '    "EMAIL_USE_SSL": settings.EMAIL_USE_SSL,\n'
    '    "EMAIL_USE_TLS": settings.EMAIL_USE_TLS,\n'
    '    "EMAIL_TIMEOUT": settings.EMAIL_TIMEOUT,\n'
    "}))\n"
)


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


def run_settings_report(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", SETTINGS_REPORT_CODE],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_production_settings_disabled_email_preserves_startup_and_dummy_backend() -> None:
    result = run_settings_report(production_settings_env())

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["ACCOUNT_EMAIL_ENABLED"] is False
    assert report["PUBLIC_BASE_URL"] is None
    assert report["EMAIL_BACKEND"] == DISABLED_EMAIL_BACKEND
    assert report["EMAIL_HOST_PASSWORD_SET"] is False


def test_production_settings_disabled_ignores_configured_smtp_junk() -> None:
    env = production_settings_env()
    env.update(enabled_env(SLAIF_ACCOUNT_EMAIL_ENABLED="false", SLAIF_SMTP_PORT="0"))
    env["SLAIF_SMTP_USE_SSL"] = "true"
    env["SLAIF_SMTP_STARTTLS"] = "true"

    result = run_settings_report(env)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["ACCOUNT_EMAIL_ENABLED"] is False
    assert report["EMAIL_BACKEND"] == DISABLED_EMAIL_BACKEND


def test_production_settings_enabled_valid_maps_smtp_backend() -> None:
    env = production_settings_env()
    env.update(enabled_env())

    result = run_settings_report(env)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["ACCOUNT_EMAIL_ENABLED"] is True
    assert report["PUBLIC_BASE_URL"] == TEST_BASE_URL
    assert report["EMAIL_BACKEND"] == SMTP_EMAIL_BACKEND
    assert report["EMAIL_HOST"] == TEST_SMTP_HOST
    assert report["EMAIL_PORT"] == 587
    assert report["EMAIL_HOST_USER"] == TEST_SMTP_USERNAME
    assert report["EMAIL_HOST_PASSWORD_SET"] is True
    assert report["DEFAULT_FROM_EMAIL"] == TEST_SMTP_FROM
    assert report["EMAIL_USE_SSL"] is False
    assert report["EMAIL_USE_TLS"] is True
    assert report["EMAIL_TIMEOUT"] == 30


@pytest.mark.parametrize(
    "case", FAILING_PRODUCTION_CASES, ids=[case[0] for case in FAILING_PRODUCTION_CASES]
)
def test_production_settings_enabled_matrix_fails_closed(
    case: tuple[str, dict[str, str], str],
) -> None:
    _name, mutation, needle = case
    env = production_settings_env()
    env.update(enabled_env(**mutation))

    result = run_django_setup(env)

    assert result.returncode != 0
    assert needle in result.stderr
    # Fail-closed output never leaks raw transport values or credentials.
    assert TEST_SMTP_PASSWORD not in result.stderr
    assert TEST_SMTP_PASSWORD not in result.stdout
    assert TEST_SMTP_USERNAME not in result.stderr


# --- synthetic local SMTP transport mechanics ------------------------------

SYNTHETIC_FROM = "no-reply@example.invalid"
SYNTHETIC_TO = "onboarding-test@example.invalid"


class _FakeSmtpSink:
    """One-connection plaintext loopback SMTP sink (stdlib socket only)."""

    def __init__(self) -> None:
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(("127.0.0.1", 0))
        self._server.listen(1)
        self._server.settimeout(10)
        self.port = self._server.getsockname()[1]
        self.commands: list[str] = []
        self.data: list[str] = []
        self.connections = 0
        self._thread: threading.Thread | None = None

    def __enter__(self) -> _FakeSmtpSink:
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self._server.close()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _send_line(self, conn: socket.socket, line: str) -> None:
        conn.sendall((line + "\r\n").encode("ascii"))

    def _read_line(self, conn: socket.socket) -> str | None:
        buffer = bytearray()
        while not buffer.endswith(b"\r\n"):
            chunk = conn.recv(1)
            if not chunk:
                return None
            buffer.extend(chunk)
        return buffer.decode("ascii", errors="replace").strip()

    def _serve(self) -> None:
        try:
            conn, _ = self._server.accept()
        except OSError:
            return
        self.connections += 1
        with conn:
            conn.settimeout(10)
            self._send_line(conn, "220 synthetic.local ESMTP 057a sink")
            in_data = False
            while True:
                line = self._read_line(conn)
                if line is None:
                    return
                if in_data:
                    if line == ".":
                        in_data = False
                        self._send_line(conn, "250 2.0.0 Ok: synthetic queued")
                    else:
                        self.data.append(line)
                    continue
                self.commands.append(line)
                verb = line.split(" ", 1)[0].upper()
                if verb in {"EHLO", "HELO"}:
                    self._send_line(conn, "250-synthetic.local")
                    self._send_line(conn, "250 8BITMIME")
                elif verb == "MAIL":
                    self._send_line(conn, "250 2.1.0 Ok")
                elif verb == "RCPT":
                    self._send_line(conn, "250 2.1.5 Ok")
                elif verb == "DATA":
                    self._send_line(conn, "354 End data with <CR><LF>.<CR><LF>")
                    in_data = True
                elif verb == "QUIT":
                    self._send_line(conn, "221 2.0.0 Bye")
                    return
                else:
                    self._send_line(conn, "250 2.0.0 Ok")


def _send_simple_message() -> int:
    return mail.send_mail(
        subject="Synthetic account email transport check",
        message="One simple message to a synthetic local SMTP sink.",
        from_email=SYNTHETIC_FROM,
        recipient_list=[SYNTHETIC_TO],
    )


def test_synthetic_sink_receives_one_simple_message_via_django_smtp_backend() -> None:
    with _FakeSmtpSink() as sink:
        with override_settings(
            EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
            EMAIL_HOST="127.0.0.1",
            EMAIL_PORT=sink.port,
            EMAIL_HOST_USER="",
            EMAIL_HOST_PASSWORD="",
            EMAIL_USE_SSL=False,
            EMAIL_USE_TLS=False,
            EMAIL_TIMEOUT=5,
            DEFAULT_FROM_EMAIL=SYNTHETIC_FROM,
        ):
            assert _send_simple_message() == 1

        assert sink.connections == 1
        commands = [command.lower() for command in sink.commands]
        assert f"mail from:<{SYNTHETIC_FROM}>" in commands
        assert f"rcpt to:<{SYNTHETIC_TO}>" in commands
        assert "data" in commands
        body = "\n".join(sink.data)
        assert "Synthetic account email transport check" in body
        assert "One simple message to a synthetic local SMTP sink." in body
        # The sink saw only the single synthetic recipient, never a real one.
        recipients = [
            command.lower() for command in sink.commands if command.lower().startswith("rcpt")
        ]
        assert recipients == [f"rcpt to:<{SYNTHETIC_TO}>"]


def test_disabled_configuration_sends_nothing_to_sink() -> None:
    with _FakeSmtpSink() as sink:
        with override_settings(
            EMAIL_BACKEND="django.core.mail.backends.dummy.EmailBackend",
            DEFAULT_FROM_EMAIL=SYNTHETIC_FROM,
        ):
            assert _send_simple_message() == 1

        assert sink.connections == 0
