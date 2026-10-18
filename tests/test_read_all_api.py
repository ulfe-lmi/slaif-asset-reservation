"""Order 051-a: explicit read-all bearer authority (real PostgreSQL/HTTP).

Dual-gate matrix (token scope AND owner's CURRENT view_all_reservations),
the minimal explicit cross-user representation with privacy canaries,
validated overlap filters/pagination, read-only verbs, response headers,
and the unchanged owner-only compatibility of the old bearer surface.
"""

from __future__ import annotations

import uuid
from datetime import UTC, timedelta

import pytest
from django.contrib.auth.models import Group, Permission
from django.test import Client, override_settings
from django.utils import timezone

from slaif_reservation.accounts.models import ApiToken, User
from slaif_reservation.accounts.services import issue_api_token
from slaif_reservation.assets.models import Asset
from slaif_reservation.reservations.models import Reservation

READ_ALL = "reservations:read_all"
LIST_URL = "/api/v1/all-reservations/"


# --- helpers ------------------------------------------------------------------


def user(email: str, **overrides: object) -> User:
    return User.objects.create_user(email=email, password="not-a-secret", **overrides)


def permission(codename: str) -> Permission:
    return Permission.objects.get(codename=codename, content_type__app_label="reservations")


def grant(target: User, *codenames: str) -> None:
    target.user_permissions.add(*[permission(c) for c in codenames])


def viewer() -> User:
    """Non-staff reader with view_all but NO booking capability."""
    target = user("readall-viewer@example.com", display_name="Read All Viewer")
    grant(target, "view_all_reservations")
    return target


def asset(slug: str = "readall-gpu") -> Asset:
    return Asset.objects.create(
        slug=slug,
        name=slug.replace("-", " ").title(),
        kind=Asset.KIND_GPU,
        active=True,
        reservable=True,
    )


def reservation(
    *,
    owner: User,
    target: Asset | None = None,
    status: str = Reservation.STATUS_CONFIRMED,
    start: timezone.datetime | None = None,
    end: timezone.datetime | None = None,
    released_at: timezone.datetime | None = None,
    purpose: str = "private purpose canary",
) -> Reservation:
    base = start or timezone.now() + timedelta(days=1)
    end = end or base + timedelta(hours=2)
    cancelled = status == Reservation.STATUS_CANCELLED
    return Reservation.objects.create(
        asset=target or asset(f"readall-{uuid.uuid4().hex[:8]}"),
        requested_by_user=owner,
        source=Reservation.SOURCE_WEB,
        status=status,
        start_at=base,
        end_at=end,
        effective_end_at=(released_at or end) if not cancelled else end,
        released_at=released_at if status == Reservation.STATUS_RELEASED else None,
        cancelled_at=base - timedelta(minutes=5) if cancelled else None,
        cancelled_by=owner if cancelled else None,
        cancellation_reason="private cancellation canary" if cancelled else "",
        purpose=purpose,
    )


def bearer(owner: User, scopes: list[str]) -> str:
    return issue_api_token(
        owner=owner, name="readall token", scopes=scopes, lifetime_days=1
    ).bearer_token


def auth(token: str) -> dict[str, str]:
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def iso(value: timezone.datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


# --- dual-gate matrix -----------------------------------------------------------


@pytest.mark.django_db
def test_dual_gate_matrix(client: Client) -> None:
    owner = viewer()
    other = user("readall-other@example.com")
    other_reservation = reservation(owner=other)

    # NEITHER: no capability and no read_all scope (scope gate fails first).
    plain = user("readall-plain@example.com")
    response = client.get(LIST_URL, **auth(bearer(plain, ["reservations:read"])))
    assert response.status_code == 403
    assert response.json()["code"] == "insufficient_scope"

    # PERMISSION ONLY: capability but no read_all scope.
    response = client.get(LIST_URL, **auth(bearer(owner, ["reservations:read"])))
    assert response.status_code == 403
    assert response.json()["code"] == "insufficient_scope"

    # SCOPE ONLY: a read_all scope without the CURRENT capability. The
    # token is a legitimate historical one (grant -> issue -> revoke the
    # grant); protected use rechecks and denies.
    no_cap = user("readall-nocap@example.com")
    grant(no_cap, "view_all_reservations")
    token = bearer(no_cap, [READ_ALL])
    no_cap.user_permissions.clear()
    response = client.get(LIST_URL, **auth(token))
    assert response.status_code == 403
    assert response.json()["code"] == "permission_denied"
    # Unauthorized callers cannot infer the record's existence.
    detail = client.get(f"{LIST_URL}{other_reservation.id}/", **auth(token))
    assert detail.status_code == 403

    # BOTH: non-staff reader without booking capability qualifies.
    assert not owner.is_staff
    assert not owner.has_perm("reservations.book_assets")
    token = bearer(owner, [READ_ALL, "reservations:read"])
    response = client.get(LIST_URL, **auth(token))
    assert response.status_code == 200
    assert str(other_reservation.id) in response.content.decode()

    # Detail for the same authorized request.
    detail = client.get(f"{LIST_URL}{other_reservation.id}/", **auth(token))
    assert detail.status_code == 200
    assert detail.json()["id"] == str(other_reservation.id)


@pytest.mark.django_db
def test_staff_and_model_view_alone_do_not_qualify(client: Client) -> None:
    staff = user("readall-staff@example.com", is_staff=True)
    staff.user_permissions.add(permission("view_reservation"))
    assert staff.has_perm("reservations.view_reservation")
    assert not staff.has_perm("reservations.view_all_reservations")
    other = user("readall-other2@example.com")
    other_reservation = reservation(owner=other)

    # Historical token: minted while the capability held, now stripped;
    # staff status plus the Administration model View permission alone do
    # NOT qualify.
    staff.user_permissions.add(permission("view_all_reservations"))
    token = bearer(staff, [READ_ALL])
    staff.user_permissions.clear()
    response = client.get(LIST_URL, **auth(token))
    assert response.status_code == 403
    assert response.json()["code"] == "permission_denied"

    # Trusted active superuser keeps Django permission semantics: the
    # capability gate passes, but the new scope is still required.
    admin = user("readall-admin@example.com", is_superuser=True)
    response = client.get(LIST_URL, **auth(bearer(admin, ["reservations:read"])))
    assert response.status_code == 403
    assert response.json()["code"] == "insufficient_scope"

    response = client.get(LIST_URL, **auth(bearer(admin, [READ_ALL])))
    assert response.status_code == 200
    assert str(other_reservation.id) in response.content.decode()


@pytest.mark.django_db
def test_capability_removal_takes_effect_with_same_valid_token(client: Client) -> None:
    owner = viewer()
    other = user("readall-other3@example.com")
    other_reservation = reservation(owner=other)
    token = bearer(owner, [READ_ALL, "reservations:read"])

    assert client.get(LIST_URL, **auth(token)).status_code == 200
    owner.user_permissions.clear()
    response = client.get(LIST_URL, **auth(token))
    assert response.status_code == 403
    assert response.json()["code"] == "permission_denied"
    # The same token keeps its owner-only scope.
    own = reservation(owner=owner)
    listing = client.get("/api/v1/reservations/", **auth(token))
    assert listing.status_code == 200
    assert str(own.id) in listing.content.decode()
    assert str(other_reservation.id) not in listing.content.decode()


@pytest.mark.django_db
def test_additive_grants_union_across_groups_and_individual(client: Client) -> None:
    owner = user("readall-union@example.com")
    group_a = Group.objects.create(name="readall-group-a")
    group_a.permissions.add(permission("view_all_reservations"))
    group_b = Group.objects.create(name="readall-group-b")
    group_b.permissions.add(permission("book_assets"))
    owner.groups.add(group_a, group_b)
    assert owner.has_perm("reservations.view_all_reservations")

    # Removing one group while the other grant remains retains authority.
    owner.groups.remove(group_a)
    owner.user_permissions.add(permission("view_all_reservations"))
    token = bearer(owner, [READ_ALL])
    assert client.get(LIST_URL, **auth(token)).status_code == 200

    # Last grant removed -> denied again with the same token.
    owner.user_permissions.clear()
    assert client.get(LIST_URL, **auth(token)).status_code == 403


def _direct_expired_token_row(owner: User, scopes: list[str]) -> str:
    """Create a token row directly (service marker) with a known plaintext,
    then age it with the same raw-SQL pattern the token suite uses: the
    api_token_expires_after_created constraint forbids an ORM save with an
    expiry before created_at, so both timestamps move to the past."""
    from django.conf import settings
    from django.db import connection

    from slaif_reservation.accounts.models import API_TOKEN_SERVICE_CREATE_ATTR
    from slaif_reservation.accounts.tokens import (
        api_token_verifier,
        format_bearer_token,
    )

    token_id = uuid.uuid4()
    secret = "E" * 43
    bearer_value = format_bearer_token(token_id=token_id, secret=secret)
    token = ApiToken(
        id=token_id,
        owner=owner,
        name="Direct lifecycle token",
        verifier=api_token_verifier(bearer_token=bearer_value, pepper=settings.API_TOKEN_PEPPER),
        scopes=scopes,
        expires_at=timezone.now() + timedelta(days=1),
    )
    setattr(token, API_TOKEN_SERVICE_CREATE_ATTR, True)
    try:
        token.save()
    finally:
        delattr(token, API_TOKEN_SERVICE_CREATE_ATTR)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE accounts_apitoken SET created_at = %s, expires_at = %s WHERE id = %s",
            [
                timezone.now() - timedelta(days=3),
                timezone.now() - timedelta(days=2),
                token_id,
            ],
        )
    return bearer_value


@pytest.mark.django_db
def test_token_lifecycle_states_still_authenticate_closed(client: Client) -> None:
    from slaif_reservation.accounts.services import revoke_api_token

    owner = viewer()

    # Expired token (row created directly, then aged past its expiry).
    expired_bearer = _direct_expired_token_row(owner, [READ_ALL])
    response = client.get(LIST_URL, **auth(expired_bearer))
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"

    # Revoked token issued through the service (plaintext known once).
    revoked_bearer = issue_api_token(
        owner=owner, name="to-revoke", scopes=[READ_ALL], lifetime_days=1
    ).bearer_token
    revoke_api_token(token=ApiToken.objects.get(owner=owner, name="to-revoke"), owner=owner)
    response = client.get(LIST_URL, **auth(revoked_bearer))
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"

    # Inactive owner: the token was valid while the owner was active.
    flipping = user("readall-flipping@example.com")
    grant(flipping, "view_all_reservations")
    flipping_bearer = bearer(flipping, [READ_ALL])
    assert client.get(LIST_URL, **auth(flipping_bearer)).status_code == 200
    User.objects.filter(pk=flipping.pk).update(is_active=False)
    response = client.get(LIST_URL, **auth(flipping_bearer))
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"

    # Service-account owner: issued while the flag was clear, then set.
    service = user("readall-service@example.com")
    grant(service, "view_all_reservations")
    service_bearer = bearer(service, [READ_ALL])
    assert client.get(LIST_URL, **auth(service_bearer)).status_code == 200
    User.objects.filter(pk=service.pk).update(is_service_account=True)
    response = client.get(LIST_URL, **auth(service_bearer))
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"


@pytest.mark.django_db
def test_shared_abuse_budgets_still_apply(client: Client) -> None:
    from django.conf import settings

    with override_settings(ABUSE_RATES={**settings.ABUSE_RATES, "api_token": (1, 3600)}):
        owner = viewer()
        token = bearer(owner, [READ_ALL])
        first = client.get(LIST_URL, **auth(token))
        assert first.status_code == 200
        second = client.get(LIST_URL, **auth(token))
        assert second.status_code == 429
        assert second.json()["code"] == "rate_limited"
        assert "Retry-After" in second


# --- representation and privacy -------------------------------------------------


ALLOWED_ROW_KEYS = {
    "id",
    "asset",
    "owner",
    "status",
    "lifecycle",
    "start_at",
    "end_at",
    "effective_end_at",
    "released_at",
    "cancelled_at",
    "blocking_interval",
}


@pytest.mark.django_db
def test_list_returns_exactly_the_minimal_allowlist(client: Client) -> None:
    owner = viewer()
    other = user("readall-canary-owner@example.com", display_name="Canary Display")
    other.external_identifier = "ext-001001"
    other.save(update_fields=["external_identifier"])
    other.groups.add(Group.objects.create(name="readall-canary-group"))
    other_reservation = reservation(owner=other)

    token = bearer(owner, [READ_ALL])
    response = client.get(LIST_URL, **auth(token))
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"count", "next", "previous", "results", "correlation_id"}
    row = next(r for r in body["results"] if r["id"] == str(other_reservation.id))
    assert set(row) == ALLOWED_ROW_KEYS
    assert set(row["asset"]) == {"id", "slug", "name", "kind"}
    assert set(row["owner"]) == {"id", "external_identifier"}
    assert row["owner"]["id"] == str(other.id)
    # Opaque external identifier: leading zeros and case preserved verbatim.
    assert row["owner"]["external_identifier"] == "ext-001001"

    # Privacy canaries: nothing private leaves the server.
    rendered = response.content.decode()
    for forbidden in (
        other.email,
        "Canary Display",
        "private purpose canary",
        "private cancellation canary",
        "readall-canary-group",
        "is_staff",
        "is_superuser",
        "password",
        "verifier",
        "physical_locator",
        "cancellation_reason",
        "purpose",
        "created_at",
        "source",
    ):
        assert forbidden not in rendered, forbidden


@pytest.mark.django_db
def test_unassigned_external_identifier_is_explicit_null(client: Client) -> None:
    owner = viewer()
    other = user("readall-null-ext@example.com")
    assert other.external_identifier is None
    other_reservation = reservation(owner=other)
    token = bearer(owner, [READ_ALL])
    response = client.get(f"{LIST_URL}{other_reservation.id}/", **auth(token))
    assert response.status_code == 200
    detail = response.json()
    assert set(detail) == ALLOWED_ROW_KEYS | {"correlation_id"}
    assert detail["owner"]["external_identifier"] is None
    assert detail["correlation_id"] == response["X-Request-ID"]


@pytest.mark.django_db
def test_max_length_and_case_sensitive_external_identifier(client: Client) -> None:
    owner = viewer()
    other = user("readall-long-ext@example.com")
    other.external_identifier = "A" * 64 + "b" * 64  # 128, mixed case
    other.save(update_fields=["external_identifier"])
    other_reservation = reservation(owner=other)
    token = bearer(owner, [READ_ALL])
    response = client.get(f"{LIST_URL}{other_reservation.id}/", **auth(token))
    row = response.json()
    assert row["owner"]["external_identifier"] == "A" * 64 + "b" * 64


@pytest.mark.django_db
def test_blocking_interval_semantics_per_status(client: Client) -> None:
    owner = viewer()
    other = user("readall-interval@example.com")
    now = timezone.now()

    confirmed_upcoming = reservation(
        owner=other, start=now + timedelta(days=1), end=now + timedelta(days=1, hours=2)
    )
    confirmed_past = reservation(
        owner=other, start=now - timedelta(days=2), end=now - timedelta(days=1, hours=23)
    )
    released = reservation(
        owner=other,
        status=Reservation.STATUS_RELEASED,
        start=now - timedelta(days=1),
        end=now + timedelta(days=1),
        released_at=now - timedelta(hours=12),
    )
    cancelled = reservation(
        owner=other, status=Reservation.STATUS_CANCELLED, start=now + timedelta(days=3)
    )

    token = bearer(owner, [READ_ALL])
    for reservation_row, expected in [
        (confirmed_upcoming, ("upcoming", True)),
        (confirmed_past, ("completed", True)),
        (released, ("released", True)),
        (cancelled, ("cancelled", False)),
    ]:
        detail = client.get(f"{LIST_URL}{reservation_row.id}/", **auth(token))
        assert detail.status_code == 200
        row = detail.json()
        assert row["lifecycle"] == expected[0]
        if expected[1]:
            assert row["blocking_interval"] == {
                "start_at": iso(reservation_row.start_at),
                "end_at": iso(reservation_row.effective_end_at),
            }
        else:
            assert row["blocking_interval"] is None

    # A released record keeps the consumed prefix as original-end evidence.
    released_detail = client.get(f"{LIST_URL}{released.id}/", **auth(token))
    row = released_detail.json()
    assert row["released_at"] == iso(released.released_at)
    assert row["end_at"] == iso(released.end_at)
    assert row["blocking_interval"]["end_at"] == iso(released.effective_end_at)


# --- filters, pagination and read-only verbs ------------------------------------


@pytest.mark.django_db
def test_overlap_filters_are_strict_half_open(client: Client) -> None:
    owner = viewer()
    other = user("readall-filter@example.com")
    now = timezone.now().replace(microsecond=0)
    before = reservation(
        owner=other, start=now - timedelta(days=3), end=now - timedelta(days=2, hours=22)
    )
    spanning = reservation(owner=other, start=now - timedelta(days=1), end=now + timedelta(days=1))
    after = reservation(
        owner=other, start=now + timedelta(days=2), end=now + timedelta(days=2, hours=2)
    )

    token = bearer(owner, [READ_ALL])
    # from = effective_end_at > from (strict): `before` ends at
    # now-3d+2h... use its exact effective end as the bound: the boundary
    # record is EXCLUDED.
    bound = iso(before.effective_end_at)
    response = client.get(LIST_URL, {"from": bound}, **auth(token))
    rows = {r["id"] for r in response.json()["results"]}
    assert str(before.id) not in rows
    assert str(spanning.id) in rows and str(after.id) in rows

    # to = start_at < to (strict): a record starting exactly at `to` is
    # EXCLUDED.
    response = client.get(LIST_URL, {"to": iso(after.start_at)}, **auth(token))
    rows = {r["id"] for r in response.json()["results"]}
    assert str(after.id) not in rows
    assert str(spanning.id) in rows and str(before.id) in rows

    # Invalid bound pairs are rejected by the shared validated serializer.
    response = client.get(
        LIST_URL, {"from": iso(now), "to": iso(now - timedelta(hours=1))}, **auth(token)
    )
    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"


@pytest.mark.django_db
def test_status_asset_lifecycle_filters_and_pagination(client: Client) -> None:
    owner = viewer()
    other = user("readall-pager@example.com")
    target = asset("readall-pager-asset")
    now = timezone.now()
    confirmed = reservation(owner=other, target=target, start=now + timedelta(days=1))
    cancelled = reservation(
        owner=other,
        target=target,
        status=Reservation.STATUS_CANCELLED,
        start=now + timedelta(days=2),
    )
    released = reservation(
        owner=other,
        target=target,
        status=Reservation.STATUS_RELEASED,
        start=now + timedelta(days=3),
        end=now + timedelta(days=3, hours=1),
        released_at=now + timedelta(days=3, minutes=10),
    )
    token = bearer(owner, [READ_ALL])

    response = client.get(LIST_URL, {"status": "cancelled"}, **auth(token))
    rows = {r["id"] for r in response.json()["results"]}
    assert rows == {str(cancelled.id)}

    response = client.get(LIST_URL, {"lifecycle": "released"}, **auth(token))
    rows = {r["id"] for r in response.json()["results"]}
    assert rows == {str(released.id)}

    response = client.get(LIST_URL, {"asset": str(target.id)}, **auth(token))
    rows = {r["id"] for r in response.json()["results"]}
    assert rows == {str(confirmed.id), str(cancelled.id), str(released.id)}

    # Unknown asset filter values are rejected (validated serializer).
    response = client.get(LIST_URL, {"asset": "not-a-uuid"}, **auth(token))
    assert response.status_code == 400

    # Pagination envelope with limit/offset and count.
    response = client.get(LIST_URL, {"limit": "2", "offset": "0"}, **auth(token))
    body = response.json()
    assert body["count"] == 3
    assert len(body["results"]) == 2
    assert body["next"] is not None
    assert body["previous"] is None
    response = client.get(LIST_URL, {"limit": "2", "offset": "2"}, **auth(token))
    body = response.json()
    assert len(body["results"]) == 1
    assert body["previous"] is not None
    assert body["next"] is None

    # Over-limit is rejected by the shared pagination contract.
    response = client.get(LIST_URL, {"limit": "101"}, **auth(token))
    assert response.status_code == 400


@pytest.mark.django_db
def test_new_routes_are_read_only(client: Client) -> None:
    owner = viewer()
    other = user("readall-verbs@example.com")
    other_reservation = reservation(owner=other)
    token = bearer(owner, [READ_ALL])

    for method, url in [
        ("post", LIST_URL),
        ("put", f"{LIST_URL}{other_reservation.id}/"),
        ("patch", f"{LIST_URL}{other_reservation.id}/"),
        ("delete", f"{LIST_URL}{other_reservation.id}/"),
    ]:
        response = getattr(client, method)(url, **auth(token))
        assert response.status_code == 405, (method, url)
    # There is no cross-user bearer mutation surface at all: nested
    # cancel/release routes under all-reservations do not exist.
    for url in [
        f"{LIST_URL}{other_reservation.id}/cancel/",
        f"{LIST_URL}{other_reservation.id}/release/",
    ]:
        assert client.post(url, **auth(token)).status_code == 404

    # No reservation was mutated by any verb.
    other_reservation.refresh_from_db()
    assert other_reservation.status == Reservation.STATUS_CONFIRMED
    assert other_reservation.effective_end_at == other_reservation.end_at


@pytest.mark.django_db
def test_authorized_missing_uuid_uses_existing_404(client: Client) -> None:
    owner = viewer()
    token = bearer(owner, [READ_ALL])
    response = client.get(f"{LIST_URL}{uuid.uuid4()}/", **auth(token))
    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "reservation_not_found"
    assert body["correlation_id"] == response["X-Request-ID"]


@pytest.mark.django_db
def test_privileged_responses_carry_safe_cache_headers(client: Client) -> None:
    owner = viewer()
    other = user("readall-headers@example.com")
    reservation(owner=other)
    token = bearer(owner, [READ_ALL])

    success = client.get(LIST_URL, **auth(token))
    assert success.status_code == 200
    assert success.json()["count"] == 1
    assert success["Cache-Control"] == "private, no-store"
    assert "Authorization" in success.get("Vary", "")

    missing = client.get(f"{LIST_URL}{uuid.uuid4()}/", **auth(token))
    assert missing.status_code == 404
    assert missing["Cache-Control"] == "private, no-store"
    assert "Authorization" in missing.get("Vary", "")

    stripped = user("readall-403@example.com")
    grant(stripped, "view_all_reservations")
    stripped_token = bearer(stripped, [READ_ALL])
    stripped.user_permissions.clear()
    forbidden = client.get(LIST_URL, **auth(stripped_token))
    assert forbidden.status_code == 403
    assert forbidden["Cache-Control"] == "private, no-store"
    assert "Authorization" in forbidden.get("Vary", "")

    not_allowed = client.post(LIST_URL, **auth(token))
    assert not_allowed.status_code == 405
    assert not_allowed["Cache-Control"] == "private, no-store"
    assert "Authorization" in not_allowed.get("Vary", "")

    # Old endpoint headers are unchanged: no no-store on the owner list.
    owner_token = bearer(other, ["reservations:read"])
    old = client.get("/api/v1/reservations/", **auth(owner_token))
    assert old.status_code == 200
    assert old.get("Cache-Control") != "private, no-store"
    assert "Authorization" not in old.get("Vary", "")


# --- owner-only compatibility ----------------------------------------------------


@pytest.mark.django_db
def test_owner_endpoints_stay_owner_only_with_all_caps_and_both_scopes(client: Client) -> None:
    privileged = user("readall-priv@example.com", is_superuser=True)
    other = user("readall-priv-other@example.com")
    other_reservation = reservation(owner=other)
    own_reservation = reservation(owner=privileged, start=timezone.now() + timedelta(days=1))
    token = bearer(
        privileged,
        [
            "reservations:read",
            READ_ALL,
            "reservations:create",
            "reservations:cancel",
            "reservations:release",
        ],
    )

    listing = client.get("/api/v1/reservations/", **auth(token))
    body = listing.content.decode()
    assert str(own_reservation.id) in body
    assert str(other_reservation.id) not in body

    detail = client.get(f"/api/v1/reservations/{other_reservation.id}/", **auth(token))
    assert detail.status_code == 404
    assert detail.json()["code"] == "reservation_not_found"

    cancelled = client.post(
        f"/api/v1/reservations/{other_reservation.id}/cancel/",
        {},
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="readall-owner-only-cancel",
        **auth(token),
    )
    assert cancelled.status_code == 404
    released = client.post(
        f"/api/v1/reservations/{other_reservation.id}/release/",
        {},
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="readall-owner-only-release",
        **auth(token),
    )
    assert released.status_code == 404
    other_reservation.refresh_from_db()
    assert other_reservation.status == Reservation.STATUS_CONFIRMED

    # The read-all surface itself sees the other record: the two surfaces
    # are deliberately different.
    assert client.get(f"{LIST_URL}{other_reservation.id}/", **auth(token)).status_code == 200


@pytest.mark.django_db
def test_asset_inventory_and_docs_boundaries_unchanged(client: Client) -> None:
    owner = viewer()
    token = bearer(owner, [READ_ALL])
    assert client.get("/api/v1/assets/", **auth(token)).status_code == 403
    assert client.get("/api/v1/me/", **auth(token)).status_code == 200
