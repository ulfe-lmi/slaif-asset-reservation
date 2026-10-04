"""Operational middleware."""

from __future__ import annotations

import ipaddress
import logging
import time
import uuid
from collections.abc import Callable
from typing import cast

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from slaif_reservation.config.env import PeerNetwork, peer_in_trusted_networks

logger = logging.getLogger("slaif_reservation.request")
proxy_logger = logging.getLogger("slaif_reservation.proxy")

# Environ keys carrying forwarding semantics. Gunicorn maps wire header names
# to HTTP_* keys with underscores (hyphen and underscore wire spellings that
# survive its parser collapse onto the same keys), so this list covers the
# standard and variant spellings the application layer could otherwise see.
FORWARDING_ENV_KEYS = (
    "HTTP_FORWARDED",
    "HTTP_X_FORWARDED_FOR",
    "HTTP_X_FORWARDED_HOST",
    "HTTP_X_FORWARDED_PREFIX",
    "HTTP_X_FORWARDED_PROTOCOL",
    "HTTP_X_FORWARDED_PROTO",
    "HTTP_X_FORWARDED_SSL",
)

UNMATCHED_ROUTE = "unmatched-route"


class TrustedProxyForwardingMiddleware:
    """Gate TLS/client-identity forwarding on an explicit trusted peer list.

    The supported Internet target is one operator-owned TLS proxy (Caddy) in
    front of a private loopback Gunicorn. Only the explicitly configured
    proxy peers may supply forwarding; every other peer is treated as a
    direct client:

    - untrusted peers: all forwarding headers are stripped from the WSGI
      environment, the scheme is pinned to the real plain-HTTP transport to
      Gunicorn, and the peer address is the client identity. A
      server-derived ``wsgi.url_scheme`` of ``https`` (for example from
      Gunicorn's own secure-scheme handling) can therefore never bypass the
      configured trust list;
    - trusted peers: ``X-Forwarded-Proto`` is honored only when it is
      exactly ``http`` or ``https``; ``X-Forwarded-For`` is honored only as a
      single valid IP (the one-hop value the supported proxy overwrites from
      the real client address). Ambiguous chains or values fall back to the
      peer address with a safe category-only warning;
    - other forwarding headers (``Forwarded``, ``X-Forwarded-Host``, ``X-Forwarded-Prefix`` and the
      ``X-Forwarded-Protocol``/``X-Forwarded-Ssl`` scheme variants) are never
      used for trust decisions and are stripped.

    The normalized one-hop client identity is exposed as
    ``request.client_ip`` and written back to ``REMOTE_ADDR`` so downstream
    code sees a single canonical value; it is the intended source for the
    next limiter objective, not another raw header interpretation.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self.trusted_networks: list[PeerNetwork] = list(
            getattr(settings, "TRUSTED_PROXY_PEERS", []) or []
        )

    def __call__(self, request: HttpRequest) -> HttpResponse:
        environ = cast("dict[str, str]", request.META)
        peer = environ.get("REMOTE_ADDR") or ""
        if peer_in_trusted_networks(peer, self.trusted_networks):
            client_ip, xff_ambiguous = self._one_hop_client_ip(
                peer, environ.get("HTTP_X_FORWARDED_FOR")
            )
            scheme, xfp_ambiguous = self._trusted_scheme(environ.get("HTTP_X_FORWARDED_PROTO"))
            if xff_ambiguous:
                proxy_logger.warning(
                    "ambiguous forwarded-for from trusted proxy; falling back to peer address",
                    extra={"category": "proxy-ambiguity", "kind": "forwarded-for"},
                )
            if xfp_ambiguous:
                proxy_logger.warning(
                    "ambiguous forwarded-proto from trusted proxy; falling back to plain transport",
                    extra={"category": "proxy-ambiguity", "kind": "forwarded-proto"},
                )
            environ["wsgi.url_scheme"] = scheme
            environ["REMOTE_ADDR"] = client_ip
            request.client_ip = client_ip  # type: ignore[attr-defined]
        else:
            for key in FORWARDING_ENV_KEYS:
                environ.pop(key, None)
            # The plain-HTTP transport to Gunicorn is the only scheme an
            # untrusted peer can establish; a server-derived https scheme
            # must not bypass the trust list.
            environ["wsgi.url_scheme"] = "http"
            request.client_ip = peer  # type: ignore[attr-defined]
        return self.get_response(request)

    @staticmethod
    def _one_hop_client_ip(peer: str, raw_xff: str | None) -> tuple[str, bool]:
        if raw_xff is None:
            return peer, False
        entries = [entry.strip() for entry in raw_xff.split(",")]
        if len(entries) != 1 or not entries[0]:
            return peer, True
        try:
            return str(ipaddress.ip_address(entries[0])), False
        except ValueError:
            return peer, True

    @staticmethod
    def _trusted_scheme(raw_xfp: str | None) -> tuple[str, bool]:
        if raw_xfp is None:
            return "http", False
        value = raw_xfp.strip().lower()
        if value in {"http", "https"}:
            return value, False
        return "http", True


class SafeRequestLogMiddleware:
    """Emit one safe structured request log line without headers or bodies.

    The logged path is the resolved route template when URL resolution
    matched, and a fixed unmatched marker otherwise: raw request paths
    (which may be hostile or private) are never retained.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        started = time.perf_counter()
        response = self.get_response(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": _safe_route(request),
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "request_id": _safe_request_id(request.headers.get("X-Request-ID")),
            },
        )
        return response


def _safe_route(request: HttpRequest) -> str:
    resolver_match = getattr(request, "resolver_match", None)
    if resolver_match is not None:
        route = getattr(resolver_match, "route", None)
        if route:
            return str(route)
    return UNMATCHED_ROUTE


def _safe_request_id(raw_value: str | None) -> str:
    if not raw_value:
        return ""
    try:
        return str(uuid.UUID(raw_value))
    except ValueError:
        return ""
