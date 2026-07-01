from __future__ import annotations

import json
import logging
from datetime import timedelta
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import RequestFactory, override_settings
from django.utils import timezone

from slaif_reservation.accounts.models import User
from slaif_reservation.accounts.services import issue_api_token
from slaif_reservation.api.models import IdempotencyRecord
from slaif_reservation.config.logging import JsonLogFormatter
from slaif_reservation.config.middleware import SafeRequestLogMiddleware


def user(email: str = "ops-member@example.com") -> User:
    return User.objects.create_user(email=email, password="not-a-secret")


def token_for(owner: User):
    return issue_api_token(
        owner=owner,
        name="Operations test token",
        scopes=["reservations:read"],
        lifetime_days=1,
    ).token


def idempotency_record(*, owner: User, expires_at: timezone.datetime) -> IdempotencyRecord:
    api_token = token_for(owner)
    return IdempotencyRecord.objects.create(
        owner=owner,
        api_token=api_token,
        action="reservations:create",
        idempotency_key=f"ops-key-{IdempotencyRecord.objects.count():04d}",
        canonical_request_hash="0" * 64,
        request_method="POST",
        request_path="/api/v1/reservations/",
        response_status=201,
        response_body={"ok": True},
        target_type="reservation",
        correlation_id=timezone.now()
        .date()
        .replace(year=2026)
        .strftime("00000000-0000-4000-8000-%m%d00000000"),
        expires_at=expires_at,
    )


def test_json_log_formatter_redacts_secret_fields(settings) -> None:
    settings.API_TOKEN_PEPPER = "test-pepper-value-that-must-not-log"
    record = logging.makeLogRecord(
        {
            "name": "slaif_reservation.test",
            "levelno": logging.INFO,
            "levelname": "INFO",
            "msg": (
                "Authorization: Bearer "
                "sar_0123456789abcdef0123456789abcdef_secretsecretsecretsecretsecret12"
            ),
            "authorization": "Bearer not-for-logs",
            "cookie": "sessionid=not-for-logs",
            "pepper": settings.API_TOKEN_PEPPER,
            "path": "/api/v1/me/",
            "status_code": 401,
        }
    )

    payload = json.loads(JsonLogFormatter().format(record))

    rendered = json.dumps(payload)
    assert "sar_0123456789abcdef0123456789abcdef" not in rendered
    assert "not-for-logs" not in rendered
    assert settings.API_TOKEN_PEPPER not in rendered
    assert payload["authorization"] == "[redacted]"
    assert payload["cookie"] == "[redacted]"
    assert payload["pepper"] == "[redacted]"
    assert payload["path"] == "/api/v1/me/"
    assert payload["status_code"] == 401


def test_request_logging_middleware_emits_safe_fields_without_headers_or_body(caplog) -> None:
    request = RequestFactory().post(
        "/api/v1/reservations/",
        data='{"purpose":"private"}',
        content_type="application/json",
        HTTP_AUTHORIZATION="Bearer not-for-logs",
        HTTP_X_REQUEST_ID="2bb51aa8-c66b-4b09-9534-31ac1e17e1d1",
    )

    def app(_request):
        from django.http import JsonResponse

        return JsonResponse({"ok": True}, status=202)

    caplog.set_level(logging.INFO, logger="slaif_reservation.request")
    response = SafeRequestLogMiddleware(app)(request)

    assert response.status_code == 202
    [record] = [item for item in caplog.records if item.name == "slaif_reservation.request"]
    assert record.path == "/api/v1/reservations/"
    assert record.method == "POST"
    assert record.status_code == 202
    assert record.request_id == "2bb51aa8-c66b-4b09-9534-31ac1e17e1d1"
    assert "not-for-logs" not in record.getMessage()
    assert "private" not in record.getMessage()


@pytest.mark.django_db
def test_operational_check_success() -> None:
    output = StringIO()

    call_command("operational_check", stdout=output)

    rendered = output.getvalue()
    assert "database=ok" in rendered
    assert "migrations=ok" in rendered
    assert "static=ok" in rendered
    assert "bootstrap=ok" in rendered
    assert "idempotency_cleanup_command=ok" in rendered
    assert "operational_check=ok" in rendered


@pytest.mark.django_db
def test_operational_check_reports_static_failure(monkeypatch) -> None:
    import slaif_reservation.api.management.commands.operational_check as command_module

    monkeypatch.setattr(command_module, "missing_static_assets", lambda: ["web/site.css"])

    with pytest.raises(CommandError, match="operational check failed"):
        call_command("operational_check", stdout=StringIO(), stderr=StringIO())


@pytest.mark.django_db
def test_purge_expired_idempotency_records_dry_run_and_apply() -> None:
    owner = user()
    expired = idempotency_record(owner=owner, expires_at=timezone.now() - timedelta(hours=1))
    active = idempotency_record(owner=owner, expires_at=timezone.now() + timedelta(hours=1))

    dry_run_output = StringIO()
    call_command("purge_expired_idempotency_records", stdout=dry_run_output)

    assert "mode=dry-run" in dry_run_output.getvalue()
    assert "expired=1" in dry_run_output.getvalue()
    assert IdempotencyRecord.objects.filter(id=expired.id).exists()
    assert IdempotencyRecord.objects.filter(id=active.id).exists()

    apply_output = StringIO()
    call_command(
        "purge_expired_idempotency_records",
        "--apply",
        "--batch-size",
        "1",
        stdout=apply_output,
    )

    assert "mode=apply" in apply_output.getvalue()
    assert "deleted=1" in apply_output.getvalue()
    assert not IdempotencyRecord.objects.filter(id=expired.id).exists()
    assert IdempotencyRecord.objects.filter(id=active.id).exists()


def test_purge_expired_idempotency_records_rejects_invalid_batch_size() -> None:
    with pytest.raises(CommandError, match="batch_size must be at least 1"):
        call_command("purge_expired_idempotency_records", "--batch-size", "0", stdout=StringIO())


def test_backup_database_refuses_missing_database_url(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(CommandError, match="DATABASE_URL is required"):
        call_command(
            "backup_database",
            "--output",
            str(tmp_path / "backup.dump"),
            stdout=StringIO(),
        )


def test_backup_database_dry_run_does_not_print_password(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgres://slaif:super-secret-password@localhost:5432/slaif_reservation",
    )
    output = StringIO()

    call_command("backup_database", "--output", str(tmp_path / "backup.dump"), stdout=output)

    rendered = output.getvalue()
    assert "mode=dry-run" in rendered
    assert "validated=true" in rendered
    assert "super-secret-password" not in rendered


def test_restore_database_refuses_missing_database_url(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    artifact = tmp_path / "backup.dump"
    artifact.write_bytes(b"not-a-real-backup")

    with pytest.raises(CommandError, match="DATABASE_URL is required"):
        call_command("restore_database", "--input", str(artifact), stdout=StringIO())


def test_restore_database_dry_run_does_not_print_password(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgres://slaif:super-secret-password@localhost:5432/slaif_reservation",
    )
    artifact = tmp_path / "backup.dump"
    artifact.write_bytes(b"not-a-real-backup")
    output = StringIO()

    call_command("restore_database", "--input", str(artifact), stdout=output)

    rendered = output.getvalue()
    assert "mode=dry-run" in rendered
    assert "validated=true" in rendered
    assert "super-secret-password" not in rendered


@override_settings(
    LOGGING={
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"json": {"()": "slaif_reservation.config.logging.JsonLogFormatter"}},
        "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
        "root": {"handlers": ["console"], "level": "INFO"},
    }
)
def test_production_json_logging_configuration_loads(settings) -> None:
    assert settings.LOGGING["formatters"]["json"]["()"] == (
        "slaif_reservation.config.logging.JsonLogFormatter"
    )
