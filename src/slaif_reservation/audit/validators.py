from __future__ import annotations

import json
from typing import Any

from django.core.exceptions import ValidationError

MAX_AUDIT_METADATA_BYTES = 4096

FORBIDDEN_METADATA_KEYS = {
    "password",
    "passwords",
    "token",
    "tokens",
    "cookie",
    "cookies",
    "authorization",
    "raw_request_body",
    "email",
    "purpose",
    "cancellation_reason",
    "physical_locator",
}


def validate_audit_metadata(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValidationError("Audit metadata must be a JSON object.")

    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > MAX_AUDIT_METADATA_BYTES:
        raise ValidationError("Audit metadata is too large.")

    forbidden = FORBIDDEN_METADATA_KEYS & set(value)
    if forbidden:
        raise ValidationError(
            f"Audit metadata contains forbidden key(s): {', '.join(sorted(forbidden))}."
        )
