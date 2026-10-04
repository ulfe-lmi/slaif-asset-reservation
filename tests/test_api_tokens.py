from __future__ import annotations

import asyncio
import hmac
import logging
import os
import re
import sys
import uuid
from datetime import UTC, timedelta

import pytest
from django.conf import settings
from django.contrib.admin.sites import site
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, connection, transaction
from django.test import Client, override_settings
from django.utils import timezone
from django.views.debug import ExceptionReporter
from django.views.decorators.debug import sensitive_variables
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from slaif_reservation.accounts.admin import ApiTokenAdmin
from slaif_reservation.accounts.exceptions import (
    TOKEN_NOT_OWNED,
    TOKEN_OWNER_INVALID,
    ApiTokenDomainError,
)
from slaif_reservation.accounts.models import (
    API_TOKEN_SERVICE_CREATE_ATTR,
    API_TOKEN_SERVICE_UPDATE_ATTR,
    ApiToken,
    User,
)
from slaif_reservation.accounts.services import (
    _service_save,
    issue_api_token,
    record_api_token_use,
    revoke_api_token,
)
from slaif_reservation.accounts.tokens import (
    DEVELOPMENT_API_TOKEN_PEPPER,
    MAX_AUTHORIZATION_HEADER_LENGTH,
    TEST_API_TOKEN_PEPPER,
    UNSAFE_API_TOKEN_PEPPERS,
    OneTimeBearerToken,
    api_token_verifier,
    display_prefix_for_token_id,
    format_bearer_token,
    normalize_api_token_scopes,
    parse_bearer_token,
    validate_api_token_pepper,
)
from slaif_reservation.api.authentication import ApiTokenAuthentication
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.audit.services import append_audit_event
from slaif_reservation.audit.validators import validate_audit_metadata


def user(email: str = "token-owner@example.com", **overrides: object) -> User:
    return User.objects.create_user(email=email, password="not-a-secret", **overrides)


def issue(owner: User, **overrides: object):
    values = {
        "owner": owner,
        "name": "Local agent",
        "scopes": ["assets:read", "reservations:create"],
        "lifetime_days": 30,
    }
    values.update(overrides)
    return issue_api_token(**values)


def token_row(owner: User, **overrides: object) -> ApiToken:
    token_id = overrides.pop("id", uuid.uuid4())
    secret = str(overrides.pop("secret", "A" * 43))
    bearer = format_bearer_token(token_id=token_id, secret=secret)
    values = {
        "id": token_id,
        "owner": owner,
        "name": "Existing token",
        "verifier": api_token_verifier(bearer_token=bearer, pepper=settings.API_TOKEN_PEPPER),
        "scopes": ["assets:read"],
        "expires_at": timezone.now() + timedelta(days=1),
    }
    values.update(overrides)
    token = ApiToken(**values)
    setattr(token, API_TOKEN_SERVICE_CREATE_ATTR, True)
    try:
        token.save()
    finally:
        if hasattr(token, API_TOKEN_SERVICE_CREATE_ATTR):
            delattr(token, API_TOKEN_SERVICE_CREATE_ATTR)
    return token


def assert_domain_error(code: str):
    return pytest.raises(ApiTokenDomainError, match=".", check=lambda exc: exc.code == code)


def connection_cursor():
    return connection.cursor()


def assert_secret_absent(needle: str, haystack: str, message: str = "secret leaked") -> None:
    if needle and needle in haystack:
        raise AssertionError(message)


def set_token_timestamps(token: ApiToken, *, created_at, expires_at) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE accounts_apitoken
               SET created_at = %s,
                   expires_at = %s
             WHERE id = %s
            """,
            [created_at, expires_at, token.id],
        )
    token.created_at = created_at
    token.expires_at = expires_at


def extract_bearer_from_html(content: str) -> str:
    match = re.search(r"sar_[0-9a-f]{32}_[A-Za-z0-9_-]+", content)
    if match is None:
        raise AssertionError("one-time bearer token was not rendered")
    return match.group(0)


def test_scope_normalization_and_validation() -> None:
    assert normalize_api_token_scopes(["reservations:create", "assets:read"]) == [
        "assets:read",
        "reservations:create",
    ]
    for value in [[], "assets:read", {"scope": "assets:read"}, ["assets:read", "assets:read"]]:
        with pytest.raises(ValidationError):
            normalize_api_token_scopes(value)
    for value in [[1], [""], ["admin:*"], [["assets:read"]]]:
        with pytest.raises(ValidationError):
            normalize_api_token_scopes(value)


def test_token_format_parser_and_verifier_uses_compare_digest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token_id = uuid.uuid4()
    bearer = format_bearer_token(token_id=token_id, secret="A" * 43)
    parsed = parse_bearer_token(bearer)
    assert parsed.token_id == token_id
    assert str(token_id) in repr(parsed)
    assert_secret_absent(bearer, repr(parsed))
    assert_secret_absent("A" * 43, repr(parsed))
    assert display_prefix_for_token_id(token_id) == f"sar_{token_id.hex[:12]}..."

    called = False
    original_compare = hmac.compare_digest

    def fake_compare(left: str, right: str) -> bool:
        nonlocal called
        called = True
        return original_compare(left, right)

    monkeypatch.setattr("slaif_reservation.accounts.tokens.hmac.compare_digest", fake_compare)
    from slaif_reservation.accounts.tokens import api_token_verifier_matches

    assert api_token_verifier_matches(candidate="a", expected="a")
    assert called


@pytest.mark.parametrize(
    "credential",
    [
        "sar_missing",
        "sar_nothex_" + "A" * 43,
        "foo_" + ("a" * 32) + "_" + "A" * 43,
        "sar_" + ("a" * 32) + "_bad*secret",
        "sar_" + ("a" * 32) + "_" + "A" * 200,
        " sar_" + ("a" * 32) + "_" + "A" * 43,
        "sar_" + ("a" * 32) + "_" + "A" * 43 + "_extra",
    ],
)
def test_token_parser_rejects_malformed_credentials(credential: str) -> None:
    with pytest.raises(ValueError):
        parse_bearer_token(credential)


@pytest.mark.django_db
def test_token_issue_result_repr_redacts_plaintext() -> None:
    owner = user()
    result = issue(owner)
    secret = result.bearer_token.rsplit("_", 1)[1]
    wrapper = OneTimeBearerToken(result.bearer_token)

    rendered = repr(result)

    assert str(wrapper) == result.bearer_token
    assert wrapper == OneTimeBearerToken("different-redacted-value")
    assert_secret_absent(result.bearer_token, repr(wrapper))
    assert_secret_absent(secret, repr(wrapper))
    assert result.token.display_prefix in rendered
    assert_secret_absent(result.bearer_token, rendered)
    assert_secret_absent(secret, rendered)


def test_token_pepper_validation() -> None:
    validate_api_token_pepper("x" * 32, secret_key="different")
    for value, secret in [
        ("", "secret"),
        ("   ", "secret"),
        ("short", "secret"),
        ("same-secret-" + ("x" * 32), "same-secret-" + ("x" * 32)),
        *[(pepper, "different") for pepper in UNSAFE_API_TOKEN_PEPPERS],
        *[(f"  {pepper}\n", "different") for pepper in UNSAFE_API_TOKEN_PEPPERS],
    ]:
        with pytest.raises(ValidationError):
            validate_api_token_pepper(value, secret_key=secret)


@pytest.mark.django_db
def test_api_token_model_status_constraints_and_uuid() -> None:
    owner = user()
    token = token_row(owner)
    assert isinstance(token.id, uuid.UUID)
    assert token.display_prefix == f"sar_{token.id.hex[:12]}..."
    assert token.status == ApiToken.STATUS_ACTIVE
    assert token.has_scope("assets:read")

    expired = token_row(owner, id=uuid.uuid4(), name="Expired")
    expired.created_at = timezone.now() - timedelta(days=2)
    expired.expires_at = timezone.now() - timedelta(days=1)
    assert expired.status == ApiToken.STATUS_EXPIRED

    revoked = token_row(
        owner,
        id=uuid.uuid4(),
        name="Revoked",
        revoked_at=timezone.now(),
        revoked_by=owner,
    )
    revoked.created_at = timezone.now() - timedelta(days=2)
    revoked.expires_at = timezone.now() - timedelta(days=1)
    assert revoked.status == ApiToken.STATUS_REVOKED


@pytest.mark.django_db
def test_api_token_model_rejects_invalid_shapes() -> None:
    owner = user()
    invalid = ApiToken(
        owner=owner,
        name=" ",
        verifier="x" * 64,
        scopes=[],
        expires_at=timezone.now() + timedelta(days=1),
    )
    with pytest.raises(ValidationError):
        invalid.full_clean()

    invalid = ApiToken(
        owner=owner,
        name="Bad",
        verifier="x" * 64,
        scopes=["assets:read"],
        expires_at=timezone.now() + timedelta(days=1),
        revoked_at=timezone.now(),
    )
    with pytest.raises(ValidationError):
        invalid.full_clean()


@pytest.mark.django_db
def test_api_token_database_constraints() -> None:
    owner = user()
    with pytest.raises(IntegrityError), transaction.atomic(), connection_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO accounts_apitoken
              (id, owner_id, name, verifier, scopes, expires_at, created_at)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s)
            """,
            [
                uuid.uuid4(),
                owner.id,
                "No scopes",
                "x" * 64,
                "[]",
                timezone.now() + timedelta(days=1),
                timezone.now(),
            ],
        )

    with pytest.raises(IntegrityError), transaction.atomic(), connection_cursor() as cursor:
        now = timezone.now()
        cursor.execute(
            """
            INSERT INTO accounts_apitoken
              (id, owner_id, name, verifier, scopes, expires_at, created_at, revoked_at)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s)
            """,
            [
                uuid.uuid4(),
                owner.id,
                "Bad revoke",
                "x" * 64,
                '["assets:read"]',
                now + timedelta(days=1),
                now,
                now,
            ],
        )


@pytest.mark.django_db
def test_api_token_orm_bypass_paths_are_blocked() -> None:
    owner = user()
    token = token_row(owner)
    original = ApiToken.objects.get(pk=token.pk)

    with pytest.raises(ValidationError):
        ApiToken.objects.create(
            owner=owner,
            name="Direct",
            verifier="d" * 64,
            scopes=["assets:read"],
            expires_at=timezone.now() + timedelta(days=1),
        )

    replacement = ApiToken(
        id=token.id,
        owner=owner,
        name="Replacement",
        verifier="y" * 64,
        scopes=["reservations:read"],
        expires_at=timezone.now() + timedelta(days=10),
    )
    with pytest.raises(ValidationError):
        replacement.save()

    token.name = "Changed"
    with pytest.raises(ValidationError):
        token.save()

    with pytest.raises(ValidationError):
        ApiToken.objects.filter(pk=token.pk).update(name="Changed")
    with pytest.raises(ValidationError):
        ApiToken.objects.filter(pk=token.pk).delete()
    with pytest.raises(ValidationError):
        token.delete()
    bulk_token = ApiToken(
        owner=owner,
        name="Bulk",
        verifier="z" * 64,
        scopes=["assets:read"],
        expires_at=timezone.now() + timedelta(days=1),
    )
    for kwargs in [
        {},
        {"ignore_conflicts": True},
        {"update_conflicts": True, "update_fields": ["name"], "unique_fields": ["id"]},
    ]:
        with pytest.raises(ValidationError):
            ApiToken.objects.bulk_create([bulk_token], **kwargs)
    with pytest.raises(ValidationError):
        ApiToken.objects.all().bulk_create([token])
    with pytest.raises(ValidationError):
        ApiToken.objects.bulk_update([token], ["name"])
    with pytest.raises(ValidationError):
        ApiToken._base_manager.filter(pk=token.pk).update(name="Changed")
    with pytest.raises(ValidationError):
        ApiToken._base_manager.filter(pk=token.pk).delete()
    with pytest.raises(ValidationError):
        ApiToken._base_manager.bulk_create([bulk_token])
    with pytest.raises(ValidationError):
        ApiToken._base_manager.bulk_update([token], ["name"])

    current = ApiToken.objects.get(pk=token.pk)
    assert current.name == original.name
    assert current.verifier == original.verifier
    assert current.scopes == original.scopes


@pytest.mark.django_db
def test_api_token_service_marker_cannot_change_immutable_history() -> None:
    owner = user()
    other = user("other-immutable@example.com")
    token = token_row(owner)
    original = ApiToken.objects.get(pk=token.pk)

    immutable_mutations = [
        ("id", uuid.uuid4()),
        ("owner", other),
        ("name", "Changed"),
        ("verifier", "f" * 64),
        ("scopes", ["reservations:read"]),
        ("expires_at", original.expires_at + timedelta(days=1)),
        ("created_at", original.created_at + timedelta(seconds=1)),
    ]

    for field_name, value in immutable_mutations:
        candidate = ApiToken.objects.get(pk=original.pk)
        setattr(candidate, field_name, value)
        setattr(candidate, API_TOKEN_SERVICE_UPDATE_ATTR, True)
        with pytest.raises(ValidationError):
            candidate.save(update_fields=["last_used_at"])
        current = ApiToken.objects.get(pk=original.pk)
        assert current.id == original.id
        assert current.owner_id == original.owner_id
        assert current.name == original.name
        assert current.verifier == original.verifier
        assert current.scopes == original.scopes
        assert current.expires_at == original.expires_at
        assert current.created_at == original.created_at

    assert AuditEvent.objects.count() == 0


@pytest.mark.django_db
def test_api_token_service_save_rejects_unauthorized_update_fields() -> None:
    owner = user()
    token = token_row(owner)
    token.last_used_at = timezone.now()

    with pytest.raises(ValidationError):
        _service_save(token, update_fields=["last_used_at", "name"])

    with pytest.raises(ValidationError):
        _service_save(token)

    current = ApiToken.objects.get(pk=token.pk)
    assert current.last_used_at is None
    assert current.name == token.name


@pytest.mark.django_db
def test_api_token_async_bulk_create_is_blocked() -> None:
    with pytest.raises(ValidationError):
        asyncio.run(ApiToken.objects.abulk_create([]))


@pytest.mark.django_db
def test_issue_api_token_stores_verifier_not_plaintext_and_audits() -> None:
    owner = user()
    result = issue(owner)
    token = ApiToken.objects.get(pk=result.token.pk)

    assert result.bearer_token.startswith(f"sar_{token.id.hex}_")
    fields = [str(getattr(token, field.name)) for field in token._meta.fields]
    for value in fields:
        assert_secret_absent(result.bearer_token, value, "bearer token stored in model field")
    assert token.verifier == api_token_verifier(
        bearer_token=result.bearer_token,
        pepper="test-only-api-token-pepper-not-for-production-32-bytes",
    )
    event = AuditEvent.objects.get(action=AuditEvent.ACTION_API_TOKEN_CREATED)
    assert event.target_type == "api_token"
    assert event.target_id == token.id
    assert event.metadata["display_prefix"] == token.display_prefix
    assert event.metadata["scopes"] == token.scopes
    assert_secret_absent(result.bearer_token, str(event.metadata), "bearer token stored in audit")
    assert token.name not in str(event.metadata)


@pytest.mark.django_db
def test_issue_api_token_rejects_inactive_and_service_account() -> None:
    inactive = user("inactive@example.com", is_active=False)
    service = user("service@example.com", is_service_account=True)
    for owner in [inactive, service]:
        with assert_domain_error(TOKEN_OWNER_INVALID):
            issue(owner)
    assert ApiToken.objects.count() == 0
    assert AuditEvent.objects.count() == 0


@pytest.mark.django_db
def test_issue_api_token_lifetime_bounds(settings) -> None:
    settings.API_TOKEN_MAX_LIFETIME_DAYS = 7
    owner = user()
    for lifetime in [0, 8]:
        with pytest.raises(ValidationError):
            issue(owner, lifetime_days=lifetime)
    assert issue(owner, lifetime_days=7).token.expires_at > timezone.now()


@pytest.mark.django_db
def test_issue_api_token_rolls_back_when_audit_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    owner = user()

    def fail_audit(**kwargs: object) -> AuditEvent:
        raise RuntimeError("audit failed")

    monkeypatch.setattr("slaif_reservation.accounts.services.append_audit_event", fail_audit)

    with pytest.raises(RuntimeError):
        issue(owner)
    assert ApiToken.objects.count() == 0


@pytest.mark.django_db
def test_revoke_api_token_owner_idempotency_and_audit() -> None:
    owner = user()
    result = issue(owner)
    token = result.token

    revoke_result = revoke_api_token(token=token, owner=owner)
    token.refresh_from_db()
    assert token.revoked_at is not None
    assert token.revoked_by == owner
    assert revoke_result.token.id == token.id
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_API_TOKEN_REVOKED).count() == 1

    revoke_api_token(token=token, owner=owner)
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_API_TOKEN_REVOKED).count() == 1


@pytest.mark.django_db
def test_revoke_api_token_other_user_denied_and_rolls_back_on_audit_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner = user()
    other = user("other@example.com")
    token = issue(owner).token
    with assert_domain_error(TOKEN_NOT_OWNED):
        revoke_api_token(token=token, owner=other)

    def fail_audit(**kwargs: object) -> AuditEvent:
        raise RuntimeError("audit failed")

    monkeypatch.setattr("slaif_reservation.accounts.services.append_audit_event", fail_audit)
    with pytest.raises(RuntimeError):
        revoke_api_token(token=token, owner=owner)
    token.refresh_from_db()
    assert token.revoked_at is None


@pytest.mark.django_db
def test_record_api_token_use_is_monotonic_and_best_effort(monkeypatch: pytest.MonkeyPatch) -> None:
    owner = user()
    token = issue(owner).token
    first = timezone.now()
    record_api_token_use(token, used_at=first)
    token.refresh_from_db()
    assert token.last_used_at == first.astimezone(UTC)

    record_api_token_use(token, used_at=first - timedelta(hours=1))
    token.refresh_from_db()
    assert token.last_used_at == first.astimezone(UTC)

    def fail_save(*args: object, **kwargs: object) -> None:
        raise DatabaseError("write failed")

    monkeypatch.setattr(ApiToken, "save", fail_save)
    record_api_token_use(token, used_at=first + timedelta(hours=1))


@pytest.mark.django_db
def test_authenticator_accepts_valid_token_and_updates_last_used() -> None:
    owner = user()
    result = issue(owner)
    request = APIRequestFactory().get("/", HTTP_AUTHORIZATION=f"Bearer {result.bearer_token}")

    auth_result = ApiTokenAuthentication().authenticate(request)

    assert auth_result is not None
    auth_user, auth_token = auth_result
    assert auth_user == owner
    assert auth_token.id == result.token.id
    auth_token.refresh_from_db()
    assert auth_token.last_used_at is not None


@pytest.mark.django_db
@pytest.mark.parametrize("scheme", ["Bearer", "bearer", "bEaReR"])
def test_authenticator_accepts_bearer_scheme_case_insensitively(scheme: str) -> None:
    owner = user()
    result = issue(owner)
    request = APIRequestFactory().get("/", HTTP_AUTHORIZATION=f"{scheme} {result.bearer_token}")

    auth_result = ApiTokenAuthentication().authenticate(request)

    assert auth_result is not None
    assert auth_result[0] == owner


@pytest.mark.django_db
def test_authenticator_missing_and_non_bearer_are_ignored() -> None:
    auth = ApiTokenAuthentication()
    assert auth.authenticate(APIRequestFactory().get("/")) is None
    request = APIRequestFactory().get("/", HTTP_AUTHORIZATION="Basic abc")
    assert auth.authenticate(request) is None
    assert request.META["HTTP_AUTHORIZATION"] == "Basic abc"
    assert auth.authenticate_header(APIRequestFactory().get("/")) == "Bearer"


@pytest.mark.django_db
def test_authenticator_preserves_non_bearer_header_for_downstream_authenticator() -> None:
    request = APIRequestFactory().get("/", HTTP_AUTHORIZATION="Basic abc123")

    assert ApiTokenAuthentication().authenticate(request) is None

    class DownstreamAuthenticator:
        def authenticate(self, downstream_request) -> str:
            return str(downstream_request.META["HTTP_AUTHORIZATION"])

    assert DownstreamAuthenticator().authenticate(request) == "Basic abc123"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "header",
    [
        "Bearer",
        "Bearer ",
        "Bearer    ",
        "Bearer\t" + "sar_" + ("a" * 32) + "_" + "A" * 43,
        "Bearer malformed",
        "Bearer " + "sar_" + ("a" * 32) + "_" + "A" * 43 + " extra",
        "Bearer " + "x" * (MAX_AUTHORIZATION_HEADER_LENGTH + 1),
        "Bearer  " + "sar_" + ("a" * 32) + "_" + "A" * 43,
        "Bearer sar_" + ("a" * 32) + "_" + "A" * 43 + " ",
    ],
)
def test_authenticator_rejects_malformed_generically(header: str) -> None:
    with pytest.raises(AuthenticationFailed, match="Invalid bearer token"):
        ApiTokenAuthentication().authenticate(
            APIRequestFactory().get("/", HTTP_AUTHORIZATION=header)
        )


@pytest.mark.django_db
def test_malformed_bearer_exception_report_redacts_authorization() -> None:
    bearer = format_bearer_token(token_id=uuid.uuid4(), secret="F" * 43)
    header = f"Bearer {bearer} extra"
    request = APIRequestFactory().get("/", HTTP_AUTHORIZATION=header)
    try:
        ApiTokenAuthentication().authenticate(request)
    except AuthenticationFailed:
        report = ExceptionReporter(request, *sys.exc_info()).get_traceback_text()
    else:  # pragma: no cover - defensive
        raise AssertionError("malformed bearer authentication did not fail")

    assert request.META["HTTP_AUTHORIZATION"] == "Bearer [redacted]"
    assert_secret_absent(header, report)
    assert_secret_absent(bearer, report)
    assert_secret_absent("F" * 43, report)


@pytest.mark.django_db
def test_authenticator_failure_matrix_is_generic() -> None:
    owner = user()
    result = issue(owner)
    wrong_secret = format_bearer_token(token_id=result.token.id, secret="B" * 43)
    unknown_uuid = format_bearer_token(token_id=uuid.uuid4(), secret="C" * 43)
    cases = [wrong_secret, unknown_uuid]

    expired = token_row(owner, name="Expired", secret="G" * 43)
    set_token_timestamps(
        expired,
        created_at=timezone.now() - timedelta(days=2),
        expires_at=timezone.now() - timedelta(days=1),
    )
    cases.append(format_bearer_token(token_id=expired.id, secret="G" * 43))

    revoked = issue(owner, name="Revoked")
    revoke_api_token(token=revoked.token, owner=owner)
    cases.append(revoked.bearer_token)

    inactive_owner = user("inactive-owner@example.com")
    inactive = issue(inactive_owner)
    inactive_owner.is_active = False
    inactive_owner.save(update_fields=["is_active"])
    cases.append(inactive.bearer_token)

    service_owner = user("service-owner@example.com")
    service = issue(service_owner)
    service_owner.is_service_account = True
    service_owner.save(update_fields=["is_service_account"])
    cases.append(service.bearer_token)

    auth = ApiTokenAuthentication()
    for bearer in cases:
        with pytest.raises(AuthenticationFailed, match="Invalid bearer token"):
            auth.authenticate(APIRequestFactory().get("/", HTTP_AUTHORIZATION=f"Bearer {bearer}"))
    result.token.refresh_from_db()
    assert result.token.last_used_at is None


@pytest.mark.django_db
def test_authenticator_exact_expiry_boundary_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    owner = user()
    result = issue(owner)
    token = result.token
    monkeypatch.setattr(
        "slaif_reservation.api.authentication.timezone.now", lambda: token.expires_at
    )

    with pytest.raises(AuthenticationFailed, match="Invalid bearer token"):
        ApiTokenAuthentication().authenticate(
            APIRequestFactory().get("/", HTTP_AUTHORIZATION=f"Bearer {result.bearer_token}")
        )

    token.refresh_from_db()
    assert token.last_used_at is None


@pytest.mark.django_db
def test_authenticator_last_use_failure_does_not_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    owner = user()
    result = issue(owner)

    def fail_record(*args: object, **kwargs: object) -> None:
        raise DatabaseError("last-use failed")

    monkeypatch.setattr("slaif_reservation.api.authentication.record_api_token_use", fail_record)
    request = APIRequestFactory().get("/", HTTP_AUTHORIZATION=f"Bearer {result.bearer_token}")
    assert ApiTokenAuthentication().authenticate(request) is not None


@pytest.mark.django_db
def test_authentication_logs_do_not_contain_secrets(caplog: pytest.LogCaptureFixture) -> None:
    owner = user()
    result = issue(owner)
    secret = result.bearer_token.rsplit("_", 1)[1]
    with caplog.at_level(logging.INFO):
        ApiTokenAuthentication().authenticate(
            APIRequestFactory().get("/", HTTP_AUTHORIZATION=f"Bearer {result.bearer_token}")
        )
        with pytest.raises(AuthenticationFailed):
            ApiTokenAuthentication().authenticate(
                APIRequestFactory().get(
                    "/",
                    HTTP_AUTHORIZATION=(
                        f"Bearer {format_bearer_token(token_id=result.token.id, secret='B' * 43)}"
                    ),
                )
            )
    logs = "\n".join(record.getMessage() for record in caplog.records)
    assert_secret_absent(result.bearer_token, logs)
    assert_secret_absent(secret, logs)
    assert_secret_absent(result.token.verifier, logs)
    assert "test-only-api-token-pepper" not in logs


@pytest.mark.django_db
def test_authentication_exception_report_redacts_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner = user()
    result = issue(owner)
    secret = result.bearer_token.rsplit("_", 1)[1]

    def fail_record(*args: object, **kwargs: object) -> None:
        raise RuntimeError("synthetic auth failure")

    monkeypatch.setattr("slaif_reservation.api.authentication.record_api_token_use", fail_record)
    request = APIRequestFactory().get("/", HTTP_AUTHORIZATION=f"Bearer {result.bearer_token}")
    try:
        ApiTokenAuthentication().authenticate(request)
    except RuntimeError:
        report = ExceptionReporter(request, *sys.exc_info()).get_traceback_text()
    else:  # pragma: no cover - defensive
        raise AssertionError("synthetic authentication failure did not occur")

    assert_secret_absent(result.bearer_token, report)
    assert_secret_absent(secret, report)
    assert_secret_absent(result.token.verifier, report)
    assert_secret_absent("test-only-api-token-pepper", report)
    assert_secret_absent(f"Bearer {result.bearer_token}", report)


@sensitive_variables("secret")
def test_format_bearer_token_exception_report_redacts_secret() -> None:
    secret = "H" * 43

    class BrokenTokenId:
        @property
        def hex(self) -> str:
            raise RuntimeError("synthetic format failure")

    try:
        format_bearer_token(token_id=BrokenTokenId(), secret=secret)  # type: ignore[arg-type]
    except RuntimeError:
        report = ExceptionReporter(None, *sys.exc_info()).get_traceback_text()
    else:  # pragma: no cover - defensive
        raise AssertionError("synthetic token formatting failure did not occur")

    assert_secret_absent(secret, report)


@sensitive_variables("bearer", "secret", "pepper")
def test_verifier_exception_report_redacts_credential_and_pepper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bearer = format_bearer_token(token_id=uuid.uuid4(), secret="I" * 43)
    secret = bearer.rsplit("_", 1)[1]
    pepper = TEST_API_TOKEN_PEPPER

    def fail_hmac(*args: object, **kwargs: object) -> object:
        raise RuntimeError("synthetic verifier failure")

    monkeypatch.setattr("slaif_reservation.accounts.tokens.hmac.new", fail_hmac)

    try:
        api_token_verifier(bearer_token=bearer, pepper=pepper)
    except RuntimeError:
        report = ExceptionReporter(None, *sys.exc_info()).get_traceback_text()
    else:  # pragma: no cover - defensive
        raise AssertionError("synthetic verifier failure did not occur")

    assert_secret_absent(bearer, report)
    assert_secret_absent(secret, report)
    assert_secret_absent(pepper, report)


@pytest.mark.django_db
@sensitive_variables("captured")
def test_token_created_template_exception_report_redacts_plaintext(
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner = user()
    client.force_login(owner)
    captured: dict[str, str] = {}
    real_issue = issue_api_token

    def capture_issue(**kwargs: object):
        result = real_issue(**kwargs)
        captured["bearer"] = result.bearer_token
        captured["secret"] = result.bearer_token.rsplit("_", 1)[1]
        return result

    def fail_time_render(*args: object, **kwargs: object) -> str:
        raise RuntimeError("synthetic template rendering failure")

    monkeypatch.setattr("slaif_reservation.web.views.issue_api_token", capture_issue)
    monkeypatch.setattr(
        "slaif_reservation.web.templatetags.web_time.require_aware_utc",
        fail_time_render,
    )

    try:
        client.post(
            "/tokens/new/",
            {"name": "Render fail", "scopes": ["assets:read"], "lifetime_days": "30"},
        )
    except RuntimeError:
        report = ExceptionReporter(None, *sys.exc_info()).get_traceback_text()
    else:  # pragma: no cover - defensive
        raise AssertionError("synthetic template rendering failure did not occur")

    assert ApiToken.objects.count() == 1
    assert_secret_absent(captured["bearer"], report)
    assert_secret_absent(captured["secret"], report)
    assert_secret_absent(ApiToken.objects.get().verifier, report)
    assert_secret_absent(TEST_API_TOKEN_PEPPER, report)


@pytest.mark.django_db
def test_bearer_token_does_not_access_staff_asset_api(client) -> None:
    owner = user()
    result = issue(owner)
    Asset.objects.create(slug="api-asset", name="API Asset", kind=Asset.KIND_GPU)

    response = client.get("/api/v1/assets/", HTTP_AUTHORIZATION=f"Bearer {result.bearer_token}")

    assert response.status_code == 403


@pytest.mark.django_db
def test_audit_metadata_rejects_nested_token_secret_material() -> None:
    token_id = uuid.uuid4()
    bearer = format_bearer_token(token_id=token_id, secret="D" * 43)
    safe_metadata = {
        "display_prefix": display_prefix_for_token_id(token_id),
        "scopes": ["assets:read"],
        "expires_at": timezone.now().isoformat(),
    }
    validate_audit_metadata(safe_metadata)

    forbidden_values = [
        {"nested": [{"Secret": "value"}]},
        {"nested": {"Verifier": "value"}},
        {"nested": [{"PEPPER": "value"}]},
        {"nested": {"bearer-token": "value"}},
        {"nested": {"api token plaintext": "value"}},
        {"safe": bearer},
        {"nested": [{"safe": f"created {bearer}"}]},
    ]
    for metadata in forbidden_values:
        with pytest.raises(ValidationError):
            validate_audit_metadata(metadata)


@pytest.mark.django_db(transaction=True)
def test_append_audit_event_rejects_prohibited_token_metadata() -> None:
    owner = user()
    bearer = format_bearer_token(token_id=uuid.uuid4(), secret="E" * 43)

    with pytest.raises(ValidationError):
        append_audit_event(
            action=AuditEvent.ACTION_API_TOKEN_CREATED,
            target_type="api_token",
            target_id=uuid.uuid4(),
            correlation_id=uuid.uuid4(),
            source=AuditEvent.SOURCE_WEB,
            actor_user=owner,
            metadata={"safe_container": [{"innocuous": bearer}]},
        )

    assert AuditEvent.objects.count() == 0


@pytest.mark.django_db
def test_token_web_lifecycle_one_time_display_and_redaction(client: Client) -> None:
    owner = user()
    client.force_login(owner)
    response = client.post(
        "/tokens/new/",
        {
            "name": "<script>alert(1)</script>",
            "scopes": ["assets:read", "reservations:create"],
            "lifetime_days": "30",
        },
    )
    assert response.status_code == 200
    assert response["Cache-Control"] == "no-store, private"
    assert response["Pragma"] == "no-cache"
    assert response["Referrer-Policy"] == "no-referrer"
    token = ApiToken.objects.get()
    content = response.content.decode()
    bearer = extract_bearer_from_html(content)
    assert bearer.startswith(f"sar_{token.id.hex}_")
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in content
    assert_secret_absent(token.verifier, content)

    session_payload = str(dict(client.session.items()))
    message_payload = " ".join(str(message) for message in get_messages(response.wsgi_request))
    list_response = client.get("/tokens/")
    assert_secret_absent(bearer, session_payload)
    assert_secret_absent(bearer, message_payload)
    assert_secret_absent(bearer, list_response.content.decode())
    assert_secret_absent(token.verifier, list_response.content.decode())
    assert token.display_prefix in list_response.content.decode()


@pytest.mark.django_db
@override_settings(API_TOKEN_MAX_LIFETIME_DAYS=7)
def test_token_creation_form_enforces_configured_lifetime_boundary(client: Client) -> None:
    owner = user()
    client.force_login(owner)
    form_response = client.get("/tokens/new/")
    assert form_response.status_code == 200
    assert 'max="7"' in form_response.content.decode()
    assert 'value="7"' in form_response.content.decode()

    valid_response = client.post(
        "/tokens/new/",
        {"name": "Seven", "scopes": ["assets:read"], "lifetime_days": "7"},
    )
    assert valid_response.status_code == 200
    assert ApiToken.objects.count() == 1
    assert AuditEvent.objects.count() == 1

    for lifetime in ["8", "0"]:
        token_count = ApiToken.objects.count()
        audit_count = AuditEvent.objects.count()
        response = client.post(
            "/tokens/new/",
            {"name": "Invalid", "scopes": ["assets:read"], "lifetime_days": lifetime},
        )
        assert response.status_code == 200
        assert "lifetime_days" in response.context["form"].errors
        assert ApiToken.objects.count() == token_count
        assert AuditEvent.objects.count() == audit_count


@pytest.mark.django_db
def test_token_routes_are_active_human_owner_only_and_csrf_protected(
    client: Client,
    django_user_model,
) -> None:
    owner = user()
    other = user("other-token@example.com")
    token = issue(owner).token

    assert client.get("/tokens/").status_code == 302
    client.force_login(other)
    assert client.post(f"/tokens/{token.id}/revoke/").status_code == 404
    token.refresh_from_db()
    assert token.revoked_at is None
    assert client.get(f"/tokens/{token.id}/revoke/").status_code == 405

    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(owner)
    assert csrf_client.post("/tokens/new/", {"name": "x"}).status_code == 403
    assert csrf_client.post(f"/tokens/{token.id}/revoke/").status_code == 403


@pytest.mark.django_db
def test_api_token_admin_is_metadata_only(rf) -> None:
    owner = user()
    token = issue(owner).token
    admin = ApiTokenAdmin(ApiToken, site)
    request = rf.get("/admin/accounts/apitoken/")
    request.user = user("admin@example.com", is_staff=True, is_superuser=True)

    assert not admin.has_add_permission(request)
    assert not admin.has_change_permission(request, token)
    assert not admin.has_delete_permission(request, token)
    assert "verifier" not in admin.get_fields(request, token)
    assert "delete_selected" not in admin.get_actions(request)


@pytest.mark.django_db
def test_api_token_admin_response_does_not_render_verifier(client: Client) -> None:
    owner = user()
    result = issue(owner)
    admin_user = user("admin-response@example.com", is_staff=True, is_superuser=True)
    client.force_login(admin_user)

    response = client.get("/admin/accounts/apitoken/")

    assert response.status_code == 200
    content = response.content.decode()
    assert result.token.display_prefix in content
    assert_secret_absent(result.token.verifier, content)
    assert_secret_absent(result.bearer_token, content)


def test_api_token_production_setting_fail_fast() -> None:
    import subprocess
    import sys
    import textwrap

    clean_env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("SLAIF_") and key not in {"DATABASE_URL", "DJANGO_SETTINGS_MODULE"}
    } | {"PYTHONPATH": "src"}
    base_env = clean_env | {
        "DJANGO_SETTINGS_MODULE": "slaif_reservation.config.settings.production",
        "SLAIF_DJANGO_SECRET_KEY": "production-secret-key-with-enough-length",
        "SLAIF_ALLOWED_HOSTS": "reservation.example.test",
        "SLAIF_CSRF_TRUSTED_ORIGINS": "https://reservation.example.test",
        "SLAIF_TRUSTED_PROXY_PEERS": "127.0.0.1",
        "DATABASE_URL": "postgres://slaif:slaif@localhost:5432/slaif_reservation",
    }

    invalid_peppers = [
        None,
        "short",
        base_env["SLAIF_DJANGO_SECRET_KEY"],
        DEVELOPMENT_API_TOKEN_PEPPER,
        TEST_API_TOKEN_PEPPER,
        f"  {DEVELOPMENT_API_TOKEN_PEPPER}\n",
        f"\t{TEST_API_TOKEN_PEPPER}  ",
    ]
    for pepper in invalid_peppers:
        env = dict(base_env)
        if pepper is not None:
            env["SLAIF_API_TOKEN_PEPPER"] = pepper
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import django; django.setup()",
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        if pepper is not None:
            assert_secret_absent(str(pepper).strip(), result.stderr)

    env = base_env | {"SLAIF_API_TOKEN_PEPPER": "valid-production-pepper-" + ("x" * 32)}
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            textwrap.dedent(
                """
                import django
                django.setup()
                from django.conf import settings
                print(settings.API_TOKEN_MAX_LIFETIME_DAYS)
                """
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    for value in ["0", "-1", "bad", "366"]:
        result = subprocess.run(
            [sys.executable, "-c", "import django; django.setup()"],
            env=env | {"SLAIF_API_TOKEN_MAX_LIFETIME_DAYS": value},
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0


@pytest.mark.django_db
def test_no_token_lifecycle_routes_in_openapi_root(client) -> None:
    response = client.get("/api/v1/")
    assert response.status_code == 200
    assert "tokens" not in response.json()["endpoints"]
    assert "reservations" in response.json()["endpoints"]
    assert client.get("/api/v1/me/").status_code == 401
    assert client.get("/api/v1/tokens/").status_code == 404
