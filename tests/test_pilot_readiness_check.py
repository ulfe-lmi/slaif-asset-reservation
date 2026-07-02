from __future__ import annotations

import json
from datetime import timedelta
from io import StringIO
from uuid import uuid4

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from slaif_reservation.accounts.models import ApiToken, User
from slaif_reservation.accounts.services import issue_api_token
from slaif_reservation.api.models import IdempotencyRecord
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.reservations.models import (
    MaintenanceBlackout,
    Reservation,
    ReservationPolicy,
)


def user(email: str, **overrides: object) -> User:
    return User.objects.create_user(email=email, password="not-a-secret", **overrides)


def asset(slug: str = "pilot-gpu", **overrides: object) -> Asset:
    values = {
        "slug": slug,
        "name": slug.replace("-", " ").title(),
        "kind": Asset.KIND_GPU,
        "active": True,
        "reservable": True,
        "verification_required": False,
    }
    values.update(overrides)
    return Asset.objects.create(**values)


def policy(target: Asset | None = None, **overrides: object) -> ReservationPolicy:
    values = {
        "name": "Pilot readiness policy",
        "asset": target,
        "min_duration_minutes": 15,
        "max_duration_minutes": 240,
        "booking_horizon_days": 30,
        "min_lead_minutes": 0,
        "cancellation_cutoff_minutes": 0,
        "max_upcoming_per_principal": 20,
        "max_concurrent_per_principal": 5,
        "purpose_required": False,
    }
    values.update(overrides)
    return ReservationPolicy.objects.create(**values)


def audit_event(action: str = AuditEvent.ACTION_BLACKOUT_CREATED) -> AuditEvent:
    return AuditEvent.objects.create(
        occurred_at=timezone.now(),
        actor_user=None,
        action=action,
        target_type="pilot_readiness",
        target_id=uuid4(),
        correlation_id=uuid4(),
        source=AuditEvent.SOURCE_ADMIN,
        metadata={"summary": "safe pilot readiness test event"},
    )


def minimal_ready_state() -> None:
    user("pilot-staff@example.com", is_staff=True)
    user("pilot-member@example.com")
    target = asset()
    policy(target)
    audit_event()


def run_json_command(*args: str) -> dict[str, object]:
    output = StringIO()
    call_command("pilot_readiness_check", "--json", *args, stdout=output)
    return json.loads(output.getvalue())


@pytest.mark.django_db
def test_pilot_readiness_empty_database_strict_failure_and_non_strict_success() -> None:
    non_strict_output = StringIO()

    call_command("pilot_readiness_check", stdout=non_strict_output)

    rendered = non_strict_output.getvalue()
    assert "pilot_readiness=fail" in rendered
    assert "FAIL active_staff_user" in rendered
    assert "FAIL active_reservable_exclusive_asset" in rendered
    assert "FAIL active_reservation_policy" in rendered

    with pytest.raises(CommandError, match="pilot readiness check failed"):
        call_command("pilot_readiness_check", "--strict", stdout=StringIO(), stderr=StringIO())


@pytest.mark.django_db
def test_pilot_readiness_minimal_ready_state_passes_strict() -> None:
    minimal_ready_state()
    output = StringIO()

    call_command("pilot_readiness_check", "--strict", stdout=output)

    rendered = output.getvalue()
    assert "pilot_readiness=pass" in rendered
    assert "FAIL" not in rendered
    assert "WARN" not in rendered


@pytest.mark.django_db
def test_pilot_readiness_assets_without_effective_policy_warn_but_do_not_fail_strict() -> None:
    user("policy-staff@example.com", is_staff=True)
    user("policy-member@example.com")
    covered = asset("covered-gpu")
    policy(covered)
    asset("uncovered-gpu")
    audit_event()
    output = StringIO()

    call_command("pilot_readiness_check", "--strict", stdout=output)

    rendered = output.getvalue()
    assert "pilot_readiness=warn" in rendered
    assert "WARN assets_without_effective_policy" in rendered
    assert "1 active reservable exclusive asset(s) lack an effective policy" in rendered


@pytest.mark.django_db
def test_pilot_readiness_json_schema_counts_and_redaction() -> None:
    minimal_ready_state()
    owner = User.objects.get(email="pilot-member@example.com")
    issue_result = issue_api_token(
        owner=owner,
        name="Pilot readiness token",
        scopes=["reservations:read"],
        lifetime_days=1,
    )
    secret_bearer = issue_result.bearer_token

    payload = run_json_command()

    assert payload["schema_version"] == 1
    assert payload["status"] == "pass"
    assert payload["counts"]["api_tokens_present"] == 1
    assert payload["counts"]["api_tokens_active"] == 1
    assert payload["counts"]["api_tokens_expired"] == 0
    assert payload["counts"]["api_tokens_revoked"] == 0
    check_ids = [item["id"] for item in payload["checks"]]
    assert check_ids == sorted(check_ids)
    rendered = json.dumps(payload, sort_keys=True)
    assert secret_bearer not in rendered
    assert ApiToken.objects.get().verifier not in rendered
    assert "Authorization" not in rendered
    assert "purpose" not in rendered
    assert "physical_locator" not in rendered


@pytest.mark.django_db
def test_pilot_readiness_reports_expired_idempotency_warning() -> None:
    minimal_ready_state()
    owner = User.objects.get(email="pilot-member@example.com")
    token = issue_api_token(
        owner=owner,
        name="Pilot readiness token",
        scopes=["reservations:create"],
        lifetime_days=1,
    ).token
    IdempotencyRecord.objects.create(
        owner=owner,
        api_token=token,
        action="reservations:create",
        idempotency_key="pilot-readiness-key",
        canonical_request_hash="0" * 64,
        request_method="POST",
        request_path="/api/v1/reservations/",
        response_status=201,
        response_body={"ok": True},
        target_type="reservation",
        target_id=uuid4(),
        correlation_id=uuid4(),
        expires_at=timezone.now() - timedelta(hours=1),
    )

    payload = run_json_command()

    assert payload["status"] == "warn"
    assert payload["counts"]["expired_idempotency_records"] == 1
    expired_check = next(
        item for item in payload["checks"] if item["id"] == "expired_idempotency_records"
    )
    assert expired_check["level"] == "warn"


@pytest.mark.django_db
def test_pilot_readiness_command_is_read_only_for_application_tables() -> None:
    minimal_ready_state()
    owner = User.objects.get(email="pilot-member@example.com")
    issue_api_token(
        owner=owner,
        name="Pilot readiness token",
        scopes=["reservations:read"],
        lifetime_days=1,
    )
    models = [
        User,
        ApiToken,
        Asset,
        ReservationPolicy,
        MaintenanceBlackout,
        Reservation,
        AuditEvent,
        IdempotencyRecord,
    ]
    before = {model.__name__: model.objects.count() for model in models}

    call_command("pilot_readiness_check", "--json", stdout=StringIO())

    after = {model.__name__: model.objects.count() for model in models}
    assert after == before


@pytest.mark.django_db
def test_pilot_readiness_migration_failure_is_a_hard_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    import slaif_reservation.api.management.commands.pilot_readiness_check as command_module

    minimal_ready_state()
    monkeypatch.setattr(command_module, "unapplied_migrations_exist", lambda: True)

    payload = run_json_command()

    assert payload["status"] == "fail"
    migration_check = next(
        item for item in payload["checks"] if item["id"] == "database_migration_ready"
    )
    assert migration_check["level"] == "fail"
    with pytest.raises(CommandError, match="pilot readiness check failed"):
        call_command("pilot_readiness_check", "--strict", stdout=StringIO(), stderr=StringIO())
