from __future__ import annotations

import hmac
import re
import secrets
import uuid
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.views.decorators.debug import sensitive_variables

TOKEN_PREFIX = "sar"
TOKEN_SECRET_BYTES = 32
TOKEN_SECRET_MIN_LENGTH = 32
TOKEN_SECRET_MAX_LENGTH = 128
MAX_AUTHORIZATION_HEADER_LENGTH = 512
API_TOKEN_PEPPER_MIN_BYTES = 32
DEVELOPMENT_API_TOKEN_PEPPER = "unsafe-development-api-token-pepper-do-not-use-in-production"
TEST_API_TOKEN_PEPPER = "test-only-api-token-pepper-not-for-production-32-bytes"
UNSAFE_API_TOKEN_PEPPERS = frozenset(
    {
        DEVELOPMENT_API_TOKEN_PEPPER,
        TEST_API_TOKEN_PEPPER,
    }
)

ALLOWED_API_TOKEN_SCOPES = (
    "assets:read",
    "availability:read",
    "reservations:read",
    "reservations:create",
    "reservations:cancel",
    "reservations:release",
)
ALLOWED_API_TOKEN_SCOPE_SET = frozenset(ALLOWED_API_TOKEN_SCOPES)

_SECRET_RE = re.compile(r"^[A-Za-z0-9_-]+$")


@dataclass(frozen=True)
class ParsedBearerToken:
    token_id: uuid.UUID


@dataclass(frozen=True)
class OneTimeBearerToken:
    value: str = field(repr=False, compare=False)

    def __str__(self) -> str:
        return self.value


def validate_api_token_scopes(value: Any) -> None:
    normalize_api_token_scopes(value)


def normalize_api_token_scopes(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise ValidationError(_("API token scopes must be a JSON list."))
    if not value:
        raise ValidationError(_("API token scopes must include at least one scope."))

    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValidationError(_("API token scopes must be strings."))
        scope = item.strip()
        if not scope:
            raise ValidationError(_("API token scopes must not be empty."))
        if scope not in ALLOWED_API_TOKEN_SCOPE_SET:
            raise ValidationError(_("API token scope is not allowed."))
        normalized.append(scope)

    canonical = sorted(set(normalized))
    if len(canonical) != len(normalized):
        raise ValidationError(_("API token scopes must be unique."))
    return canonical


def display_prefix_for_token_id(token_id: uuid.UUID) -> str:
    return f"{TOKEN_PREFIX}_{token_id.hex[:12]}..."


def generate_api_token_secret() -> str:
    return secrets.token_hex(TOKEN_SECRET_BYTES)


@sensitive_variables("secret")
def format_bearer_token(*, token_id: uuid.UUID, secret: str) -> str:
    return f"{TOKEN_PREFIX}_{token_id.hex}_{secret}"


@sensitive_variables("value", "secret")
def parse_bearer_token(value: str) -> ParsedBearerToken:
    if len(value) > MAX_AUTHORIZATION_HEADER_LENGTH:
        raise ValueError("Invalid API token.")

    parts = value.split("_")
    if len(parts) != 3 or parts[0] != TOKEN_PREFIX:
        raise ValueError("Invalid API token.")

    raw_uuid = parts[1]
    secret = parts[2]
    if len(raw_uuid) != 32:
        raise ValueError("Invalid API token.")
    if not (TOKEN_SECRET_MIN_LENGTH <= len(secret) <= TOKEN_SECRET_MAX_LENGTH):
        raise ValueError("Invalid API token.")
    if not _SECRET_RE.fullmatch(secret):
        raise ValueError("Invalid API token.")

    try:
        token_id = uuid.UUID(hex=raw_uuid)
    except ValueError as exc:
        raise ValueError("Invalid API token.") from exc
    return ParsedBearerToken(token_id=token_id)


@sensitive_variables("bearer_token", "pepper")
def api_token_verifier(*, bearer_token: str, pepper: str) -> str:
    return hmac.new(
        pepper.encode("utf-8"),
        bearer_token.encode("utf-8"),
        sha256,
    ).hexdigest()


def api_token_verifier_matches(*, candidate: str, expected: str) -> bool:
    return hmac.compare_digest(candidate, expected)


@sensitive_variables("pepper", "secret_key")
def validate_api_token_pepper(pepper: str, *, secret_key: str | None = None) -> None:
    if not pepper or not pepper.strip():
        raise ValidationError(_("API token pepper is required."))
    if len(pepper.encode("utf-8")) < API_TOKEN_PEPPER_MIN_BYTES:
        raise ValidationError(_("API token pepper must be at least 32 UTF-8 bytes."))
    if secret_key is not None and pepper == secret_key:
        raise ValidationError(_("API token pepper must be distinct from SECRET_KEY."))
    if pepper.strip() in UNSAFE_API_TOKEN_PEPPERS:
        raise ValidationError(_("Configured API token pepper is forbidden in production."))
