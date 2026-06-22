"""Test settings. PostgreSQL remains the expected database."""

from __future__ import annotations

import os

from slaif_reservation.config.settings.base import *  # noqa: F403
from slaif_reservation.config.settings.base import apply_database_url

SECRET_KEY = "test-only-secret-key"
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
API_DOCS_ENABLED = True
API_DOCS_PUBLIC = True
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
WHITENOISE_AUTOREFRESH = True
STORAGES["staticfiles"] = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}  # noqa: F405

apply_database_url(
    os.environ.get("TEST_DATABASE_URL")
    or os.environ.get("DATABASE_URL")
    or "postgres://slaif:slaif@localhost:5432/slaif_reservation"
)
