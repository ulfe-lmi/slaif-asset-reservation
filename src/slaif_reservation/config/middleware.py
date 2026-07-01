"""Operational middleware."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("slaif_reservation.request")


class SafeRequestLogMiddleware:
    """Emit one safe structured request log line without headers or bodies."""

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
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "request_id": _safe_request_id(request.headers.get("X-Request-ID")),
            },
        )
        return response


def _safe_request_id(raw_value: str | None) -> str:
    if not raw_value:
        return ""
    try:
        return str(uuid.UUID(raw_value))
    except ValueError:
        return ""
