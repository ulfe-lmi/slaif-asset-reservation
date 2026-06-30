from __future__ import annotations

import json
import re
from typing import Any

from django.core.exceptions import ValidationError

MAX_AUDIT_METADATA_BYTES = 4096
TOKEN_PLAINTEXT_RE = re.compile(r"\bsar_[0-9a-fA-F]{32}_[A-Za-z0-9_-]{32,128}\b")

FORBIDDEN_METADATA_KEYS = {
    "api_token",
    "api_token_plaintext",
    "authorization_header",
    "bearer_token",
    "bearer_tokens",
    "password",
    "passwords",
    "pepper",
    "secret",
    "secrets",
    "token",
    "tokens",
    "verifier",
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


def _contains_token_plaintext(value: Any) -> bool:
    if isinstance(value, str):
        return bool(TOKEN_PLAINTEXT_RE.search(value))
    if isinstance(value, dict):
        return any(_contains_token_plaintext(nested) for nested in value.values())
    if isinstance(value, list):
        return any(_contains_token_plaintext(item) for item in value)
    return False


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
    if _contains_token_plaintext(value):
        raise ValidationError("Audit metadata contains API token plaintext.")
