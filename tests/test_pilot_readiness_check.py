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
    from django.contrib.auth.models import Permission

    minimal_ready_state()
    owner = User.objects.get(email="pilot-member@example.com")
    # 051-a: creating a create-scope token now requires the owner's current
    # booking capability; grant it explicitly for this fixture only (the
    # readiness command logic itself is unchanged).
    owner.user_permissions.add(
        Permission.objects.get(codename="book_assets", content_type__app_label="reservations")
    )
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


# 019-a boundary tests: pin the failure boundaries the seven pre-existing
# tests do not cover. Each test isolates exactly one boundary and asserts the
# rest of the report stays clean.
@pytest.mark.django_db
def test_pilot_readiness_database_connection_failure_is_a_hard_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from django.db import OperationalError

    import slaif_reservation.api.management.commands.pilot_readiness_check as command_module

    class FailingConnection:
        def ensure_connection(self, *args: object, **kwargs: object) -> None:
            raise OperationalError("synthetic connection failure")

    minimal_ready_state()
    monkeypatch.setattr(command_module, "connection", FailingConnection())

    payload = run_json_command()

    assert payload["status"] == "fail"
    migration_check = next(
        item for item in payload["checks"] if item["id"] == "database_migration_ready"
    )
    assert migration_check["level"] == "fail"
    for item in payload["checks"]:
        if item["id"] != "database_migration_ready":
            assert item["level"] != "fail"
    with pytest.raises(CommandError, match="pilot readiness check failed"):
        call_command("pilot_readiness_check", "--strict", stdout=StringIO(), stderr=StringIO())


@pytest.mark.django_db
def test_pilot_readiness_service_account_staff_cannot_satisfy_human_staff_gate() -> None:
    user("service-staff@example.com", is_staff=True, is_service_account=True)
    target = asset()
    policy(target)
    audit_event()

    payload = run_json_command()

    assert payload["status"] == "fail"
    assert payload["counts"]["active_staff_users"] == 0
    staff_check = next(item for item in payload["checks"] if item["id"] == "active_staff_user")
    assert staff_check["level"] == "fail"
    for item in payload["checks"]:
        if item["id"] != "active_staff_user":
            assert item["level"] != "fail"


@pytest.mark.django_db
def test_pilot_readiness_non_staff_service_account_is_no_human_user() -> None:
    user("service-member@example.com", is_service_account=True)

    payload = run_json_command()

    assert payload["counts"]["active_human_users"] == 0
    ordinary_check = next(
        item for item in payload["checks"] if item["id"] == "ordinary_pilot_users"
    )
    assert ordinary_check["level"] == "warn"


@pytest.mark.django_db
def test_pilot_readiness_inactive_staff_user_fails_human_staff_gate() -> None:
    user("inactive-staff@example.com", is_staff=True, is_active=False)
    target = asset()
    policy(target)
    audit_event()

    payload = run_json_command()

    assert payload["status"] == "fail"
    assert payload["counts"]["active_staff_users"] == 0
    staff_check = next(item for item in payload["checks"] if item["id"] == "active_staff_user")
    assert staff_check["level"] == "fail"
    for item in payload["checks"]:
        if item["id"] != "active_staff_user":
            assert item["level"] != "fail"


@pytest.mark.django_db
def test_pilot_readiness_inactive_or_non_reservable_asset_fails_asset_gate() -> None:
    user("asset-staff@example.com", is_staff=True)
    user("asset-member@example.com")
    asset("inactive-gpu", active=False, reservable=False)
    asset("locked-gpu", reservable=False)
    policy()
    audit_event()

    payload = run_json_command()

    assert payload["status"] == "fail"
    assert payload["counts"]["active_reservable_exclusive_assets"] == 0
    asset_check = next(
        item for item in payload["checks"] if item["id"] == "active_reservable_exclusive_asset"
    )
    assert asset_check["level"] == "fail"
    for item in payload["checks"]:
        if item["id"] != "active_reservable_exclusive_asset":
            assert item["level"] != "fail"


@pytest.mark.django_db
def test_pilot_readiness_inactive_policy_fails_policy_gate() -> None:
    user("policy-staff@example.com", is_staff=True)
    user("policy-member@example.com")
    target = asset()
    policy(target, active=False)
    audit_event()

    payload = run_json_command()

    assert payload["status"] == "fail"
    assert payload["counts"]["active_reservation_policies"] == 0
    policy_check = next(
        item for item in payload["checks"] if item["id"] == "active_reservation_policy"
    )
    assert policy_check["level"] == "fail"
    for item in payload["checks"]:
        if item["id"] != "active_reservation_policy":
            assert item["level"] != "fail"


@pytest.mark.django_db
def test_pilot_readiness_blackout_deactivation_is_not_exercise_evidence() -> None:
    user("blackout-staff@example.com", is_staff=True)
    user("blackout-member@example.com")
    target = asset()
    policy(target)
    audit_event(action=AuditEvent.ACTION_BLACKOUT_DEACTIVATED)

    payload = run_json_command()

    assert payload["counts"]["successful_blackout_audit_events"] == 0
    exercise_check = next(
        item for item in payload["checks"] if item["id"] == "successful_blackout_exercise"
    )
    assert exercise_check["level"] == "warn"
    assert payload["counts"]["recent_audit_events"] == 1
    recent_check = next(item for item in payload["checks"] if item["id"] == "recent_audit_events")
    assert recent_check["level"] == "pass"


@pytest.mark.django_db
def test_pilot_readiness_old_blackout_event_expires_from_recent_window_only() -> None:
    user("window-staff@example.com", is_staff=True)
    user("window-member@example.com")
    target = asset()
    policy(target)
    AuditEvent.objects.create(
        occurred_at=timezone.now() - timedelta(days=8),
        actor_user=None,
        action=AuditEvent.ACTION_BLACKOUT_CREATED,
        target_type="pilot_readiness",
        target_id=uuid4(),
        correlation_id=uuid4(),
        source=AuditEvent.SOURCE_ADMIN,
        metadata={"summary": "safe pilot readiness boundary event"},
    )

    payload = run_json_command()

    assert payload["counts"]["recent_audit_events"] == 0
    recent_check = next(item for item in payload["checks"] if item["id"] == "recent_audit_events")
    assert recent_check["level"] == "warn"
    assert payload["counts"]["successful_blackout_audit_events"] == 1
    exercise_check = next(
        item for item in payload["checks"] if item["id"] == "successful_blackout_exercise"
    )
    assert exercise_check["level"] == "pass"
    assert payload["status"] == "warn"


@pytest.mark.django_db
def test_pilot_readiness_token_buckets_partition_and_do_not_gate_status() -> None:
    from django.db import connection

    from slaif_reservation.accounts.services import revoke_api_token

    minimal_ready_state()
    owner = User.objects.get(email="pilot-member@example.com")
    issue_api_token(
        owner=owner, name="Boundary active token", scopes=["reservations:read"], lifetime_days=7
    )
    expired_token = issue_api_token(
        owner=owner, name="Boundary expired token", scopes=["reservations:read"], lifetime_days=1
    ).token
    revoked_token = issue_api_token(
        owner=owner, name="Boundary revoked token", scopes=["reservations:read"], lifetime_days=7
    ).token
    # Age the expired token with the same raw-SQL pattern the token suite uses
    # (set_token_timestamps): the api_token_expires_after_created constraint
    # forbids an ORM save with expires_at before created_at.
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE accounts_apitoken
               SET created_at = %s,
                   expires_at = %s
             WHERE id = %s
            """,
            [
                timezone.now() - timedelta(days=3),
                timezone.now() - timedelta(days=2),
                expired_token.id,
            ],
        )
    revoke_api_token(token=revoked_token, owner=owner)

    payload = run_json_command()

    assert payload["counts"]["api_tokens_present"] == 3
    assert payload["counts"]["api_tokens_active"] == 1
    assert payload["counts"]["api_tokens_expired"] == 1
    assert payload["counts"]["api_tokens_revoked"] == 1
    assert payload["status"] == "pass"
    for item in payload["checks"]:
        assert item["level"] == "pass"


@pytest.mark.django_db
def test_pilot_readiness_ambiguous_policy_counts_as_uncovered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import slaif_reservation.api.management.commands.pilot_readiness_check as command_module
    from slaif_reservation.reservations.exceptions import (
        POLICY_AMBIGUOUS,
        ReservationDomainError,
    )

    def ambiguous_resolver(_asset: object) -> ReservationPolicy:
        raise ReservationDomainError(
            POLICY_AMBIGUOUS, "Multiple active policies match at the same priority."
        )

    user("ambiguous-staff@example.com", is_staff=True)
    user("ambiguous-member@example.com")
    asset()
    policy(name="Ambiguous global one")
    audit_event()
    # The enforced constraints reservation_policy_one_active_per_asset and
    # reservation_policy_one_active_global make two live policies at one
    # resolution level impossible via the ORM, so the ambiguity branch is
    # pinned through the product's own POLICY_AMBIGUOUS domain error, exactly
    # as test_reservations_services.test_equal_priority_policy_ambiguity_
    # fails_closed pins it there.
    monkeypatch.setattr(
        command_module.reservation_services, "resolve_effective_policy", ambiguous_resolver
    )

    payload = run_json_command()

    assert payload["counts"]["assets_without_effective_policy"] == 1
    uncovered_check = next(
        item for item in payload["checks"] if item["id"] == "assets_without_effective_policy"
    )
    assert uncovered_check["level"] == "warn"
    assert (
        "1 active reservable exclusive asset(s) lack an effective policy"
        in uncovered_check["detail"]
    )
    assert payload["status"] == "warn"
