from __future__ import annotations

import json
import re
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


def _normalized_key(value: Any) -> str:
    return re.sub(r"[\s-]+", "_", str(value).strip().lower())


def _forbidden_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        dict_found = {
            normalized_key
            for key in value
            if (normalized_key := _normalized_key(key)) in FORBIDDEN_METADATA_KEYS
        }
        for nested in value.values():
            dict_found.update(_forbidden_keys(nested))
        return dict_found
    if isinstance(value, list):
        list_found: set[str] = set()
        for item in value:
            list_found.update(_forbidden_keys(item))
        return list_found
    return set()


def validate_audit_metadata(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValidationError("Audit metadata must be a JSON object.")

    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > MAX_AUDIT_METADATA_BYTES:
        raise ValidationError("Audit metadata is too large.")

    forbidden = _forbidden_keys(value)
    if forbidden:
        raise ValidationError(
            f"Audit metadata contains forbidden key(s): {', '.join(sorted(forbidden))}."
        )
