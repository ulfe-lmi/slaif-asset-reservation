"""Safe Gunicorn logging support.

Gunicorn 23 records raw request content in its own loggers below the
application layer:

- the error log includes the raw request line, method, HTTP version or
  header line when a request fails to parse (for example
  ``Invalid HTTP request line: '...'``);
- the access log's default line includes the raw request target with its
  query string.

Neither is acceptable for the production boundary, where hostile clients
may supply arbitrary text at the parser. This module provides a drop-in
logger class (``--logger-class slaif_reservation.config.gunicorn.SlaifGunicornLogger``)
that replaces Gunicorn's formatters with safe JSON recorders: the error
log emits a category plus the peer address (never the offending text), and
the access log emits method/status/size (never the request target or
query). It depends only on the standard library and ``gunicorn.glogging``.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

from gunicorn.glogging import Logger  # type: ignore[import-untyped]

TOKEN_VALUE_RE = re.compile(r"sar_[0-9a-fA-F]{32}_[A-Za-z0-9_-]{32,128}")
AUTHORIZATION_RE = re.compile(r"(?i)(authorization\s*[:=]\s*)(bearer|basic)\s+[\s\S]*$")

# "Invalid request from ip=<peer>: <raw error text>"
INVALID_REQUEST_RE = re.compile(r"^Invalid request from ip=(?P<ip>\S+):")
# "Error handling request <raw target> (no URI read)"
ERROR_HANDLING_RE = re.compile(r"^Error handling request ")
# "<peer> - - [<time>] "<METHOD> <target> <proto>" <status> <size>"
ACCESS_LINE_RE = re.compile(
    r"^(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]*)\] "
    r'"(?P<method>[A-Za-z]+) (?P<target>\S+) (?P<proto>[^"]*)" '
    r"(?P<status>\d{3}) (?P<size>\d+|-)"
)


def _timestamp() -> str:
    return datetime.now(tz=UTC).isoformat()


def _redact(text: str) -> str:
    text = TOKEN_VALUE_RE.sub("[redacted]", text)
    text = AUTHORIZATION_RE.sub(r"\1[redacted]", text)
    return text


def _dump(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


class SlaifGunicornErrorFormatter(logging.Formatter):
    """Category-only JSON for the Gunicorn error log."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": _timestamp(),
            "level": record.levelname,
            "logger": record.name,
        }
        message = record.getMessage()
        invalid = INVALID_REQUEST_RE.match(message)
        if invalid:
            payload["category"] = "invalid-request"
            payload["peer"] = invalid.group("ip")
        elif ERROR_HANDLING_RE.match(message):
            payload["category"] = "request-error"
            if record.exc_info:
                exc = record.exc_info[1]
                payload["exception_type"] = type(exc).__name__
        else:
            payload["message"] = _redact(message)
            if record.exc_info:
                payload["exception_type"] = type(record.exc_info[1]).__name__
        return _dump(payload)


class SlaifGunicornAccessFormatter(logging.Formatter):
    """Method/status/size-only JSON for the Gunicorn access log."""

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        match = ACCESS_LINE_RE.match(message)
        payload: dict[str, object] = {
            "timestamp": _timestamp(),
            "level": record.levelname,
            "logger": record.name,
        }
        if match:
            size = match.group("size")
            payload.update(
                {
                    "category": "access",
                    "method": match.group("method"),
                    "peer": match.group("ip"),
                    "status": int(match.group("status")),
                    "size": None if size == "-" else int(size),
                }
            )
        else:
            payload["category"] = "access-unparsed"
        return _dump(payload)


# Gunicorn's default error page (gunicorn.util.write_error) embeds the
# exception message of a rejected request. For parser rejections that
# message is the raw request line, method, header or PROXY line exactly
# as sent by the client, so the hostile bytes would be reflected back in
# the 4xx response body. The fixed detail below replaces it; the raw text
# is already excluded from the error log by the safe formatter.
SAFE_ERROR_DETAIL = "<p>The request could not be processed.</p>"


def install_safe_error_responses() -> None:
    """Keep Gunicorn from echoing raw parser input in error response bodies.

    Idempotent: the first call installs the wrapper, later calls return.
    The wrapper is installed when the safe logger class is first used
    (the arbiter constructs it before forking workers, and each worker
    inherits the patched ``gunicorn.util`` module).
    """
    import gunicorn.util as gunicorn_util  # type: ignore[import-untyped]

    if getattr(gunicorn_util.write_error, "_slaif_safe", False):
        return
    original_write_error = gunicorn_util.write_error

    def safe_write_error(sock: Any, status_int: int, reason: str, mesg: str) -> None:
        original_write_error(sock, status_int, reason, SAFE_ERROR_DETAIL)

    safe_write_error._slaif_safe = True  # type: ignore[attr-defined]
    gunicorn_util.write_error = safe_write_error


class SlaifGunicornLogger(Logger):  # type: ignore[misc]
    """Gunicorn logger with safe JSON formatters for both loggers.

    Gunicorn 23's ``Logger.setup`` attaches its handlers directly to the
    ``gunicorn.error``/``gunicorn.access`` loggers and marks them with a
    private ``_gunicorn`` attribute; the instance ``error_handlers``/
    ``access_handlers`` lists are never populated. The formatters are
    therefore swapped on the real handlers after ``super().setup``.

    Instantiating this class also installs the safe error-response guard
    (:func:`install_safe_error_responses`), because the class is
    constructed by the arbiter before workers fork and by any process
    that runs Gunicorn with this logger.
    """

    def __init__(self, cfg: Any) -> None:
        install_safe_error_responses()
        super().__init__(cfg)

    def setup(self, cfg: Any) -> None:
        super().setup(cfg)
        for handler in self.error_log.handlers:
            if getattr(handler, "_gunicorn", False):
                handler.setFormatter(SlaifGunicornErrorFormatter())
        for handler in self.access_log.handlers:
            if getattr(handler, "_gunicorn", False):
                handler.setFormatter(SlaifGunicornAccessFormatter())
