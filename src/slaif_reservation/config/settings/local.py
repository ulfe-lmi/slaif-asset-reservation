"""Safe local development settings."""

from __future__ import annotations

import os

from slaif_reservation.config.env import env_bool, env_list
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

if database_url := os.environ.get("DATABASE_URL"):
    apply_database_url(database_url)
