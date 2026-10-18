from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, timedelta

import pytest
from django.contrib.auth.models import Permission
from django.db import close_old_connections
from django.test import Client
from django.utils import timezone

from slaif_reservation.accounts.models import User
from slaif_reservation.accounts.services import issue_api_token
from slaif_reservation.api.models import IdempotencyRecord
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.reservations.models import Reservation, ReservationPolicy
from slaif_reservation.reservations.services import create_blackout, create_reservation


def user(email: str = "api-member@example.com", **overrides: object) -> User:
    created = User.objects.create_user(email=email, password="not-a-secret", **overrides)
    grant_booking(created)
    return created


def grant_booking(target: User) -> None:
    # A16: positive booking fixtures explicitly carry the baseline
    # reservations.book_assets capability (real Permission row); the
    # dedicated no-grant denial cases create their own users.
    target.user_permissions.add(
        Permission.objects.get(codename="book_assets", content_type__app_label="reservations")
    )


def asset(slug: str = "api-gpu-a", **overrides: object) -> Asset:
    values = {
        "slug": slug,
        "name": slug.replace("-", " ").title(),
        "kind": Asset.KIND_GPU,
        "active": True,
        "reservable": True,
    }
    values.update(overrides)
    return Asset.objects.create(**values)


def policy(target: Asset, **overrides: object) -> ReservationPolicy:
    values = {
        "name": f"Policy {target.slug}",
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


def bearer(owner: User, scopes: list[str]) -> tuple[str, object]:
    result = issue_api_token(
        owner=owner,
        name="API test token",
        scopes=scopes,
        lifetime_days=1,
    )
    return result.bearer_token, result.token


def auth_header(token: str) -> dict[str, str]:
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def future_window(hours: int = 2) -> tuple[timezone.datetime, timezone.datetime]:
    start = (timezone.now() + timedelta(days=1, hours=hours)).replace(second=0, microsecond=0)
    return start, start + timedelta(hours=1)


def direct_reservation(
    *,
    owner: User,
    target: Asset,
    start: timezone.datetime,
    end: timezone.datetime,
    status: str = Reservation.STATUS_CONFIRMED,
    released_at: timezone.datetime | None = None,
) -> Reservation:
    return Reservation.objects.create(
        asset=target,
        requested_by_user=owner,
        source=Reservation.SOURCE_API,
        status=status,
        start_at=start,
        end_at=end,
        effective_end_at=released_at if released_at else end,
        released_at=released_at if status == Reservation.STATUS_RELEASED else None,
        cancelled_at=(
            start - timedelta(minutes=5) if status == Reservation.STATUS_CANCELLED else None
        ),
        cancelled_by=owner if status == Reservation.STATUS_CANCELLED else None,
        cancellation_reason="private reason" if status == Reservation.STATUS_CANCELLED else "",
        purpose="private purpose",
    )


def iso(value: timezone.datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


@pytest.mark.django_db
def test_bearer_authentication_and_scope_matrix(client) -> None:
    owner = user()
    token, _row = bearer(owner, ["reservations:read"])

    missing = client.get("/api/v1/me/")
    assert missing.status_code == 401
    assert missing.json()["code"] == "authentication_required"

    malformed = client.get("/api/v1/me/", HTTP_AUTHORIZATION="Bearer not-a-valid-token")
    assert malformed.status_code == 401
    assert malformed.json()["code"] == "invalid_token"

    response = client.get(
        "/api/v1/assets/00000000-0000-0000-0000-000000000001/availability/",
        **auth_header(token),
    )
    assert response.status_code == 403
    assert response.json()["code"] == "insufficient_scope"

    ok = client.get("/api/v1/me/", **auth_header(token))
    assert ok.status_code == 200
    payload = ok.json()
    assert payload["principal"]["id"] == str(owner.id)
    assert "email" not in payload["principal"]
    assert "verifier" not in str(payload)


@pytest.mark.django_db
def test_staff_asset_api_remains_session_only(client) -> None:
    owner = user()
    token, _row = bearer(owner, ["assets:read"])
    target = asset()

    response = client.get("/api/v1/assets/", **auth_header(token))
    assert response.status_code == 403

    detail = client.get(f"/api/v1/assets/{target.id}/", **auth_header(token))
    assert detail.status_code == 403


@pytest.mark.django_db
def test_availability_api_is_privacy_safe(client) -> None:
    owner = user()
    other = user("other-api@example.com")
    target = asset()
    policy(target)
    token, _row = bearer(owner, ["availability:read"])
    start, end = future_window()
    direct_reservation(owner=other, target=target, start=start, end=end)

    response = client.get(
        f"/api/v1/assets/{target.id}/availability/",
        {"date": start.date().isoformat(), "days": "1", "timezone": "UTC"},
        **auth_header(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["asset"]["id"] == str(target.id)
    assert payload["display_timezone"] == "UTC"
    assert payload["busy"][0]["label"] == "Unavailable"
    body = response.content.decode()
    assert other.email not in body
    assert "private purpose" not in body
    assert str(Reservation.objects.get().id) not in body


@pytest.mark.django_db
def test_availability_api_reports_missing_asset_with_endpoint_code(client) -> None:
    owner = user()
    token, _row = bearer(owner, ["availability:read"])

    response = client.get(
        f"/api/v1/assets/{uuid.uuid4()}/availability/",
        {"date": timezone.localdate().isoformat(), "days": "1", "timezone": "UTC"},
        **auth_header(token),
    )

    assert response.status_code == 404
    payload = response.json()
    assert payload["code"] == "asset_not_found"
    body = response.content.decode()
    assert "Traceback" not in body
    assert "Asset object" not in body


@pytest.mark.django_db
def test_availability_api_interval_semantics_and_privacy(client) -> None:
    owner = user()
    other = user("availability-other@example.com", display_name="Other User")
    target = asset()
    policy(target, min_duration_minutes=30)
    token, _row = bearer(owner, ["availability:read"])
    window_start = (timezone.now() + timedelta(days=3)).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    window_end = window_start + timedelta(days=1)
    confirmed_start_clip = direct_reservation(
        owner=other,
        target=target,
        start=window_start - timedelta(hours=1),
        end=window_start + timedelta(hours=1),
    )
    confirmed_adjacent = direct_reservation(
        owner=other,
        target=target,
        start=window_start + timedelta(hours=1),
        end=window_start + timedelta(hours=2),
    )
    released = direct_reservation(
        owner=other,
        target=target,
        start=window_start + timedelta(hours=3),
        end=window_start + timedelta(hours=6),
        status=Reservation.STATUS_RELEASED,
        released_at=window_start + timedelta(hours=4),
    )
    cancelled = direct_reservation(
        owner=other,
        target=target,
        start=window_start + timedelta(hours=5),
        end=window_start + timedelta(hours=6),
        status=Reservation.STATUS_CANCELLED,
    )
    confirmed_end_clip = direct_reservation(
        owner=other,
        target=target,
        start=window_end - timedelta(hours=1),
        end=window_end + timedelta(hours=1),
    )

    response = client.get(
        f"/api/v1/assets/{target.id}/availability/",
        {"date": window_start.date().isoformat(), "days": "1", "timezone": "UTC"},
        **auth_header(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["busy"] == [
        {
            "start": iso(window_start),
            "end": iso(window_start + timedelta(hours=2)),
            "label": "Unavailable",
            "reservation_id": None,
        },
        {
            "start": iso(window_start + timedelta(hours=3)),
            "end": iso(window_start + timedelta(hours=4)),
            "label": "Unavailable",
            "reservation_id": None,
        },
        {
            "start": iso(window_end - timedelta(hours=1)),
            "end": iso(window_end),
            "label": "Unavailable",
            "reservation_id": None,
        },
    ]
    assert payload["free"] == [
        {
            "start": iso(window_start + timedelta(hours=2)),
            "end": iso(window_start + timedelta(hours=3)),
            "latest_valid_start": iso(window_start + timedelta(hours=2, minutes=30)),
        },
        {
            "start": iso(window_start + timedelta(hours=4)),
            "end": iso(window_end - timedelta(hours=1)),
            "latest_valid_start": iso(window_end - timedelta(hours=1, minutes=30)),
        },
    ]
    body = response.content.decode()
    for private_value in [
        other.email,
        other.display_name,
        "private purpose",
        "private reason",
        str(confirmed_start_clip.id),
        str(confirmed_adjacent.id),
        str(released.id),
        str(cancelled.id),
        str(confirmed_end_clip.id),
    ]:
        assert private_value not in body


@pytest.mark.django_db
def test_availability_api_includes_blackouts_without_reason_or_identity(client) -> None:
    owner = user()
    staff = user("availability-staff@example.com", is_staff=True)
    staff.user_permissions.add(
        Permission.objects.get(
            codename="manage_maintenance_blackouts",
            content_type__app_label="reservations",
        )
    )
    other = user("availability-blackout-other@example.com", display_name="Other Person")
    target = asset()
    policy(target, min_duration_minutes=30)
    token, _row = bearer(owner, ["availability:read"])
    window_start = (timezone.now() + timedelta(days=4)).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    create_blackout(
        asset=target,
        actor_user=staff,
        reason="private blackout reason",
        start_at=window_start + timedelta(hours=2),
        end_at=window_start + timedelta(hours=4),
        confirmed_overlap=True,
    )
    direct_reservation(
        owner=other,
        target=target,
        start=window_start + timedelta(hours=4),
        end=window_start + timedelta(hours=5),
    )

    response = client.get(
        f"/api/v1/assets/{target.id}/availability/",
        {"date": window_start.date().isoformat(), "days": "1", "timezone": "UTC"},
        **auth_header(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["busy"][0]["label"] == "Unavailable"
    assert payload["busy"][0]["start"] == iso(window_start + timedelta(hours=2))
    assert payload["busy"][0]["end"] == iso(window_start + timedelta(hours=5))
    body = response.content.decode()
    assert "private blackout reason" not in body
    assert other.email not in body
    assert other.display_name not in body
    assert "private purpose" not in body


@pytest.mark.django_db
@pytest.mark.parametrize(
    "params",
    [
        {"date": "not-a-date"},
        {"days": "0"},
        {"days": "8"},
        {"timezone": "Mars/Base"},
    ],
)
def test_availability_api_rejects_invalid_parameters_with_problem_details(
    client,
    params: dict[str, str],
) -> None:
    owner = user()
    target = asset()
    policy(target)
    token, _row = bearer(owner, ["availability:read"])

    response = client.get(
        f"/api/v1/assets/{target.id}/availability/",
        params,
        **auth_header(token),
    )

    assert response.status_code == 400
    assert response["Content-Type"].startswith("application/problem+json")
    payload = response.json()
    assert payload["code"] == "validation_error"
    assert payload["correlation_id"]
    body = response.content.decode()
    assert "Traceback" not in body
    assert "ZoneInfo" not in body


@pytest.mark.django_db
def test_reservation_create_is_idempotent_and_replays_without_duplicate_audit(client) -> None:
    owner = user()
    target = asset()
    policy(target)
    token, token_row = bearer(owner, ["reservations:create", "reservations:read"])
    start, end = future_window()
    body = {
        "asset_id": str(target.id),
        "start_at": start.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "end_at": end.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "purpose": "safe API purpose",
    }
    headers = {
        **auth_header(token),
        "HTTP_IDEMPOTENCY_KEY": "create-key-001",
        "HTTP_X_REQUEST_ID": str(uuid.uuid4()),
    }

    first = client.post("/api/v1/reservations/", body, content_type="application/json", **headers)
    second = client.post("/api/v1/reservations/", body, content_type="application/json", **headers)

    assert first.status_code == 201
    assert second.status_code == 201
    assert second["X-Idempotent-Replay"] == "true"
    assert first["Location"].endswith(f"/api/v1/reservations/{first.json()['id']}/")
    assert second["Location"] == first["Location"]
    assert second["X-Request-ID"] == first.json()["correlation_id"]
    assert second.json() == first.json()
    assert Reservation.objects.count() == 1
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_RESERVATION_CREATED).count() == 1
    record = IdempotencyRecord.objects.get(api_token=token_row)
    assert record.response_status == 201
    assert record.response_headers == {"Location": first["Location"]}
    assert "Authorization" not in str(record.response_body)
    assert "Authorization" not in str(record.response_headers)
    assert "Bearer" not in str(record.response_headers)
    assert "safe API purpose" in str(record.response_body)
    assert record.target_type == "reservation"


@pytest.mark.django_db
@pytest.mark.parametrize("changed_body", [False, True])
def test_expired_idempotency_record_fails_without_replay_or_mutation(
    client,
    changed_body: bool,
) -> None:
    owner = user()
    target = asset()
    policy(target)
    token, token_row = bearer(owner, ["reservations:create"])
    start, end = future_window()
    body = {
        "asset_id": str(target.id),
        "start_at": iso(start),
        "end_at": iso(end),
        "purpose": "first",
    }
    headers = {**auth_header(token), "HTTP_IDEMPOTENCY_KEY": "expired-key-1"}
    first = client.post("/api/v1/reservations/", body, content_type="application/json", **headers)
    assert first.status_code == 201
    record = IdempotencyRecord.objects.get(api_token=token_row)
    record.expires_at = timezone.now() - timedelta(seconds=1)
    record.save(update_fields=["expires_at"])
    before_reservation_count = Reservation.objects.count()
    before_audit_count = AuditEvent.objects.count()

    retry_body = {**body, "purpose": "changed"} if changed_body else body
    retry = client.post(
        "/api/v1/reservations/",
        retry_body,
        content_type="application/json",
        **headers,
    )

    assert retry.status_code == 409
    payload = retry.json()
    assert payload["code"] == "idempotency_expired"
    assert "X-Idempotent-Replay" not in retry
    assert Reservation.objects.count() == before_reservation_count
    assert AuditEvent.objects.count() == before_audit_count


@pytest.mark.django_db
def test_idempotency_conflict_rejects_same_key_different_request(client) -> None:
    owner = user()
    target = asset()
    policy(target)
    token, _row = bearer(owner, ["reservations:create"])
    start, end = future_window()
    body = {
        "asset_id": str(target.id),
        "start_at": start.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "end_at": end.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "purpose": "first",
    }
    headers = {**auth_header(token), "HTTP_IDEMPOTENCY_KEY": "same-key-diff-1"}
    first = client.post("/api/v1/reservations/", body, content_type="application/json", **headers)
    changed = {**body, "purpose": "changed"}
    second = client.post(
        "/api/v1/reservations/",
        changed,
        content_type="application/json",
        **headers,
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["code"] == "idempotency_conflict"
    assert Reservation.objects.count() == 1


@pytest.mark.django_db
def test_same_key_different_token_is_independent(client) -> None:
    first_owner = user("first-token@example.com")
    second_owner = user("second-token@example.com")
    first_asset = asset("api-token-gpu-a")
    second_asset = asset("api-token-gpu-b")
    policy(first_asset)
    policy(second_asset)
    first_token, _first_row = bearer(first_owner, ["reservations:create"])
    second_token, _second_row = bearer(second_owner, ["reservations:create"])
    first_start, first_end = future_window(2)
    second_start, second_end = future_window(4)

    first = client.post(
        "/api/v1/reservations/",
        {
            "asset_id": str(first_asset.id),
            "start_at": first_start.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "end_at": first_end.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "purpose": "",
        },
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="shared-key-001",
        **auth_header(first_token),
    )
    second = client.post(
        "/api/v1/reservations/",
        {
            "asset_id": str(second_asset.id),
            "start_at": second_start.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "end_at": second_end.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "purpose": "",
        },
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="shared-key-001",
        **auth_header(second_token),
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert Reservation.objects.count() == 2
    assert IdempotencyRecord.objects.count() == 2


@pytest.mark.django_db(transaction=True)
def test_concurrent_identical_create_mutates_once() -> None:
    owner = user("concurrent-owner@example.com")
    target = asset("api-concurrent-gpu-a")
    policy(target)
    token, _row = bearer(owner, ["reservations:create"])
    start, end = future_window(3)
    payload = {
        "asset_id": str(target.id),
        "start_at": start.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "end_at": end.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "purpose": "concurrent",
    }

    def post_once() -> tuple[int, bool]:
        close_old_connections()
        local_client = Client()
        response = local_client.post(
            "/api/v1/reservations/",
            payload,
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY="concurrent-create-1",
            **auth_header(token),
        )
        close_old_connections()
        return response.status_code, response.headers.get("X-Idempotent-Replay") == "true"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _index: post_once(), range(2)))

    assert sorted(status for status, _replayed in results) == [201, 201]
    assert sum(1 for _status, replayed in results if replayed) == 1
    assert Reservation.objects.count() == 1
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_RESERVATION_CREATED).count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_different_body_same_key_conflicts_once() -> None:
    owner = user("concurrent-conflict@example.com")
    first_asset = asset("api-concurrent-gpu-b")
    second_asset = asset("api-concurrent-gpu-c")
    policy(first_asset)
    policy(second_asset)
    token, _row = bearer(owner, ["reservations:create"])
    first_start, first_end = future_window(3)
    second_start, second_end = future_window(5)
    payloads = [
        {
            "asset_id": str(first_asset.id),
            "start_at": first_start.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "end_at": first_end.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "purpose": "first",
        },
        {
            "asset_id": str(second_asset.id),
            "start_at": second_start.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "end_at": second_end.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "purpose": "second",
        },
    ]

    def post_payload(payload: dict[str, str]) -> tuple[int, str | None]:
        close_old_connections()
        local_client = Client()
        response = local_client.post(
            "/api/v1/reservations/",
            payload,
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY="concurrent-conflict-1",
            **auth_header(token),
        )
        code = response.json().get("code") if response.status_code != 201 else None
        close_old_connections()
        return response.status_code, code

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(post_payload, payloads))

    assert sorted(status for status, _code in results) == [201, 409]
    assert any(code == "idempotency_conflict" for _status, code in results)
    assert Reservation.objects.count() == 1
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_RESERVATION_CREATED).count() == 1


@pytest.mark.django_db
def test_reservation_list_detail_cancel_and_release_are_owner_scoped(client) -> None:
    owner = user()
    other = user("other-owner@example.com")
    target = asset()
    other_target = asset("api-gpu-b")
    policy(target)
    policy(other_target)
    token, _row = bearer(
        owner,
        [
            "reservations:read",
            "reservations:cancel",
            "reservations:release",
        ],
    )
    start, end = future_window()
    own = create_reservation(
        asset=target,
        requested_by_user=owner,
        start_at=start,
        end_at=end,
        purpose="owner purpose",
        source=Reservation.SOURCE_API,
    ).reservation
    other_reservation = create_reservation(
        asset=other_target,
        requested_by_user=other,
        start_at=start,
        end_at=end,
        purpose="other private purpose",
        source=Reservation.SOURCE_API,
    ).reservation

    list_response = client.get("/api/v1/reservations/", **auth_header(token))
    assert list_response.status_code == 200
    body = list_response.content.decode()
    assert str(own.id) in body
    assert str(other_reservation.id) not in body
    assert "other private purpose" not in body

    missing = client.get(f"/api/v1/reservations/{other_reservation.id}/", **auth_header(token))
    assert missing.status_code == 404
    assert missing.json()["code"] == "reservation_not_found"

    cancel = client.post(
        f"/api/v1/reservations/{own.id}/cancel/",
        {"reason": "owner reason"},
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="cancel-key-1",
        **auth_header(token),
    )
    assert cancel.status_code == 200
    own.refresh_from_db()
    assert own.status == Reservation.STATUS_CANCELLED

    active_start = timezone.now() - timedelta(minutes=10)
    active_end = timezone.now() + timedelta(minutes=50)
    active = direct_reservation(owner=owner, target=target, start=active_start, end=active_end)
    release = client.post(
        f"/api/v1/reservations/{active.id}/release/",
        {},
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="release-key-1",
        **auth_header(token),
    )
    assert release.status_code == 200
    active.refresh_from_db()
    assert active.status == Reservation.STATUS_RELEASED


@pytest.mark.django_db
def test_reservation_not_found_codes_are_endpoint_specific_and_non_disclosing(client) -> None:
    owner = user()
    other = user("other-reservation@example.com")
    target = asset()
    other_target = asset("other-reservation-gpu")
    policy(target)
    policy(other_target)
    token, _row = bearer(
        owner,
        ["reservations:read", "reservations:cancel", "reservations:release"],
    )
    start, end = future_window()
    other_reservation = create_reservation(
        asset=other_target,
        requested_by_user=other,
        start_at=start,
        end_at=end,
        purpose="other private purpose",
        source=Reservation.SOURCE_API,
    ).reservation

    responses = [
        client.get(f"/api/v1/reservations/{uuid.uuid4()}/", **auth_header(token)),
        client.get(f"/api/v1/reservations/{other_reservation.id}/", **auth_header(token)),
        client.post(
            f"/api/v1/reservations/{other_reservation.id}/cancel/",
            {"reason": "owner reason"},
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY="other-cancel-1",
            **auth_header(token),
        ),
        client.post(
            f"/api/v1/reservations/{other_reservation.id}/release/",
            {},
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY="other-release-1",
            **auth_header(token),
        ),
    ]

    for response in responses:
        assert response.status_code == 404
        assert response["Content-Type"].startswith("application/problem+json")
        payload = response.json()
        assert payload["code"] == "reservation_not_found"
        body = response.content.decode()
        assert str(other_reservation.id) not in body
        assert other.email not in body
        assert "other private purpose" not in body
        assert "Traceback" not in body
        assert "Reservation object" not in body


@pytest.mark.django_db
def test_reservation_list_rejects_unknown_and_invalid_time_window_filters(client) -> None:
    owner = user()
    token, _row = bearer(owner, ["reservations:read"])
    start, end = future_window()

    unknown = client.get("/api/v1/reservations/", {"unexpected": "1"}, **auth_header(token))
    assert unknown.status_code == 400
    assert unknown.json()["code"] == "validation_error"

    inverted = client.get(
        "/api/v1/reservations/",
        {"from": iso(end), "to": iso(start)},
        **auth_header(token),
    )
    assert inverted.status_code == 400
    assert inverted.json()["code"] == "validation_error"
    body = inverted.content.decode()
    assert "Traceback" not in body
    assert "Reservation object" not in body


@pytest.mark.django_db
def test_mutation_requires_valid_idempotency_key_and_aware_timestamps(client) -> None:
    owner = user()
    target = asset()
    policy(target)
    token, _row = bearer(owner, ["reservations:create"])
    start, end = future_window()
    body = {
        "asset_id": str(target.id),
        "start_at": start.replace(tzinfo=None).isoformat(),
        "end_at": end.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "purpose": "",
    }

    missing_key = client.post(
        "/api/v1/reservations/",
        body,
        content_type="application/json",
        **auth_header(token),
    )
    assert missing_key.status_code == 400
    assert missing_key.json()["code"] == "idempotency_required"

    invalid_time = client.post(
        "/api/v1/reservations/",
        body,
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="valid-key-001",
        **auth_header(token),
    )
    assert invalid_time.status_code == 400
    assert invalid_time.json()["code"] == "validation_error"
    assert Reservation.objects.count() == 0
