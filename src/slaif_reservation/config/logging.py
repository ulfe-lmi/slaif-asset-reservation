"""Structured logging helpers for production-shaped operation."""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

from django.conf import settings

REDACTED = "[redacted]"
TOKEN_VALUE_RE = re.compile(r"sar_[0-9a-fA-F]{32}_[A-Za-z0-9_-]{32,128}")
AUTHORIZATION_RE = re.compile(r"(?i)(authorization\\s*[:=]\\s*)(bearer|basic)\\s+[^\\s,;]+")

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
    text = AUTHORIZATION_RE.sub(r"\\1" + REDACTED, text)
    for setting_name in ("API_TOKEN_PEPPER", "SECRET_KEY"):
        configured = getattr(settings, setting_name, "")
        if configured and isinstance(configured, str):
            text = text.replace(configured, REDACTED)
    return text


class JsonLogFormatter(logging.Formatter):
    """Small JSON formatter that emits only safe, explicit operational fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_log_value(record.getMessage()),
        }
        for key, value in sorted(record.__dict__.items()):
            if key in LOG_RECORD_RESERVED or key.startswith("_"):
                continue
            payload[key] = redact_log_value(value, field_name=key)
        if record.exc_info:
            payload["exception"] = redact_log_value(self.formatException(record.exc_info))
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))
