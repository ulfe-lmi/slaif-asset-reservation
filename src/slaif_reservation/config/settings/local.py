"""Safe local development settings."""

from __future__ import annotations

import os

from slaif_reservation.config.email import resolve_account_email_settings
from slaif_reservation.config.env import env_bool, env_int_range, env_list
from slaif_reservation.config.settings.base import *  # noqa: F403
from slaif_reservation.config.settings.base import apply_database_url

SECRET_KEY = os.environ.get("SLAIF_DJANGO_SECRET_KEY", SECRET_KEY)  # noqa: F405
DEBUG = env_bool("SLAIF_DEBUG", default=True)
ALLOWED_HOSTS = env_list(
    "SLAIF_ALLOWED_HOSTS",
    default=("localhost", "127.0.0.1", "0.0.0.0"),
)  # noqa: S104
CSRF_TRUSTED_ORIGINS = env_list(
    "SLAIF_CSRF_TRUSTED_ORIGINS",
    default=("http://localhost:8000", "http://127.0.0.1:8000"),
)
API_DOCS_ENABLED = env_bool("SLAIF_ENABLE_API_DOCS", default=True)
API_DOCS_PUBLIC = env_bool("SLAIF_PUBLIC_API_DOCS", default=True)
API_TOKEN_PEPPER = os.environ.get("SLAIF_API_TOKEN_PEPPER", API_TOKEN_PEPPER)  # noqa: F405
API_TOKEN_MAX_LIFETIME_DAYS = env_int_range(
    "SLAIF_API_TOKEN_MAX_LIFETIME_DAYS",
    default=90,
    minimum=1,
    maximum=365,
)

# Account email transport (SAR-055): opt-in, disabled by default. Local
# development may point at a synthetic loopback SMTP sink without TLS;
# no real relay or recipient is configured by default.
_account_email = resolve_account_email_settings(
    production=False,
    allowed_hosts=ALLOWED_HOSTS,
    csrf_trusted_origins=CSRF_TRUSTED_ORIGINS,
)
ACCOUNT_EMAIL_ENABLED = _account_email.enabled
PUBLIC_BASE_URL = _account_email.public_base_url
EMAIL_BACKEND = _account_email.email_backend
if _account_email.enabled:
    EMAIL_HOST = _account_email.host
    EMAIL_PORT = _account_email.port
    EMAIL_HOST_USER = _account_email.host_user
    EMAIL_HOST_PASSWORD = _account_email.host_password
    DEFAULT_FROM_EMAIL = _account_email.default_from_email
    EMAIL_USE_SSL = _account_email.use_ssl
    EMAIL_USE_TLS = _account_email.use_tls
    EMAIL_TIMEOUT = _account_email.timeout

if database_url := os.environ.get("DATABASE_URL"):
    apply_database_url(database_url)
