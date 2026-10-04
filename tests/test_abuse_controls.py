from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest
from django.conf import settings
from django.db import close_old_connections
from django.test import override_settings

from slaif_reservation.api.models import AbuseBucket
from slaif_reservation.config.abuse import BudgetExceeded, consume


@pytest.mark.django_db(transaction=True)
def test_shared_atomic_quota_cannot_be_multiplied_by_concurrent_connections() -> None:
    def attempt(_: int) -> bool:
        close_old_connections()
        try:
            consume("login_ip", "198.51.100.7")
            return True
        except BudgetExceeded:
            return False
        finally:
            close_old_connections()

    with override_settings(ABUSE_RATES={"login_ip": (5, 3600)}):
        with ThreadPoolExecutor(max_workers=12) as pool:
            allowed = list(pool.map(attempt, range(30)))
    assert sum(allowed) == 5
    assert AbuseBucket.objects.get().count == 6


@pytest.mark.django_db
def test_counter_identity_is_pseudonymous_and_denial_is_bounded() -> None:
    with override_settings(ABUSE_RATES={"login_identity": (1, 3600)}):
        consume("login_identity", "member@example.test")
        with pytest.raises(BudgetExceeded) as caught:
            consume("login_identity", "member@example.test")
    assert 1 <= caught.value.wait <= 3600
    row = AbuseBucket.objects.get()
    assert len(row.key) == 64
    assert "member" not in row.key
    assert row.count == 2


@pytest.mark.django_db
def test_window_expiry_and_cleanup_are_deliberate() -> None:
    from datetime import UTC, datetime, timedelta

    from slaif_reservation.config.abuse import purge_expired

    moment = datetime.now(UTC).timestamp()
    with override_settings(ABUSE_RATES={"api_ip": (1, 60)}):
        consume("api_ip", "198.51.100.5", timestamp=moment)
        with pytest.raises(BudgetExceeded):
            consume("api_ip", "198.51.100.5", timestamp=moment)
        consume("api_ip", "198.51.100.5", timestamp=moment + 61)
    assert AbuseBucket.objects.count() == 2
    old = AbuseBucket.objects.order_by("expires_at").first()
    assert old is not None
    old.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    old.save(update_fields=["expires_at"])
    assert purge_expired() == 1
    assert AbuseBucket.objects.count() == 2
    assert purge_expired(apply=True, batch=1) == 1
    assert AbuseBucket.objects.count() == 1


@pytest.mark.django_db
def test_login_routes_share_normalized_identity_without_locking_account() -> None:
    from django.test import Client

    rates = {**settings.ABUSE_RATES, "login_ip": (100, 3600), "login_identity": (2, 3600)}
    client = Client()
    with override_settings(ABUSE_RATES=rates):
        assert (
            client.post(
                "/login/", {"username": "unknown@example.test", "password": "incorrect"}
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/admin/login/", {"username": "UNKNOWN@example.test", "password": "incorrect"}
            ).status_code
            == 200
        )
        result = client.post(
            "/login/", {"username": "unknown@example.test", "password": "incorrect"}
        )
    assert result.status_code == 429
    assert int(result["Retry-After"]) >= 1
    assert result["Cache-Control"] == "no-store"


@pytest.mark.django_db
def test_missing_invalid_bearer_is_limited_before_authentication() -> None:
    from django.conf import settings
    from django.test import Client

    client = Client()
    with override_settings(ABUSE_RATES={**settings.ABUSE_RATES, "api_ip": (2, 3600)}):
        assert client.get("/api/v1/me/").status_code == 401
        assert client.get("/api/v1/me/", HTTP_AUTHORIZATION="Bearer invalid").status_code == 401
        response = client.get("/api/v1/me/")
    assert response.status_code == 429
    assert response.json()["code"] == "rate_limited"
    assert response.json()["correlation_id"] == response["X-Request-ID"]


def test_budget_failure_is_closed_and_liveness_does_not_query_budgets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from django.test import Client

    from slaif_reservation.config import abuse

    def unavailable(*args: object, **kwargs: object) -> None:
        raise abuse.BudgetUnavailable("Security budget unavailable.")

    monkeypatch.setattr(abuse, "consume", unavailable)
    client = Client()
    response = client.get("/api/v1/me/")
    assert response.status_code == 503
    assert response.json()["code"] == "service_unavailable"
    assert client.post("/login/", {"username": "unknown@example.test"}).status_code == 503
    assert client.get("/health/live").status_code == 200


@pytest.mark.django_db(transaction=True)
def test_locked_counter_fails_within_bound_and_can_recover() -> None:
    import threading
    import time

    from django.db import transaction

    from slaif_reservation.config.abuse import BudgetUnavailable

    ready = threading.Event()
    release = threading.Event()
    with override_settings(ABUSE_RATES={"api_ip": (100, 3600)}):
        consume("api_ip", "198.51.100.20")
        key = AbuseBucket.objects.get().pk

        def holder() -> None:
            close_old_connections()
            try:
                with transaction.atomic():
                    AbuseBucket.objects.select_for_update().get(pk=key)
                    ready.set()
                    release.wait(timeout=5)
            finally:
                close_old_connections()

        thread = threading.Thread(target=holder)
        thread.start()
        assert ready.wait(timeout=3)
        try:
            started = time.monotonic()
            with pytest.raises(BudgetUnavailable):
                consume("api_ip", "198.51.100.20")
            assert time.monotonic() - started < 3
        finally:
            release.set()
            thread.join(timeout=5)
        consume("api_ip", "198.51.100.20")


@pytest.mark.django_db
def test_cleanup_command_defaults_to_dry_run_and_is_bounded() -> None:
    from datetime import UTC, datetime, timedelta
    from io import StringIO

    from django.core.management import call_command

    cutoff = datetime.now(UTC)
    AbuseBucket.objects.bulk_create(
        [
            AbuseBucket(key=f"expired-{index}", count=1, expires_at=cutoff - timedelta(seconds=1))
            for index in range(3)
        ]
    )
    AbuseBucket.objects.create(key="current", count=1, expires_at=cutoff + timedelta(hours=1))
    output = StringIO()
    call_command("purge_expired_abuse_buckets", stdout=output)
    assert "3 expired (dry-run)" in output.getvalue()
    assert AbuseBucket.objects.count() == 4
    call_command("purge_expired_abuse_buckets", apply=True, batch_size=2, stdout=StringIO())
    assert AbuseBucket.objects.count() == 2
    assert AbuseBucket.objects.filter(key="current").exists()


@pytest.mark.django_db
def test_token_quota_rejects_mutations_without_changing_idempotency_or_audit() -> None:
    import json
    import uuid

    from django.test import Client
    from tests.test_api_v1_reservations import (
        asset,
        auth_header,
        bearer,
        future_window,
        iso,
        policy,
        user,
    )

    from slaif_reservation.api.models import IdempotencyRecord
    from slaif_reservation.audit.models import AuditEvent
    from slaif_reservation.reservations.models import Reservation

    owner = user()
    target = asset()
    policy(target)
    token, _ = bearer(owner, ["reservations:create", "reservations:read"])
    start, end = future_window()
    payload = json.dumps({"asset_id": str(target.id), "start_at": iso(start), "end_at": iso(end)})
    key = str(uuid.uuid4())
    headers = {**auth_header(token), "HTTP_IDEMPOTENCY_KEY": key}
    client = Client()
    with override_settings(ABUSE_RATES={**settings.ABUSE_RATES, "api_token": (2, 3600)}):
        first = client.post(
            "/api/v1/reservations/", payload, content_type="application/json", **headers
        )
        assert first.status_code == 201
        replay = client.post(
            "/api/v1/reservations/", payload, content_type="application/json", **headers
        )
        assert replay.status_code == 201
        assert replay.json() == first.json()
        before = (
            Reservation.objects.count(),
            IdempotencyRecord.objects.count(),
            AuditEvent.objects.count(),
        )
        denied = client.post(
            "/api/v1/reservations/",
            payload,
            content_type="application/json",
            **{**headers, "HTTP_IDEMPOTENCY_KEY": str(uuid.uuid4())},
        )
        assert denied.status_code == 429
        assert denied.json()["code"] == "rate_limited"
        assert (
            Reservation.objects.count(),
            IdempotencyRecord.objects.count(),
            AuditEvent.objects.count(),
        ) == before
