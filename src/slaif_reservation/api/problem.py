from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import Any, cast

from django.http import HttpRequest
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import exception_handler


def correlation_id_from_request(request: Request | HttpRequest | None) -> uuid.UUID:
    existing = getattr(request, "_slaif_correlation_id", None)
    if isinstance(existing, uuid.UUID):
        return existing
    raw = ""
    if request is not None:
        meta = getattr(request, "META", {})
        raw = str(meta.get("HTTP_X_REQUEST_ID", "")).strip()
    try:
        correlation = uuid.UUID(raw)
    except (TypeError, ValueError):
        correlation = uuid.uuid4()
    if request is not None:
        cast(Any, request)._slaif_correlation_id = correlation
    return correlation


def problem_response(
    *,
    request: Request | HttpRequest | None,
    status_code: int,
    code: str,
    title: str | None = None,
    detail: str | None = None,
    correlation_id: uuid.UUID | None = None,
) -> Response:
    correlation = correlation_id or correlation_id_from_request(request)
    phrase = title or HTTPStatus(status_code).phrase
    body = {
        "type": f"https://slaif.local/problems/{code}",
        "title": phrase,
        "status": status_code,
        "code": code,
        "detail": detail or phrase,
        "correlation_id": str(correlation),
    }
    response = Response(body, status=status_code, content_type="application/problem+json")
    response["X-Request-ID"] = str(correlation)
    return response


class InsufficientScope(APIException):  # type: ignore[misc]
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "The token does not grant this operation."
    default_code = "insufficient_scope"


class IdempotencyConflict(APIException):  # type: ignore[misc]
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The idempotency key conflicts with a previous request."
    default_code = "idempotency_conflict"


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    request = context.get("request")
    if isinstance(exc, NotAuthenticated):
        return problem_response(
            request=request,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="authentication_required",
            title="Authentication required",
            detail="Bearer token authentication is required.",
        )
    if isinstance(exc, AuthenticationFailed):
        return problem_response(
            request=request,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_token",
            title="Invalid token",
            detail="Bearer token authentication failed.",
        )
    if isinstance(exc, InsufficientScope):
        return problem_response(
            request=request,
            status_code=status.HTTP_403_FORBIDDEN,
            code="insufficient_scope",
            title="Insufficient scope",
            detail="The token does not grant this operation.",
        )
    if isinstance(exc, IdempotencyConflict):
        return problem_response(
            request=request,
            status_code=status.HTTP_409_CONFLICT,
            code="idempotency_conflict",
            title="Idempotency conflict",
            detail="The idempotency key conflicts with a previous request.",
        )
    if isinstance(exc, PermissionDenied):
        return problem_response(
            request=request,
            status_code=status.HTTP_403_FORBIDDEN,
            code="permission_denied",
            title="Permission denied",
            detail="The requested operation is not permitted.",
        )
    if isinstance(exc, NotFound):
        return problem_response(
            request=request,
            status_code=status.HTTP_404_NOT_FOUND,
            code="not_found",
            title="Not found",
            detail="The requested resource was not found.",
        )
    if isinstance(exc, ValidationError):
        return problem_response(
            request=request,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="validation_error",
            title="Validation error",
            detail="The request parameters or body are invalid.",
        )

    response = exception_handler(exc, context)
    if response is None:
        return None
    code = getattr(getattr(exc, "default_code", None), "value", None) or "api_error"
    return problem_response(
        request=request,
        status_code=response.status_code,
        code=str(code),
        detail="The request could not be completed.",
    )
