"""Small environment parsing helpers for fail-closed settings."""

from __future__ import annotations

import os
from collections.abc import Mapping
from urllib.parse import parse_qsl, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

Env = Mapping[str, str]

TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
FALSE_VALUES = {"0", "false", "f", "no", "n", "off", ""}


def env_bool(name: str, *, default: bool, env: Env | None = None) -> bool:
    source = os.environ if env is None else env
    raw_value = source.get(name)
    if raw_value is None:
        return default

    value = raw_value.strip().lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    msg = f"{name} must be a boolean value"
    raise ImproperlyConfigured(msg)


def env_list(name: str, *, default: tuple[str, ...] = (), env: Env | None = None) -> list[str]:
    source = os.environ if env is None else env
    raw_value = source.get(name)
    if raw_value is None:
        return list(default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def env_required(name: str, *, env: Env | None = None) -> str:
    source = os.environ if env is None else env
    value = source.get(name)
    if value is None or value.strip() == "":
        msg = f"{name} is required"
        raise ImproperlyConfigured(msg)
    return value


def env_non_negative_int(name: str, *, default: int, env: Env | None = None) -> int:
    source = os.environ if env is None else env
    raw_value = source.get(name)
    if raw_value is None:
        return default

    try:
        value = int(raw_value.strip())
    except ValueError as exc:
        msg = f"{name} must be a non-negative integer"
        raise ImproperlyConfigured(msg) from exc

    if value < 0:
        msg = f"{name} must be a non-negative integer"
        raise ImproperlyConfigured(msg)
    return value


def postgres_database_from_url(url: str) -> dict[str, str | int | dict[str, str]]:
    parsed = urlparse(url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        msg = "DATABASE_URL must use the postgres or postgresql scheme"
        raise ImproperlyConfigured(msg)
    if not parsed.hostname or not parsed.path.strip("/"):
        msg = "DATABASE_URL must include host and database name"
        raise ImproperlyConfigured(msg)

    config: dict[str, str | int | dict[str, str]] = {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": parsed.hostname,
        "NAME": unquote(parsed.path.strip("/")),
    }
    if parsed.username:
        config["USER"] = unquote(parsed.username)
    if parsed.password:
        config["PASSWORD"] = unquote(parsed.password)
    if parsed.port:
        config["PORT"] = parsed.port

    options = {key: value for key, value in parse_qsl(parsed.query)}
    if options:
        config["OPTIONS"] = options

    return config
