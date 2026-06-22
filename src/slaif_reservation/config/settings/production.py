"""Production-shaped settings that fail closed when required configuration is absent."""

from __future__ import annotations

from django.core.exceptions import ImproperlyConfigured

from slaif_reservation.config.env import env_bool, env_list, env_non_negative_int, env_required
from slaif_reservation.config.settings.base import *  # noqa: F403
from slaif_reservation.config.settings.base import apply_database_url

SECRET_KEY = env_required("SLAIF_DJANGO_SECRET_KEY")
DEBUG = env_bool("SLAIF_DEBUG", default=False)
if DEBUG:
    msg = "SLAIF_DEBUG must not be enabled in production settings"
    raise ImproperlyConfigured(msg)

ALLOWED_HOSTS = env_list("SLAIF_ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    msg = "SLAIF_ALLOWED_HOSTS is required in production settings"
    raise ImproperlyConfigured(msg)

CSRF_TRUSTED_ORIGINS = env_list("SLAIF_CSRF_TRUSTED_ORIGINS")
if not CSRF_TRUSTED_ORIGINS:
    msg = "SLAIF_CSRF_TRUSTED_ORIGINS is required in production settings"
    raise ImproperlyConfigured(msg)

apply_database_url(env_required("DATABASE_URL"))

SECURE_SSL_REDIRECT = env_bool("SLAIF_SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env_non_negative_int("SLAIF_SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    "SLAIF_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=False,
)
SECURE_HSTS_PRELOAD = env_bool("SLAIF_SECURE_HSTS_PRELOAD", default=False)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

API_DOCS_ENABLED = env_bool("SLAIF_ENABLE_API_DOCS", default=False)
API_DOCS_PUBLIC = False
