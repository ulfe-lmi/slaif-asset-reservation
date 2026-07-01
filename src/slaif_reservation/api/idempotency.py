from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from slaif_reservation.accounts.models import ApiToken, User
from slaif_reservation.api.models import IdempotencyRecord
from slaif_reservation.api.problem import problem_response

IDEMPOTENCY_KEY_MIN_LENGTH = 8
IDEMPOTENCY_KEY_MAX_LENGTH = 128
IDEMPOTENCY_RECORD_TTL = timedelta(hours=24)
IDEMPOTENCY_KEY_RE = re.compile(r"^[!-~]{8,128}$")
SAFE_REPLAY_HEADERS = {"Location"}


@dataclass(frozen=True)
class MutationResult:
    status_code: int
    body: dict[str, Any]
    target_type: str
    target_id: uuid.UUID | None
    headers: dict[str, str] | None = None


def validate_idempotency_key(value: str | None) -> str:
    if value is None:
        raise ValueError("Idempotency-Key header is required.")
    key = value.strip()
    if key != value or not IDEMPOTENCY_KEY_RE.fullmatch(key):
        raise ValueError("Idempotency-Key must be 8 to 128 printable non-whitespace characters.")
    return key


def canonical_request_hash(
    *,
    method: str,
    path: str,
    body: Any,
    action: str,
) -> str:
    payload = {
        "action": action,
        "body": _json_safe(body),
        "method": method.upper(),
        "path": path,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def execute_idempotent_mutation(
    *,
    request: Request,
    owner: User,
    api_token: ApiToken,
    action: str,
    body: Any,
    correlation_id: uuid.UUID,
    callback: Callable[[], MutationResult],
) -> Response:
    raw_key = request.headers.get("Idempotency-Key")
    try:
        key = validate_idempotency_key(raw_key)
    except ValueError:
        return problem_response(
            request=request,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="idempotency_required" if raw_key is None else "invalid_idempotency_key",
            title="Invalid idempotency key",
            detail="Mutation endpoints require a valid Idempotency-Key header.",
            correlation_id=correlation_id,
        )

    request_hash = canonical_request_hash(
        method=request.method,
        path=request.path,
        body=body,
        action=action,
    )

    with transaction.atomic():
        existing = _locked_record(
            owner=owner,
            api_token=api_token,
            action=action,
            key=key,
        )
        if existing is not None:
            return _response_for_existing(request, existing, request_hash, correlation_id)

        record = IdempotencyRecord(
            owner=owner,
            api_token=api_token,
            action=action,
            idempotency_key=key,
            canonical_request_hash=request_hash,
            request_method=request.method.upper(),
            request_path=request.path,
            correlation_id=correlation_id,
            expires_at=timezone.now() + IDEMPOTENCY_RECORD_TTL,
        )
        try:
            with transaction.atomic():
                record.save()
        except IntegrityError:
            existing = _locked_record(
                owner=owner,
                api_token=api_token,
                action=action,
                key=key,
            )
            if existing is not None:
                return _response_for_existing(request, existing, request_hash, correlation_id)
            raise

        result = callback()
        record.response_status = result.status_code
        record.response_body = result.body
        record.response_headers = _safe_replay_headers(result.headers or {})
        record.target_type = result.target_type
        record.target_id = result.target_id
        record.correlation_id = uuid.UUID(str(result.body.get("correlation_id", correlation_id)))
        record.save(
            update_fields=[
                "response_status",
                "response_body",
                "response_headers",
                "target_type",
                "target_id",
                "correlation_id",
            ]
        )
        response = Response(result.body, status=result.status_code)
        response["X-Request-ID"] = str(record.correlation_id)
        for key_name, value in (result.headers or {}).items():
            response[key_name] = value
        return response


def _locked_record(
    *,
    owner: User,
    api_token: ApiToken,
    action: str,
    key: str,
) -> IdempotencyRecord | None:
    return (
        IdempotencyRecord.objects.select_for_update()
        .filter(owner=owner, api_token=api_token, action=action, idempotency_key=key)
        .first()
    )


def _response_for_existing(
    request: Request,
    record: IdempotencyRecord,
    request_hash: str,
    correlation_id: uuid.UUID,
) -> Response:
    if record.expires_at <= timezone.now():
        return problem_response(
            request=request,
            status_code=status.HTTP_409_CONFLICT,
            code="idempotency_expired",
            title="Idempotency key expired",
            detail="The Idempotency-Key was already used and its replay window has expired.",
            correlation_id=correlation_id,
        )
    if record.canonical_request_hash != request_hash:
        return problem_response(
            request=request,
            status_code=status.HTTP_409_CONFLICT,
            code="idempotency_conflict",
            title="Idempotency conflict",
            detail="The Idempotency-Key was already used for a different request.",
            correlation_id=correlation_id,
        )
    if record.response_status is None:
        return problem_response(
            request=request,
            status_code=status.HTTP_409_CONFLICT,
            code="idempotency_conflict",
            title="Idempotency conflict",
            detail="The Idempotency-Key is already being processed.",
            correlation_id=correlation_id,
        )
    response = Response(record.response_body, status=record.response_status)
    response["X-Request-ID"] = str(record.correlation_id)
    response["X-Idempotent-Replay"] = "true"
    for key_name, value in _safe_replay_headers(record.response_headers).items():
        response[key_name] = value
    return response


def _safe_replay_headers(headers: dict[str, Any]) -> dict[str, str]:
    safe: dict[str, str] = {}
    for key_name, value in headers.items():
        canonical = str(key_name).strip()
        if canonical not in SAFE_REPLAY_HEADERS:
            continue
        text = str(value).strip()
        if not text or len(text) > 2048 or "\r" in text or "\n" in text:
            continue
        safe[canonical] = text
    return safe


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
