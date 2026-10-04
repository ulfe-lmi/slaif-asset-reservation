"""Production-shaped settings that fail closed when required configuration is absent."""

from __future__ import annotations

from django.core.exceptions import ImproperlyConfigured

from slaif_reservation.accounts.tokens import validate_api_token_pepper
from slaif_reservation.config.env import (
    env_bool,
    env_int_range,
    env_list,
    env_non_negative_int,
    env_required,
    env_trusted_proxy_peers,
    validate_allowed_host_entry,
    validate_csrf_origin,
    validate_production_secret_key,
)
from slaif_reservation.config.settings.base import *  # noqa: F403
from slaif_reservation.config.settings.base import apply_database_url

SECRET_KEY = env_required("SLAIF_DJANGO_SECRET_KEY")
validate_production_secret_key(SECRET_KEY)
DEBUG = env_bool("SLAIF_DEBUG", default=False)
if DEBUG:
    msg = "SLAIF_DEBUG must not be enabled in production settings"
    raise ImproperlyConfigured(msg)

ALLOWED_HOSTS = env_list("SLAIF_ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    msg = "SLAIF_ALLOWED_HOSTS is required in production settings"
    raise ImproperlyConfigured(msg)
if "*" in ALLOWED_HOSTS:
    msg = "SLAIF_ALLOWED_HOSTS must list explicit hosts; the wildcard '*' is unsafe"
    raise ImproperlyConfigured(msg)
# Each configured host must be an explicit bare host (hostname, IP literal,
# or Django dotted subdomain wildcard); scheme, port, userinfo and malformed
# entries fail closed without echoing the raw value.
ALLOWED_HOSTS = [validate_allowed_host_entry(entry) for entry in ALLOWED_HOSTS]

CSRF_TRUSTED_ORIGINS = [
    validate_csrf_origin(origin) for origin in env_list("SLAIF_CSRF_TRUSTED_ORIGINS")
]
if not CSRF_TRUSTED_ORIGINS:
    msg = "SLAIF_CSRF_TRUSTED_ORIGINS is required in production settings"
    raise ImproperlyConfigured(msg)

apply_database_url(env_required("DATABASE_URL"))

SECURE_SSL_REDIRECT = env_bool("SLAIF_SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
if SECURE_SSL_REDIRECT:
    # With the redirect on, every legitimate origin is https; an http origin
    # can never work and would only mask a misconfigured deployment.
    if any(origin.startswith("http://") for origin in CSRF_TRUSTED_ORIGINS):
        msg = (
            "SLAIF_CSRF_TRUSTED_ORIGINS must be https origins while "
            "SLAIF_SECURE_SSL_REDIRECT is enabled"
        )
        raise ImproperlyConfigured(msg)

SECURE_HSTS_SECONDS = env_non_negative_int("SLAIF_SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    "SLAIF_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=False,
)
SECURE_HSTS_PRELOAD = env_bool("SLAIF_SECURE_HSTS_PRELOAD", default=False)
# The supported explicit HTTPS contract: HSTS is only meaningful with the
# SSL redirect on (every legitimate origin is https and plain-transport
# requests are bounced), and the subdomain/preload flags are only meaningful
# with a non-zero max-age. Out-of-contract combinations fail closed.
if SECURE_HSTS_SECONDS > 0 and not SECURE_SSL_REDIRECT:
    msg = "SLAIF_SECURE_HSTS_SECONDS is only supported while SLAIF_SECURE_SSL_REDIRECT is enabled"
    raise ImproperlyConfigured(msg)
if (SECURE_HSTS_INCLUDE_SUBDOMAINS or SECURE_HSTS_PRELOAD) and SECURE_HSTS_SECONDS == 0:
    msg = (
        "SLAIF_SECURE_HSTS_INCLUDE_SUBDOMAINS/SLAIF_SECURE_HSTS_PRELOAD require "
        "a non-zero SLAIF_SECURE_HSTS_SECONDS"
    )
    raise ImproperlyConfigured(msg)

# TLS/client-identity forwarding is gated on an explicit, strictly validated
# peer list by TrustedProxyForwardingMiddleware (see middleware.py). The
# blanket SECURE_PROXY_SSL_HEADER trust is deliberately not used: only the
# configured proxy peers may supply forwarding.
TRUSTED_PROXY_PEERS = env_trusted_proxy_peers("SLAIF_TRUSTED_PROXY_PEERS")

SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

API_DOCS_ENABLED = env_bool("SLAIF_ENABLE_API_DOCS", default=False)
API_DOCS_PUBLIC = False

API_TOKEN_PEPPER = env_required("SLAIF_API_TOKEN_PEPPER")
try:
    validate_api_token_pepper(API_TOKEN_PEPPER, secret_key=SECRET_KEY)
except Exception as exc:
    msg = "SLAIF_API_TOKEN_PEPPER is invalid for production settings"
    raise ImproperlyConfigured(msg) from exc
API_TOKEN_MAX_LIFETIME_DAYS = env_int_range(
    "SLAIF_API_TOKEN_MAX_LIFETIME_DAYS",
    default=90,
    minimum=1,
    maximum=365,
)

MIDDLEWARE = [
    "slaif_reservation.config.middleware.TrustedProxyForwardingMiddleware",
    *MIDDLEWARE,  # noqa: F405
    "slaif_reservation.config.middleware.SafeRequestLogMiddleware",
]
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "safe_django_response": {
            "()": "slaif_reservation.config.logging.SafeDjangoResponseLogFilter",
        },
    },
    "formatters": {
        "json": {
            "()": "slaif_reservation.config.logging.JsonLogFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["safe_django_response"],
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.server": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "slaif_reservation": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
