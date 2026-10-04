"""Small environment parsing helpers for fail-closed settings."""

from __future__ import annotations

import ipaddress
import os
from collections.abc import Mapping
from urllib.parse import parse_qsl, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

Env = Mapping[str, str]

TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
FALSE_VALUES = {"0", "false", "f", "no", "n", "off", ""}
UNSAFE_SECRET_KEYS = frozenset(
    {
        "unsafe-local-development-key",
        "test-only-secret-key",
        "change-me-for-local-development-only",
        "local-compose-only-secret",
        "REPLACE_WITH_AT_LEAST_32_BYTES_FROM_A_PROTECTED_SECRET_STORE",
    }
)
SECRET_KEY_MIN_BYTES = 32


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


def validate_production_secret_key(value: str) -> None:
    if not value or not value.strip():
        msg = "SLAIF_DJANGO_SECRET_KEY is required"
        raise ImproperlyConfigured(msg)
    if len(value.encode("utf-8")) < SECRET_KEY_MIN_BYTES:
        msg = "SLAIF_DJANGO_SECRET_KEY is invalid for production settings"
        raise ImproperlyConfigured(msg)
    if value.strip() in UNSAFE_SECRET_KEYS:
        msg = "SLAIF_DJANGO_SECRET_KEY is invalid for production settings"
        raise ImproperlyConfigured(msg)


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


def env_int_range(
    name: str,
    *,
    default: int,
    minimum: int,
    maximum: int,
    env: Env | None = None,
) -> int:
    source = os.environ if env is None else env
    raw_value = source.get(name)
    if raw_value is None:
        return default

    try:
        value = int(raw_value.strip())
    except ValueError as exc:
        msg = f"{name} must be an integer from {minimum} through {maximum}"
        raise ImproperlyConfigured(msg) from exc

    if value < minimum or value > maximum:
        msg = f"{name} must be an integer from {minimum} through {maximum}"
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


MAX_TRUSTED_PROXY_NETWORK_SIZE_BITS = 1  # at most a /31 pair (IPv4) or /127 (IPv6)

PeerNetwork = ipaddress.IPv4Network | ipaddress.IPv6Network


def _max_prefix(network: PeerNetwork) -> int:
    if isinstance(network, ipaddress.IPv4Network):
        return 31
    return 127


def validate_trusted_proxy_entry(raw_value: str) -> PeerNetwork:
    """Parse one explicit trusted proxy peer entry (IP or tiny point-to-point net).

    The supported Internet target is a single operator-owned TLS proxy in front
    of a private loopback Gunicorn, so trusted peers must be explicit hosts or
    point-to-point pairs. Broad ranges (private LAN blocks, 0.0.0.0/0, ::/0)
    would let any host in the range impersonate the proxy.
    """
    try:
        network = ipaddress.ip_network(raw_value, strict=True)
    except ValueError as exc:
        msg = (
            "SLAIF_TRUSTED_PROXY_PEERS entries must be explicit IP addresses or "
            "point-to-point networks (/31 IPv4, /127 IPv6)"
        )
        raise ImproperlyConfigured(msg) from exc
    if network.prefixlen < _max_prefix(network):
        msg = (
            "SLAIF_TRUSTED_PROXY_PEERS entries must be explicit IP addresses or "
            "point-to-point networks (/31 IPv4, /127 IPv6)"
        )
        raise ImproperlyConfigured(msg)
    return network


def env_trusted_proxy_peers(name: str, *, env: Env | None = None) -> list[PeerNetwork]:
    """Parse and strictly validate the explicit trusted proxy peer list."""
    source = os.environ if env is None else env
    raw_value = source.get(name)
    if raw_value is None or not raw_value.strip():
        msg = f"{name} is required"
        raise ImproperlyConfigured(msg)
    networks: list[PeerNetwork] = []
    for item in raw_value.split(","):
        entry = item.strip()
        if not entry:
            continue
        networks.append(validate_trusted_proxy_entry(entry))
    if not networks:
        msg = f"{name} is required"
        raise ImproperlyConfigured(msg)
    return networks


def peer_in_trusted_networks(peer: str | None, networks: list[PeerNetwork]) -> bool:
    if not peer:
        return False
    try:
        address = ipaddress.ip_address(peer)
    except ValueError:
        return False
    return any(address in network for network in networks)


def validate_csrf_origin(origin: str) -> str:
    """Validate one explicit CSRF trusted origin (scheme://host[:port]).

    Raises ImproperlyConfigured for anything that is not a bare origin: no
    userinfo, path, query or fragment, and no credentials in the URL.
    """
    parsed = urlparse(origin)
    if parsed.scheme not in {"http", "https"}:
        msg = "SLAIF_CSRF_TRUSTED_ORIGINS entries must be http or https origins"
        raise ImproperlyConfigured(msg)
    if not parsed.hostname:
        msg = "SLAIF_CSRF_TRUSTED_ORIGINS entries must include a host"
        raise ImproperlyConfigured(msg)
    if parsed.username or parsed.password:
        msg = "SLAIF_CSRF_TRUSTED_ORIGINS entries must not include credentials"
        raise ImproperlyConfigured(msg)
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        msg = "SLAIF_CSRF_TRUSTED_ORIGINS entries must be bare origins"
        raise ImproperlyConfigured(msg)
    return origin
