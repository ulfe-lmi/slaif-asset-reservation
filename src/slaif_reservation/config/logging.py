"""Structured logging helpers for production-shaped operation."""

from __future__ import annotations

import json
import logging
import math
import os
import re
import traceback
from datetime import UTC, datetime
from typing import Any

from django.conf import settings

REDACTED = "[redacted]"
TOKEN_VALUE_RE = re.compile(r"sar_[0-9a-fA-F]{32}_[A-Za-z0-9_-]{32,128}")
AUTHORIZATION_RE = re.compile(r"(?i)(authorization\s*[:=]\s*)(bearer|basic)\s+[^\s,;]+")

FORBIDDEN_FIELD_NAMES = frozenset(
    {
        "authorization",
        "authorization_header",
        "cookie",
        "cookies",
        "csrf",
        "csrfmiddlewaretoken",
        "password",
        "raw_request_body",
        "request_body",
        "body",
        "bearer_token",
        "token_secret",
        "secret",
        "verifier",
        "pepper",
        "purpose",
        "cancellation_reason",
    }
)

LOG_RECORD_RESERVED = frozenset(
    logging.makeLogRecord({}).__dict__.keys()
    | {
        "asctime",
        "message",
    }
)


def _normalized_key(value: str) -> str:
    return value.lower().replace("-", "_").replace(" ", "_")


def redact_log_value(value: Any, *, field_name: str | None = None) -> Any:
    """Return a log-safe representation of ``value`` without known secret material."""

    if field_name is not None and _normalized_key(field_name) in FORBIDDEN_FIELD_NAMES:
        return REDACTED
    if isinstance(value, dict):
        return {
            str(key): redact_log_value(item, field_name=str(key)) for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_log_value(item) for item in value]
    if isinstance(value, tuple):
        return [redact_log_value(item) for item in value]
    if not isinstance(value, str):
        return value

    text = TOKEN_VALUE_RE.sub(REDACTED, value)
    text = AUTHORIZATION_RE.sub(r"\1" + REDACTED, text)
    for setting_name in ("API_TOKEN_PEPPER", "SECRET_KEY"):
        configured = getattr(settings, setting_name, "")
        if configured and isinstance(configured, str):
            text = text.replace(configured, REDACTED)
    return text


UNSERIALIZABLE = "[unserializable]"
TRUNCATED = "[truncated]"
CIRCULAR = "[circular]"
MAX_CONTAINER_DEPTH = 10
MAX_EXCEPTION_STACK_FRAMES = 12


class SafeDjangoResponseLogFilter(logging.Filter):
    """Remove client-controlled text from Django response log records.

    Django's ``log_response`` formats 4xx/5xx lines as
    ``"<reason>: <request.path>"`` and SuspiciousOperation lines as the raw
    exception string, which can carry a hostile Host header value,
    Content-Type value or file path. Those records carry the
    ``status_code`` and ``request`` extras, which is the signature this
    filter keys on: client-controlled arguments are replaced with a fixed
    marker, and for the ``django.security.*`` loggers the message itself is
    the exception string, so it is replaced too. The fixed reason
    templates, the exception class (already carried by the logger name) and
    the ``status_code``/``request`` extras are preserved; the JSON
    formatter renders ``request`` as ``[unserializable]``.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if "status_code" not in record.__dict__ or "request" not in record.__dict__:
            return True
        args = record.args
        if isinstance(args, (tuple, list)):
            record.args = tuple(REDACTED if isinstance(arg, str) else arg for arg in args)
        elif isinstance(args, dict):
            record.args = {
                key: (REDACTED if isinstance(value, str) else value) for key, value in args.items()
            }
        if record.name.startswith("django.security.") and isinstance(record.msg, str):
            record.msg = REDACTED
        return True


def _json_safe_value(
    value: Any,
    *,
    field_name: str | None = None,
    depth: int = 0,
    seen: frozenset[int] = frozenset(),
) -> Any:
    """Return a JSON-safe, redaction-preserving representation of ``value``.

    Field-name redaction matches :func:`redact_log_value`; strings are
    redacted through it. Scalars pass through. Containers are walked with a
    depth cap and cycle detection so a hostile or malformed record can
    neither crash the formatter nor leak through ``repr``/``str``: anything
    unrecognized becomes a fixed marker.
    """
    if field_name is not None and _normalized_key(field_name) in FORBIDDEN_FIELD_NAMES:
        return REDACTED
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        return redact_log_value(value, field_name=field_name)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else UNSERIALIZABLE
    if isinstance(value, (bytes, bytearray, memoryview)):
        return REDACTED
    if isinstance(value, dict):
        if depth >= MAX_CONTAINER_DEPTH:
            return TRUNCATED
        if id(value) in seen:
            return CIRCULAR
        seen = seen | {id(value)}
        return {
            str(key): _json_safe_value(item, field_name=str(key), depth=depth + 1, seen=seen)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        if depth >= MAX_CONTAINER_DEPTH:
            return TRUNCATED
        if id(value) in seen:
            return CIRCULAR
        seen = seen | {id(value)}
        return [
            _json_safe_value(item, field_name=field_name, depth=depth + 1, seen=seen)
            for item in value
        ]
    return UNSERIALIZABLE


class JsonLogFormatter(logging.Formatter):
    """Small JSON formatter that emits only safe, explicit operational fields."""

    def format(self, record: logging.LogRecord) -> str:
        try:
            message = _json_safe_value(record.getMessage())
        except Exception:
            message = UNSERIALIZABLE
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
        }
        for key, value in sorted(record.__dict__.items()):
            if key in LOG_RECORD_RESERVED or key.startswith("_"):
                continue
            payload[key] = _json_safe_value(value, field_name=key)
        if record.exc_info and record.exc_info[0] is not None:
            # Safe error category and stack metadata only: the exception
            # class name plus bounded file:line frames. The exception
            # message is arbitrary text that hostile input can flow into,
            # and traceback source lines can carry locals, so neither is
            # retained.
            payload["exception_type"] = type(record.exc_info[1]).__name__
            frames = traceback.extract_tb(record.exc_info[2])
            stack = [
                f"{os.path.basename(frame.filename)}:{frame.lineno}"
                for frame in frames
                if frame.filename
            ]
            if stack:
                payload["exception_stack"] = stack[-MAX_EXCEPTION_STACK_FRAMES:]
        try:
            return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        except (TypeError, ValueError):
            return json.dumps(
                {
                    "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": UNSERIALIZABLE,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
