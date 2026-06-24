from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import DatabaseError, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from slaif_reservation.accounts.exceptions import (
    TOKEN_LIFETIME_INVALID,
    TOKEN_NOT_OWNED,
    TOKEN_OWNER_INVALID,
    ApiTokenDomainError,
)
from slaif_reservation.accounts.models import API_TOKEN_SERVICE_UPDATE_ATTR, ApiToken, User
from slaif_reservation.accounts.tokens import (
    api_token_verifier,
    format_bearer_token,
    generate_api_token_secret,
    normalize_api_token_scopes,
)
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.audit.services import append_audit_event

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ApiTokenIssueResult:
    token: ApiToken
    bearer_token: str = field(repr=False, compare=False)
    correlation_id: uuid.UUID


@dataclass(frozen=True)
class ApiTokenMutationResult:
    token: ApiToken
    correlation_id: uuid.UUID


def _correlation(value: uuid.UUID | None) -> uuid.UUID:
    return value or uuid.uuid4()


def _raise(code: str, message: str) -> None:
    raise ApiTokenDomainError(code, message)


def _utc_now(value: datetime | None = None) -> datetime:
    candidate = timezone.now() if value is None else value
    if timezone.is_naive(candidate):
        _raise(TOKEN_LIFETIME_INVALID, "Current time must be timezone-aware.")
    return candidate.astimezone(UTC)


def _lock_active_human(owner: Any) -> User:
    locked = User.objects.select_for_update().get(pk=owner.pk)
    if not locked.is_active or locked.is_service_account:
        _raise(TOKEN_OWNER_INVALID, "API token owner must be an active human user.")
    return locked


def _service_save(token: ApiToken, *, update_fields: list[str] | None = None) -> None:
    setattr(token, API_TOKEN_SERVICE_UPDATE_ATTR, True)
    try:
        if update_fields is None:
            token.save()
        else:
            token.save(update_fields=update_fields)
    finally:
        if hasattr(token, API_TOKEN_SERVICE_UPDATE_ATTR):
            delattr(token, API_TOKEN_SERVICE_UPDATE_ATTR)


def _validate_lifetime_days(lifetime_days: int) -> int:
    try:
        lifetime = int(lifetime_days)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Lifetime must be an integer number of days.") from exc
    maximum = int(settings.API_TOKEN_MAX_LIFETIME_DAYS)
    if lifetime < 1 or lifetime > maximum:
        raise ValidationError(f"Lifetime must be between 1 and {maximum} days.")
    return lifetime


@sensitive_variables("bearer_token", "secret")
def issue_api_token(
    *,
    owner: Any,
    name: str,
    scopes: list[str],
    lifetime_days: int,
    source: str = AuditEvent.SOURCE_WEB,
    now: datetime | None = None,
    correlation_id: uuid.UUID | None = None,
) -> ApiTokenIssueResult:
    now_utc = _utc_now(now)
    correlation = _correlation(correlation_id)
    canonical_scopes = normalize_api_token_scopes(scopes)
    lifetime = _validate_lifetime_days(lifetime_days)
    cleaned_name = name.strip()
    if not cleaned_name:
        raise ValidationError({"name": ["Token name is required."]})
    if len(cleaned_name) > 100:
        raise ValidationError({"name": ["Ensure this value has at most 100 characters."]})

    with transaction.atomic():
        locked_owner = _lock_active_human(owner)
        token_id = uuid.uuid4()
        secret = generate_api_token_secret()
        bearer_token = format_bearer_token(token_id=token_id, secret=secret)
        token = ApiToken(
            id=token_id,
            owner=locked_owner,
            name=cleaned_name,
            verifier=api_token_verifier(
                bearer_token=bearer_token,
                pepper=settings.API_TOKEN_PEPPER,
            ),
            scopes=canonical_scopes,
            expires_at=now_utc + timedelta(days=lifetime),
        )
        token.full_clean()
        _service_save(token)
        append_audit_event(
            action=AuditEvent.ACTION_API_TOKEN_CREATED,
            target_type="api_token",
            target_id=token.id,
            correlation_id=correlation,
            source=source,
            actor_user=locked_owner,
            metadata={
                "display_prefix": token.display_prefix,
                "scopes": token.scopes,
                "expires_at": token.expires_at.isoformat(),
            },
        )
        return ApiTokenIssueResult(
            token=token,
            bearer_token=bearer_token,
            correlation_id=correlation,
        )


def revoke_api_token(
    *,
    token: ApiToken,
    owner: Any,
    source: str = AuditEvent.SOURCE_WEB,
    now: datetime | None = None,
    correlation_id: uuid.UUID | None = None,
) -> ApiTokenMutationResult:
    now_utc = _utc_now(now)
    correlation = _correlation(correlation_id)

    with transaction.atomic():
        locked_owner = _lock_active_human(owner)
        locked = ApiToken.objects.select_for_update().get(pk=token.pk)
        if locked.owner_id != locked_owner.pk:
            _raise(TOKEN_NOT_OWNED, "API token was not found for this owner.")
        if locked.revoked_at is not None:
            return ApiTokenMutationResult(token=locked, correlation_id=correlation)

        locked.revoked_at = now_utc
        locked.revoked_by = locked_owner
        locked.full_clean()
        _service_save(locked, update_fields=["revoked_at", "revoked_by"])
        append_audit_event(
            action=AuditEvent.ACTION_API_TOKEN_REVOKED,
            target_type="api_token",
            target_id=locked.id,
            correlation_id=correlation,
            source=source,
            actor_user=locked_owner,
            metadata={
                "display_prefix": locked.display_prefix,
                "scopes": locked.scopes,
                "expires_at": locked.expires_at.isoformat(),
            },
        )
        return ApiTokenMutationResult(token=locked, correlation_id=correlation)


def record_api_token_use(token: ApiToken, *, used_at: datetime | None = None) -> None:
    now_utc = _utc_now(used_at)
    try:
        with transaction.atomic():
            locked = ApiToken.objects.select_for_update().get(pk=token.pk)
            if locked.last_used_at is not None and locked.last_used_at >= now_utc:
                return
            locked.last_used_at = now_utc
            locked.full_clean()
            _service_save(locked, update_fields=["last_used_at"])
            token.last_used_at = locked.last_used_at
    except (DatabaseError, ValidationError) as exc:
        logger.warning(
            "api_token_last_use_update_failed",
            extra={"api_token_id": str(token.id), "api_token_prefix": token.display_prefix},
            exc_info=exc,
        )
