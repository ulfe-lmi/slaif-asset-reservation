"""Base Django settings shared by all environments."""

from __future__ import annotations

from pathlib import Path

from slaif_reservation.config.env import env_bool, env_list, postgres_database_from_url

BASE_DIR = Path(__file__).resolve().parents[4]

SECRET_KEY = "unsafe-local-development-key"
DEBUG = False

ALLOWED_HOSTS: list[str] = []
CSRF_TRUSTED_ORIGINS: list[str] = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "slaif_reservation.accounts",
    "slaif_reservation.api",
    "slaif_reservation.web",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "slaif_reservation.config.urls"
WSGI_APPLICATION = "slaif_reservation.config.wsgi.application"
ASGI_APPLICATION = "slaif_reservation.config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": postgres_database_from_url("postgres://slaif:slaif@localhost:5432/slaif_reservation")
}

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Ljubljana"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

API_DOCS_ENABLED = False
API_DOCS_PUBLIC = False

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "SLAIF Asset Reservation API",
    "DESCRIPTION": "Pre-alpha API shell. Domain endpoints are intentionally deferred.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api/v1",
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}


def apply_database_url(database_url: str) -> None:
    DATABASES["default"] = postgres_database_from_url(database_url)


def configure_common_from_environment() -> None:
    global API_DOCS_ENABLED, API_DOCS_PUBLIC, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS

    ALLOWED_HOSTS = env_list("SLAIF_ALLOWED_HOSTS", default=tuple(ALLOWED_HOSTS))
    CSRF_TRUSTED_ORIGINS = env_list(
        "SLAIF_CSRF_TRUSTED_ORIGINS",
        default=tuple(CSRF_TRUSTED_ORIGINS),
    )
    API_DOCS_ENABLED = env_bool("SLAIF_ENABLE_API_DOCS", default=API_DOCS_ENABLED)
    API_DOCS_PUBLIC = env_bool("SLAIF_PUBLIC_API_DOCS", default=API_DOCS_PUBLIC)
