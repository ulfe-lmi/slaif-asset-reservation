from __future__ import annotations

import logging

from django.conf import settings
from django.db import DatabaseError
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from slaif_reservation.accounts.models import ApiToken
from slaif_reservation.accounts.services import record_api_token_use
from slaif_reservation.accounts.tokens import (
    MAX_AUTHORIZATION_HEADER_LENGTH,
    api_token_verifier,
    api_token_verifier_matches,
    parse_bearer_token,
)

logger = logging.getLogger(__name__)


def _redact_authorization(request: Request) -> None:
    request.META["HTTP_AUTHORIZATION"] = "Bearer [redacted]"


class ApiTokenAuthentication(BaseAuthentication):  # type: ignore[misc]
    www_authenticate_realm = "api"

    @sensitive_variables("raw_header", "header", "credential", "candidate")
    def authenticate(self, request: Request) -> tuple[object, ApiToken] | None:
        raw_header = get_authorization_header(request)
        if not raw_header:
            return None
        try:
            header = raw_header.decode("ascii")
        except UnicodeDecodeError as exc:
            if raw_header.lower().startswith(b"bearer"):
                _redact_authorization(request)
                raise AuthenticationFailed("Invalid bearer token.") from exc
            return None
        scheme_candidate = header.split(None, 1)[0] if header.split(None, 1) else ""
        if scheme_candidate.lower() != "bearer":
            return None
        _redact_authorization(request)
        if len(raw_header) > MAX_AUTHORIZATION_HEADER_LENGTH:
            raise AuthenticationFailed("Invalid bearer token.")

        parts = header.split(" ")
        if len(parts) != 2:
            raise AuthenticationFailed("Invalid bearer token.")
        scheme, credential = parts
        if scheme.lower() != "bearer":
            return None
        if (
            not credential
            or credential.strip() != credential
            or any(character.isspace() for character in credential)
        ):
            raise AuthenticationFailed("Invalid bearer token.")

        try:
            parsed = parse_bearer_token(credential)
        except ValueError as exc:
            raise AuthenticationFailed("Invalid bearer token.") from exc

        try:
            token = ApiToken.objects.select_related("owner").get(pk=parsed.token_id)
        except ApiToken.DoesNotExist as exc:
            raise AuthenticationFailed("Invalid bearer token.") from exc

        candidate = api_token_verifier(
            bearer_token=credential,
            pepper=settings.API_TOKEN_PEPPER,
        )
        if not api_token_verifier_matches(candidate=candidate, expected=token.verifier):
            raise AuthenticationFailed("Invalid bearer token.")
        if not token.owner.is_active or token.owner.is_service_account:
            raise AuthenticationFailed("Invalid bearer token.")
        if token.revoked_at is not None:
            raise AuthenticationFailed("Invalid bearer token.")
        if token.expires_at <= timezone.now():
            raise AuthenticationFailed("Invalid bearer token.")

        try:
            record_api_token_use(token)
        except DatabaseError:
            logger.warning(
                "api_token_last_use_update_failed",
                extra={"api_token_id": str(token.id), "api_token_prefix": token.display_prefix},
            )
        return token.owner, token

    def authenticate_header(self, request: Request) -> str:
        return "Bearer"
