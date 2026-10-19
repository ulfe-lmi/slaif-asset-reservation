"""Order 051-a: issuance ceilings and token-scope authority (real PG).

New scope issuance is bounded by the owner's CURRENT capability:
read_all requires view_all_reservations, create requires book_assets.
The check runs on the fresh row-locked owner inside ``issue_api_token``;
denials write nothing. Old tokens keep their stored scopes (usable,
revocable) until a protected operation rechecks and denies. The member
token form offers only the currently issuable scopes.
"""

from __future__ import annotations

from html import unescape

import pytest
from django.contrib.auth.models import Permission
from django.test import Client

from slaif_reservation.accounts.exceptions import TOKEN_SCOPE_INVALID, ApiTokenDomainError
from slaif_reservation.accounts.models import ApiToken, User
from slaif_reservation.accounts.services import (
    issue_api_token,
    revoke_api_token,
)

READ_ALL = "reservations:read_all"
CREATE = "reservations:create"


def user(email: str, **overrides: object) -> User:
    return User.objects.create_user(email=email, password="not-a-secret", **overrides)


def permission(codename: str) -> Permission:
    return Permission.objects.get(codename=codename, content_type__app_label="reservations")


def grant(target: User, *codenames: str) -> None:
    target.user_permissions.add(*[permission(c) for c in codenames])


def expect_scope_denied(owner: User, scopes: list[str]) -> None:
    with pytest.raises(ApiTokenDomainError) as excinfo:
        issue_api_token(owner=owner, name="Denied", scopes=scopes, lifetime_days=1)
    assert excinfo.value.code == TOKEN_SCOPE_INVALID


@pytest.mark.django_db
def test_issuance_ceiling_matrix_2x2() -> None:
    # view_all only: can issue read_all, cannot issue create. No staff.
    reader = user("scope-reader@example.com")
    grant(reader, "view_all_reservations")
    assert not reader.is_staff
    issued = issue_api_token(owner=reader, name="Reader token", scopes=[READ_ALL], lifetime_days=1)
    assert issued.token.scopes == [READ_ALL]
    expect_scope_denied(reader, [CREATE])
    expect_scope_denied(reader, [READ_ALL, CREATE])

    # book only: can issue create, cannot issue read_all.
    booker = user("scope-booker@example.com")
    grant(booker, "book_assets")
    issued = issue_api_token(
        owner=booker, name="Booker token", scopes=[CREATE, "reservations:read"], lifetime_days=1
    )
    assert issued.token.scopes == [CREATE, "reservations:read"]
    expect_scope_denied(booker, [READ_ALL])

    # Both capabilities: both ceiling scopes are issuable.
    both = user("scope-both@example.com")
    grant(both, "book_assets", "view_all_reservations")
    issued = issue_api_token(
        owner=both, name="Both token", scopes=[CREATE, READ_ALL], lifetime_days=1
    )
    assert issued.token.scopes == [CREATE, READ_ALL]

    # Neither capability: neither ceiling scope is issuable.
    neither = user("scope-neither@example.com")
    expect_scope_denied(neither, [CREATE])
    expect_scope_denied(neither, [READ_ALL])

    # Un-ceilinged scopes keep their current meaning for anyone.
    issued = issue_api_token(
        owner=neither,
        name="Plain token",
        scopes=["reservations:read", "availability:read"],
        lifetime_days=1,
    )
    assert issued.token.scopes == ["availability:read", "reservations:read"]


@pytest.mark.django_db
def test_denial_writes_nothing() -> None:
    reader = user("scope-nowrite@example.com")
    from slaif_reservation.audit.models import AuditEvent

    before_audit = AuditEvent.objects.count()
    expect_scope_denied(reader, [READ_ALL])
    assert ApiToken.objects.count() == 0
    assert AuditEvent.objects.count() == before_audit

    # A valid scope in the same request still fails atomically.
    grant(reader, "view_all_reservations")
    before_audit = AuditEvent.objects.count()
    expect_scope_denied(reader, [READ_ALL, CREATE])
    assert ApiToken.objects.count() == 0
    assert AuditEvent.objects.count() == before_audit


@pytest.mark.django_db
def test_stale_user_instance_cannot_bypass_locked_issuance() -> None:
    owner = user("scope-stale@example.com")
    grant(owner, "view_all_reservations")
    # Warm the in-memory permission cache on this exact instance.
    assert owner.has_perm("reservations.view_all_reservations")

    owner.user_permissions.remove(permission("view_all_reservations"))

    # The passed instance may still carry the stale grant; the service must
    # recheck the fresh row-locked owner and deny.
    expect_scope_denied(owner, [READ_ALL])
    assert ApiToken.objects.count() == 0

    # Restoring the grant on a fresh instance issues successfully.
    fresh = User.objects.get(pk=owner.pk)
    assert not fresh.has_perm("reservations.view_all_reservations")
    grant(fresh, "view_all_reservations")
    issued = issue_api_token(
        owner=User.objects.get(pk=owner.pk), name="Restored", scopes=[READ_ALL], lifetime_days=1
    )
    assert issued.token.scopes == [READ_ALL]


@pytest.mark.django_db
def test_additive_grant_union_for_issuance() -> None:
    from django.contrib.auth.models import Group

    owner = user("scope-union@example.com")
    group_a = Group.objects.create(name="scope-group-a")
    group_a.permissions.add(permission("view_all_reservations"))
    group_b = Group.objects.create(name="scope-group-b")
    group_b.permissions.add(permission("book_assets"))
    owner.groups.add(group_a, group_b)

    # Both ceiling scopes issuable through the group union.
    issued = issue_api_token(owner=owner, name="Union", scopes=[CREATE, READ_ALL], lifetime_days=1)
    assert issued.token.scopes == [CREATE, READ_ALL]

    # Removing one group while the other grant remains retains authority.
    owner.groups.remove(group_a)
    owner.user_permissions.add(permission("view_all_reservations"))
    assert can_issue_now(owner, READ_ALL)

    # The last grant removed closes the ceiling again.
    owner.user_permissions.clear()
    expect_scope_denied(owner, [READ_ALL])


def can_issue_now(owner: User, scope: str) -> bool:
    from slaif_reservation.accounts.authorization import can_issue_scope

    return can_issue_scope(owner, scope)


@pytest.mark.django_db
def test_old_token_keeps_stored_scope_after_capability_removal() -> None:
    client = Client()
    owner = user("scope-oldtoken@example.com")
    grant(owner, "view_all_reservations", "book_assets")
    issued = issue_api_token(
        owner=owner,
        name="Old token",
        scopes=["reservations:read", CREATE, READ_ALL],
        lifetime_days=7,
    )
    owner.user_permissions.clear()

    # The stored scope rows are never mutated or backfilled.
    issued.token.refresh_from_db()
    assert issued.token.scopes == sorted([CREATE, READ_ALL, "reservations:read"])

    # Authentication and owner-only use still work...
    listing = client.get(
        "/api/v1/reservations/",
        HTTP_AUTHORIZATION=f"Bearer {issued.bearer_token}",
    )
    assert listing.status_code == 200

    # ...protected read-all use is rechecked and denied...
    cross = client.get(
        "/api/v1/all-reservations/",
        HTTP_AUTHORIZATION=f"Bearer {issued.bearer_token}",
    )
    assert cross.status_code == 403
    assert cross.json()["code"] == "permission_denied"

    # ...and the token revokes normally through the owner lifecycle.
    revoke_api_token(token=issued.token, owner=owner)
    issued.token.refresh_from_db()
    assert issued.token.revoked_at is not None


@pytest.mark.django_db
def test_superuser_issuance_keeps_django_semantics() -> None:
    admin = user("scope-admin@example.com", is_superuser=True)
    issued = issue_api_token(
        owner=admin, name="Admin token", scopes=[CREATE, READ_ALL], lifetime_days=1
    )
    assert issued.token.scopes == [CREATE, READ_ALL]


@pytest.mark.django_db
def test_inactive_and_service_owners_cannot_issue() -> None:
    inactive = user("scope-inactive@example.com", is_active=False)
    grant(inactive, "view_all_reservations")
    with pytest.raises(ApiTokenDomainError) as excinfo:
        issue_api_token(owner=inactive, name="No", scopes=[READ_ALL], lifetime_days=1)
    assert excinfo.value.code == "token_owner_invalid"

    service = user("scope-service@example.com", is_service_account=True)
    grant(service, "view_all_reservations")
    with pytest.raises(ApiTokenDomainError) as excinfo:
        issue_api_token(owner=service, name="No", scopes=[READ_ALL], lifetime_days=1)
    assert excinfo.value.code == "token_owner_invalid"


# --- member token form: only currently issuable choices -----------------------


def _form_choices(client: Client, owner: User) -> tuple[list[str], str]:
    client.force_login(owner)
    html = unescape(client.get("/tokens/new/").content.decode())
    choices: list[str] = []
    for scope in (
        "assets:read",
        "availability:read",
        "reservations:read",
        CREATE,
        "reservations:cancel",
        "reservations:release",
        READ_ALL,
    ):
        if f'value="{scope}"' in html:
            choices.append(scope)
    return choices, html


@pytest.mark.django_db
def test_form_offers_only_currently_issuable_scopes(client: Client) -> None:
    reader = user("scope-ui-reader@example.com")
    grant(reader, "view_all_reservations")
    booker = user("scope-ui-booker@example.com")
    grant(booker, "book_assets")
    both = user("scope-ui-both@example.com")
    grant(both, "book_assets", "view_all_reservations")

    reader_choices, _ = _form_choices(client, reader)
    assert READ_ALL in reader_choices
    assert CREATE not in reader_choices
    booker_choices, _ = _form_choices(client, booker)
    assert CREATE in booker_choices
    assert READ_ALL not in booker_choices
    both_choices, html = _form_choices(client, both)
    assert READ_ALL in both_choices
    assert CREATE in both_choices

    # The new scope carries its human label and read-only effect help.
    assert "Read other people's reservations (read-only)" in html
    assert "Read-only: lets the token list and inspect other people's reservations" in html
    assert "while your account currently has the view-all-reservations capability" in html


@pytest.mark.django_db
def test_form_forged_and_revoked_post_cannot_create(client: Client) -> None:
    owner = user("scope-ui-forged@example.com")
    grant(owner, "book_assets", "view_all_reservations")
    client.force_login(owner)
    # The GET form offered both ceiling scopes...
    assert client.get("/tokens/new/").status_code == 200

    # ...then the capability is revoked before the POST (GET -> POST race).
    owner.user_permissions.clear()

    response = client.post(
        "/tokens/new/",
        {"name": "Forged race", "scopes": [READ_ALL], "lifetime_days": "7"},
    )
    assert response.status_code == 200
    assert "scopes" in response.context["form"].errors
    assert ApiToken.objects.count() == 0

    # Even bypassing the form, the service's fresh locked-owner check
    # denies the same request (authoritative boundary).
    expect_scope_denied(User.objects.get(pk=owner.pk), [READ_ALL])
    assert ApiToken.objects.count() == 0

    # A scope that was never issuable is rejected the same way.
    response = client.post(
        "/tokens/new/",
        {
            "name": "Forged unknown",
            "scopes": ["reservations:read_all", "admin:*"],
            "lifetime_days": "7",
        },
    )
    assert response.status_code == 200
    assert "scopes" in response.context["form"].errors
    assert ApiToken.objects.count() == 0


@pytest.mark.django_db
def test_owner_list_and_revoke_work_after_loosing_rights(client: Client) -> None:
    owner = user("scope-ui-lost@example.com")
    grant(owner, "view_all_reservations")
    issued = issue_api_token(
        owner=owner, name="Lost rights token", scopes=[READ_ALL], lifetime_days=7
    )
    owner.user_permissions.clear()

    client.force_login(owner)
    listing = client.get("/tokens/")
    assert listing.status_code == 200
    assert issued.token.display_prefix in listing.content.decode()
    assert issued.bearer_token not in listing.content.decode()

    revoke = client.post(f"/tokens/{issued.token.id}/revoke/")
    assert revoke.status_code == 302
    issued.token.refresh_from_db()
    assert issued.token.revoked_at is not None
