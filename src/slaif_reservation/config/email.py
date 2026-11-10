"""Operator opt-in account email transport resolution (SAR-055).

This module only resolves validated Django email settings from the
SLAIF-prefixed operator environment values. It never opens an SMTP
connection, sends mail, or touches the account-creation path. While the
capability is disabled (the default) the resolved backend is the dummy
backend, so no send can reach a relay and installs without any
SLAIF_SMTP_* value start exactly as before.

The operator keys are SLAIF_ACCOUNT_EMAIL_ENABLED, SLAIF_PUBLIC_BASE_URL,
SLAIF_SMTP_HOST, SLAIF_SMTP_PORT, SLAIF_SMTP_USERNAME, SLAIF_SMTP_PASSWORD,
SLAIF_SMTP_FROM, SLAIF_SMTP_USE_SSL (implicit TLS), SLAIF_SMTP_STARTTLS
(explicit STARTTLS) and SLAIF_SMTP_TIMEOUT_SECONDS. Mapping to Django's
built-in SMTP backend: EMAIL_HOST / EMAIL_PORT / EMAIL_HOST_USER /
EMAIL_HOST_PASSWORD / DEFAULT_FROM_EMAIL / EMAIL_USE_SSL / EMAIL_USE_TLS /
EMAIL_TIMEOUT.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

from slaif_reservation.config.env import (
    Env,
    env_bool,
    env_int_range,
    validate_allowed_host_entry,
    validate_canonical_service_url,
)

DISABLED_EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"
SMTP_EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"


@dataclass(frozen=True)
class AccountEmailSettings:
    """Validated account email transport settings for one environment."""

    enabled: bool
    public_base_url: str | None
    email_backend: str
    host: str | None = None
    port: int | None = None
    host_user: str | None = None
    host_password: str | None = None
    default_from_email: str | None = None
    use_ssl: bool = False
    use_tls: bool = False
    timeout: int | None = None


def resolve_account_email_settings(
    env: Env | None = None,
    *,
    production: bool,
    allowed_hosts: Sequence[str] = (),
    csrf_trusted_origins: Sequence[str] = (),
) -> AccountEmailSettings:
    """Resolve the account email transport, failing closed on any defect.

    When ``production`` is true the base URL host must be listed in
    ``allowed_hosts`` and its origin in ``csrf_trusted_origins`` (both in
    their normalized settings form), exactly one TLS mode must be
    selected, and plaintext SMTP is never permitted. Local (non-production)
    resolution enforces the canonical URL and transport field rules but
    may use an unencrypted synthetic sink. Error messages are category-only
    and never echo raw values or credentials.
    """
    source = os.environ if env is None else env

    if not env_bool("SLAIF_ACCOUNT_EMAIL_ENABLED", default=False, env=source):
        return AccountEmailSettings(
            enabled=False,
            public_base_url=None,
            email_backend=DISABLED_EMAIL_BACKEND,
        )

    raw_base_url = (source.get("SLAIF_PUBLIC_BASE_URL") or "").strip()
    if not raw_base_url:
        msg = "SLAIF_PUBLIC_BASE_URL is required when account email is enabled"
        raise ImproperlyConfigured(msg)
    canonical_base_url = validate_canonical_service_url(raw_base_url)
    parsed_base = urlparse(canonical_base_url)

    if production:
        # Compare the configured origin (normalized, brackets kept for
        # IPv6) against the already-validated host and origin lists.
        origin_netloc = parsed_base.netloc
        if parsed_base.port is not None:
            origin_netloc = origin_netloc[: -(len(str(parsed_base.port)) + 1)]
        if origin_netloc not in allowed_hosts:
            msg = "SLAIF_PUBLIC_BASE_URL host must be listed in SLAIF_ALLOWED_HOSTS"
            raise ImproperlyConfigured(msg)
        if canonical_base_url not in csrf_trusted_origins:
            msg = "SLAIF_PUBLIC_BASE_URL origin must be listed in SLAIF_CSRF_TRUSTED_ORIGINS"
            raise ImproperlyConfigured(msg)

    raw_smtp_host = (source.get("SLAIF_SMTP_HOST") or "").strip()
    if not raw_smtp_host:
        msg = "SLAIF_SMTP_HOST is required when account email is enabled"
        raise ImproperlyConfigured(msg)
    try:
        smtp_host = validate_allowed_host_entry(raw_smtp_host)
    except ImproperlyConfigured:
        raise ImproperlyConfigured("SLAIF_SMTP_HOST must be a valid bare host") from None

    raw_port = source.get("SLAIF_SMTP_PORT")
    if raw_port is None or not raw_port.strip():
        msg = "SLAIF_SMTP_PORT is required when account email is enabled"
        raise ImproperlyConfigured(msg)
    smtp_port = env_int_range("SLAIF_SMTP_PORT", default=0, minimum=1, maximum=65535, env=source)

    raw_from = (source.get("SLAIF_SMTP_FROM") or "").strip()
    if not raw_from:
        msg = "SLAIF_SMTP_FROM is required when account email is enabled"
        raise ImproperlyConfigured(msg)

    host_user = source.get("SLAIF_SMTP_USERNAME")
    host_password = source.get("SLAIF_SMTP_PASSWORD")
    user_set = host_user is not None and bool(host_user.strip())
    password_set = host_password is not None and host_password != ""
    if user_set != password_set:
        msg = "SLAIF_SMTP_USERNAME and SLAIF_SMTP_PASSWORD must be set together"
        raise ImproperlyConfigured(msg)

    use_ssl = env_bool("SLAIF_SMTP_USE_SSL", default=False, env=source)
    use_tls = env_bool("SLAIF_SMTP_STARTTLS", default=False, env=source)
    if use_ssl and use_tls:
        msg = "SLAIF_SMTP_USE_SSL and SLAIF_SMTP_STARTTLS are mutually exclusive"
        raise ImproperlyConfigured(msg)
    if production and not (use_ssl or use_tls):
        msg = (
            "SLAIF_SMTP_USE_SSL or SLAIF_SMTP_STARTTLS is required for "
            "production account email; plaintext SMTP is not permitted"
        )
        raise ImproperlyConfigured(msg)

    timeout = env_int_range(
        "SLAIF_SMTP_TIMEOUT_SECONDS", default=30, minimum=1, maximum=60, env=source
    )

    return AccountEmailSettings(
        enabled=True,
        public_base_url=canonical_base_url,
        email_backend=SMTP_EMAIL_BACKEND,
        host=smtp_host,
        port=smtp_port,
        host_user=host_user if user_set else None,
        host_password=host_password if password_set else None,
        default_from_email=raw_from,
        use_ssl=use_ssl,
        use_tls=use_tls,
        timeout=timeout,
    )
