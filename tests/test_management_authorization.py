"""Granular management authority (order 050-a, issue #103).

Real Permission rows, real HTTP and service calls against PostgreSQL:
the 17-route /manage/ capability matrix, shared row-locked service guards,
partial-access UI privacy, the All reservations browser, blackout preview
privacy and deliberate-upgrade boundaries.
"""

from __future__ import annotations

from datetime import UTC, timedelta

import pytest
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from django.utils import timezone

from slaif_reservation.accounts.models import User
from slaif_reservation.accounts.services import issue_api_token
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.reservations.exceptions import (
    POLICY_MUTATION_NOT_AUTHORIZED,
    RESERVATION_NOT_OWNED,
    ReservationDomainError,
)
from slaif_reservation.reservations.models import (
    MaintenanceBlackout,
    Reservation,
    ReservationPolicy,
)
from slaif_reservation.reservations.services import (
    cancel_reservation,
    create_blackout,
    create_policy,
    create_reservation,
    deactivate_blackout,
    deactivate_policy,
    update_policy,
)

CANARY_EMAIL = "overlap-owner-canary@example.com"
CANARY_PURPOSE = "canary-purpose-must-not-leak"
CANARY_NAME = "Overlap Owner Canary"

ALL_CAPABILITIES = (
    "view_all_reservations",
    "cancel_others_reservations",
    "release_others_reservations",
    "view_booking_policies",
    "manage_booking_policies",
    "view_maintenance_blackouts",
    "manage_maintenance_blackouts",
    "view_audit_history",
    "export_audit_history",
)

#: The full 17-route inventory: route name -> capability sets. A principal
#: may use the route iff they hold at least one named codename (SAR-048:
#: manage capabilities include their module's read interface, never the
#: reverse; read-all is distinct from model View; mutation caps imply no
#: read).
ROUTE_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "dashboard": ALL_CAPABILITIES,
    "policy-list": ("view_booking_policies", "manage_booking_policies"),
    "policy-detail": ("view_booking_policies", "manage_booking_policies"),
    "policy-create": ("manage_booking_policies",),
    "policy-update": ("manage_booking_policies",),
    "policy-deactivate": ("manage_booking_policies",),
    "blackout-list": ("view_maintenance_blackouts", "manage_maintenance_blackouts"),
    "blackout-detail": ("view_maintenance_blackouts", "manage_maintenance_blackouts"),
    "blackout-create": ("manage_maintenance_blackouts",),
    "blackout-deactivate": ("manage_maintenance_blackouts",),
    "reservation-list": ("view_all_reservations",),
    "reservation-detail": ("view_all_reservations",),
    "reservation-cancel": ("cancel_others_reservations",),
    "reservation-release": ("release_others_reservations",),
    "audit-list": ("view_audit_history",),
    "audit-detail": ("view_audit_history",),
    "audit-export": ("export_audit_history",),
}

POST_ONLY = {
    "policy-deactivate",
    "blackout-deactivate",
    "reservation-cancel",
    "reservation-release",
}


def permission(codename: str) -> Permission:
    return Permission.objects.get(codename=codename, content_type__app_label="reservations")


def grant(user: User, *codenames: str) -> User:
    user.user_permissions.add(*[permission(c) for c in codenames])
    return user


def revoke(user: User, *codenames: str) -> User:
    user.user_permissions.remove(*[permission(c) for c in codenames])
    return user


@pytest.fixture
def member_booker() -> User:
    user = User.objects.create_user(
        email="member-050@example.com",
        password="not-a-secret",
        display_name="Member",
    )
    return grant(user, "book_assets")


@pytest.fixture
def staff_only() -> User:
    return User.objects.create_user(
        email="staffonly-050@example.com",
        password="not-a-secret",
        display_name="Staff Only",
        is_staff=True,
    )


@pytest.fixture
def staff_admin_view() -> User:
    """Staff with Administration model View permissions, no app grants."""
    user = User.objects.create_user(
        email="staffview-050@example.com",
        password="not-a-secret",
        display_name="Staff AdminView",
        is_staff=True,
    )
    for model in (Reservation, ReservationPolicy, MaintenanceBlackout, AuditEvent):
        ct = ContentType.objects.get_for_model(model)
        user.user_permissions.add(
            Permission.objects.get(codename=f"view_{model._meta.model_name}", content_type=ct)
        )
    return user


@pytest.fixture
def superuser() -> User:
    return User.objects.create_superuser(
        email="super-050@example.com",
        password="not-a-secret",
        display_name="Super",
    )


@pytest.fixture
def service_account() -> User:
    return User.objects.create_user(
        email="svc-050@example.com",
        password="not-a-secret",
        is_staff=True,
        is_service_account=True,
    )


@pytest.fixture
def machine() -> Asset:
    return Asset.objects.create(
        slug="authority-machine",
        name="Authority Machine",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
        verification_required=False,
    )


@pytest.fixture
def asset(machine: Asset) -> Asset:
    return Asset.objects.create(
        slug="authority-gpu",
        name="Authority GPU",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
        verification_required=False,
    )


@pytest.fixture
def policy(asset: Asset) -> ReservationPolicy:
    return ReservationPolicy.objects.create(
        name="Authority policy",
        asset=asset,
        min_duration_minutes=15,
        max_duration_minutes=240,
        booking_horizon_days=30,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=20,
        max_concurrent_per_principal=5,
        purpose_required=False,
    )


@pytest.fixture
def owner() -> User:
    return User.objects.create_user(
        email=CANARY_EMAIL,
        password="not-a-secret",
        display_name=CANARY_NAME,
    )


@pytest.fixture
def other_owner() -> User:
    return User.objects.create_user(
        email="second-owner-050@example.com",
        password="not-a-secret",
        display_name="Second Owner",
    )


@pytest.fixture
def reservable_reservation(owner: User, asset: Asset) -> Reservation:
    start = timezone.now() + timedelta(days=5, hours=3)
    return make_reservation(owner, asset, start, start + timedelta(hours=1), purpose=CANARY_PURPOSE)


@pytest.fixture
def blackout(policy: ReservationPolicy, staff_only: User) -> MaintenanceBlackout:
    start = timezone.now() + timedelta(days=9, hours=3)
    return MaintenanceBlackout.objects.create(
        asset=policy.asset,
        created_by=staff_only,
        reason="synthetic blackout",
        start_at=start,
        end_at=start + timedelta(hours=1),
        active=True,
    )


@pytest.fixture
def audit_event(staff_only: User, asset: Asset) -> AuditEvent:
    return AuditEvent.objects.create(
        occurred_at=timezone.now(),
        actor_user=staff_only,
        action=AuditEvent.ACTION_BLACKOUT_CREATED,
        target_type="maintenance_blackout",
        target_id=asset.id,
        correlation_id=asset.id,
        source=AuditEvent.SOURCE_ADMIN,
        metadata={"marker": "050"},
    )


def make_reservation(
    owner: User,
    target: Asset,
    start: timezone.datetime,
    end: timezone.datetime,
    *,
    status: str = Reservation.STATUS_CONFIRMED,
    purpose: str = "",
) -> Reservation:
    return Reservation.objects.create(
        asset=target,
        requested_by_user=owner,
        source=Reservation.SOURCE_WEB,
        status=status,
        start_at=start,
        end_at=end,
        effective_end_at=end,
        released_at=(
            start + timedelta(minutes=5) if status == Reservation.STATUS_RELEASED else None
        ),
        cancelled_at=(
            start - timedelta(minutes=5) if status == Reservation.STATUS_CANCELLED else None
        ),
        cancelled_by=owner if status == Reservation.STATUS_CANCELLED else None,
        cancellation_reason="" if status != Reservation.STATUS_CANCELLED else "gone",
        purpose=purpose,
    )


def route_paths(
    policy: ReservationPolicy,
    blackout: MaintenanceBlackout,
    reservation: Reservation,
    event: AuditEvent,
) -> dict[str, str]:
    return {
        "dashboard": "/manage/",
        "policy-list": "/manage/policies/",
        "policy-detail": f"/manage/policies/{policy.id}/",
        "policy-create": "/manage/policies/new/",
        "policy-update": f"/manage/policies/{policy.id}/edit/",
        "policy-deactivate": f"/manage/policies/{policy.id}/deactivate/",
        "blackout-list": "/manage/blackouts/",
        "blackout-detail": f"/manage/blackouts/{blackout.id}/",
        "blackout-create": "/manage/blackouts/new/",
        "blackout-deactivate": f"/manage/blackouts/{blackout.id}/deactivate/",
        "reservation-list": "/manage/reservations/",
        "reservation-detail": f"/manage/reservations/{reservation.id}/",
        "reservation-cancel": f"/manage/reservations/{reservation.id}/cancel/",
        "reservation-release": f"/manage/reservations/{reservation.id}/release/",
        "audit-list": "/manage/audit/",
        "audit-detail": f"/manage/audit/{event.id}/",
        "audit-export": "/manage/audit/export.csv",
    }


def _policy_payload(asset: Asset, **overrides: object) -> dict[str, str]:
    payload = {
        "name": "050 policy form",
        "asset": str(asset.id),
        "min_duration_minutes": "15",
        "max_duration_minutes": "120",
        "booking_horizon_days": "30",
        "min_lead_minutes": "0",
        "cancellation_cutoff_minutes": "0",
        "max_upcoming_per_principal": "10",
        "max_concurrent_per_principal": "2",
    }
    payload.update(overrides)
    return payload


def _blackout_payload(
    asset: Asset, start: timezone.datetime, end: timezone.datetime
) -> dict[str, str]:
    return {
        "asset": str(asset.id),
        "timezone": "UTC",
        "start": start.astimezone(UTC).replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M"),
        "end": end.astimezone(UTC).replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M"),
        "reason": "050 blackout",
    }


@pytest.mark.django_db
def test_route_capability_matrix_nonstaff(
    client: Client,
    member_booker: User,
    staff_only: User,
    staff_admin_view: User,
    superuser: User,
    service_account: User,
    policy: ReservationPolicy,
    blackout: MaintenanceBlackout,
    reservable_reservation: Reservation,
    audit_event: AuditEvent,
) -> None:
    paths = route_paths(policy, blackout, reservable_reservation, audit_event)
    assert set(paths) == set(ROUTE_CAPABILITIES)  # the full 17-route inventory

    # Anonymous: login redirect everywhere, no disclosure.
    for path in paths.values():
        response = client.get(path)
        assert response.status_code == 302
        assert "/login/" in response["Location"]

    # book_assets alone: a booking capability is NOT management access.
    client.force_login(member_booker)
    for name, path in paths.items():
        assert client.get(path).status_code == 403, (name,)
    client.logout()

    # Staff alone, and staff with unrelated Administration model Views.
    for denied in (staff_only, staff_admin_view):
        client.force_login(denied)
        for name, path in paths.items():
            assert client.get(path).status_code == 403, (denied.email, name)
        client.logout()

    # A service account holding every capability still fails the human gate.
    grant(service_account, *ALL_CAPABILITIES)
    client.force_login(service_account)
    for name, path in paths.items():
        assert client.get(path).status_code == 403, (name,)
    client.logout()

    # Trusted active superusers keep Django permission semantics everywhere
    # (GET on POST-only routes is still 405, not 200).
    client.force_login(superuser)
    for name, path in paths.items():
        response = client.get(path)
        expected = 405 if name in POST_ONLY else 200
        assert response.status_code == expected, (name, response.status_code)
    client.logout()

    # Each single capability admits exactly its own routes and nothing else.
    for codename in ALL_CAPABILITIES:
        holder = User.objects.create_user(
            email=f"cap-{codename}-050@example.com",
            password="not-a-secret",
            display_name=codename,
        )
        grant(holder, codename)
        client.force_login(holder)
        for name, required in ROUTE_CAPABILITIES.items():
            if name in POST_ONLY:
                # GET on a POST-only route: 405 for holders, 403 for the rest
                # (the capability check runs before the verb check).
                expected = 405 if codename in required else 403
            else:
                expected = 200 if codename in required else 403
            response = client.get(paths[name])
            assert response.status_code == expected, (codename, name, response.status_code)
            if name in POST_ONLY and codename not in required:
                assert client.post(paths[name], {}).status_code == 403, (codename, name)
        client.logout()


@pytest.mark.django_db
def test_inactive_humans_redirect_to_login(
    client: Client,
    policy: ReservationPolicy,
    blackout: MaintenanceBlackout,
    reservable_reservation: Reservation,
    audit_event: AuditEvent,
) -> None:
    paths = route_paths(policy, blackout, reservable_reservation, audit_event)
    inactive = User.objects.create_user(
        email="inactive-050@example.com",
        password="not-a-secret",
        is_staff=True,
        is_active=False,
    )
    grant(inactive, *ALL_CAPABILITIES)
    inactive_superuser = User.objects.create_user(
        email="inactivesuper-050@example.com",
        password="not-a-secret",
        is_staff=True,
        is_superuser=True,
        is_active=False,
    )
    for denied in (inactive, inactive_superuser):
        client.force_login(denied)
        for path in paths.values():
            response = client.get(path)
            assert response.status_code == 302
            assert "/login/" in response["Location"]
        client.logout()


@pytest.mark.django_db
def test_group_individual_union_and_removal_take_effect_immediately(
    client: Client,
    policy: ReservationPolicy,
    blackout: MaintenanceBlackout,
    reservable_reservation: Reservation,
    audit_event: AuditEvent,
) -> None:
    paths = route_paths(policy, blackout, reservable_reservation, audit_event)
    user = User.objects.create_user(
        email="union-050@example.com", password="not-a-secret", display_name="Union"
    )
    group_policies = Group.objects.create(name="050 policy readers")
    group_policies.permissions.add(permission("view_booking_policies"))
    group_blackouts = Group.objects.create(name="050 blackout managers")
    group_blackouts.permissions.add(permission("manage_maintenance_blackouts"))
    user.groups.add(group_policies, group_blackouts)
    grant(user, "view_audit_history")

    client.force_login(user)
    assert client.get(paths["policy-list"]).status_code == 200
    assert client.get(paths["policy-create"]).status_code == 403
    assert client.get(paths["blackout-list"]).status_code == 200
    assert client.get(paths["blackout-create"]).status_code == 200
    assert client.get(paths["audit-list"]).status_code == 200
    assert client.get(paths["reservation-list"]).status_code == 403

    # Group removal: the SAME session loses that module immediately (there
    # is no process-global grant cache).
    user.groups.remove(group_policies)
    assert client.get(paths["policy-list"]).status_code == 403
    assert client.get(paths["blackout-create"]).status_code == 200
    assert client.get(paths["audit-list"]).status_code == 200

    revoke(user, "view_audit_history")
    assert client.get(paths["audit-list"]).status_code == 403
    client.logout()


@pytest.mark.django_db
def test_direct_gets_denied_without_record_disclosure(
    client: Client,
    staff_only: User,
    reservable_reservation: Reservation,
    audit_event: AuditEvent,
) -> None:
    """A hidden button cannot authorize a direct GET on protected records."""
    client.force_login(staff_only)
    for path in (
        f"/manage/reservations/{reservable_reservation.id}/",
        f"/manage/audit/{audit_event.id}/",
        "/manage/audit/export.csv",
    ):
        response = client.get(path)
        assert response.status_code == 403
        assert CANARY_EMAIL.encode() not in response.content
        assert CANARY_PURPOSE.encode() not in response.content
        assert b"canary" not in response.content.lower()


@pytest.mark.django_db
def test_forged_mutation_posts_denied_and_wrong_capability_denied(
    owner: User,
    asset: Asset,
    policy: ReservationPolicy,
    blackout: MaintenanceBlackout,
) -> None:
    start = timezone.now() + timedelta(days=4, hours=3)
    reservation = make_reservation(owner, asset, start, start + timedelta(hours=1))
    releasable_start = timezone.now() - timedelta(minutes=30)
    releasable = make_reservation(
        owner, asset, releasable_start, releasable_start + timedelta(hours=2)
    )
    client = Client(enforce_csrf_checks=True)

    # Read-all viewer: sees the detail but every forged mutation is refused.
    viewer = grant(
        User.objects.create_user(email="viewer-050@example.com", password="not-a-secret"),
        "view_all_reservations",
    )
    client.force_login(viewer)
    assert client.get(f"/manage/reservations/{reservation.id}/").status_code == 200
    csrf = client.cookies["csrftoken"].value
    for path in (
        f"/manage/reservations/{reservation.id}/cancel/",
        f"/manage/reservations/{releasable.id}/release/",
    ):
        response = client.post(path, {"reason": "forged"}, HTTP_X_CSRFTOKEN=csrf)
        assert response.status_code == 403
    reservation.refresh_from_db()
    releasable.refresh_from_db()
    assert reservation.status == Reservation.STATUS_CONFIRMED
    assert releasable.status == Reservation.STATUS_CONFIRMED
    assert AuditEvent.objects.count() == 0
    client.logout()

    # Wrong mutation capability: cancel-only cannot release.
    canceller = grant(
        User.objects.create_user(email="canceller-050@example.com", password="not-a-secret"),
        "cancel_others_reservations",
    )
    client.force_login(canceller)
    assert client.post(f"/manage/reservations/{releasable.id}/release/", {}).status_code == 403
    client.logout()

    # Policy manager cannot manage blackouts; blackout manager cannot manage
    # policies (manage caps never imply one another).
    policy_manager = grant(
        User.objects.create_user(email="pmgr-050@example.com", password="not-a-secret"),
        "manage_booking_policies",
    )
    blackout_manager = grant(
        User.objects.create_user(email="bmgr-050@example.com", password="not-a-secret"),
        "manage_maintenance_blackouts",
    )
    client.force_login(policy_manager)
    assert client.post(f"/manage/blackouts/{blackout.id}/deactivate/", {}).status_code == 403
    assert (
        client.post(
            "/manage/blackouts/new/",
            _blackout_payload(asset, start, start + timedelta(hours=1)),
        ).status_code
        == 403
    )
    client.logout()
    client.force_login(blackout_manager)
    assert client.post(f"/manage/policies/{policy.id}/deactivate/", {}).status_code == 403
    assert client.post("/manage/policies/new/", _policy_payload(asset)).status_code == 403
    assert (
        client.post(
            f"/manage/policies/{policy.id}/edit/", _policy_payload(asset, name="Nope")
        ).status_code
        == 403
    )
    blackout.refresh_from_db()
    policy.refresh_from_db()
    assert blackout.active and policy.active


@pytest.mark.django_db
def test_mutator_only_success_without_read_all_and_safe_redirect(
    owner: User, asset: Asset, policy: ReservationPolicy
) -> None:
    start = timezone.now() + timedelta(days=4, hours=3)
    reservation = make_reservation(owner, asset, start, start + timedelta(hours=1))
    client = Client(enforce_csrf_checks=True)
    canceller = grant(
        User.objects.create_user(email="mutator-050@example.com", password="not-a-secret"),
        "cancel_others_reservations",
    )
    client.force_login(canceller)

    # No list/detail access at all...
    assert client.get("/manage/reservations/").status_code == 403
    assert client.get(f"/manage/reservations/{reservation.id}/").status_code == 403

    # ...but the authorized mutation by known UUID succeeds with a SAFE
    # redirect to the management landing (never the private detail).
    csrf = client.get("/manage/").cookies["csrftoken"].value
    response = client.post(
        f"/manage/reservations/{reservation.id}/cancel/",
        {"reason": "authorized"},
        HTTP_X_CSRFTOKEN=csrf,
    )
    assert response.status_code == 302
    assert response["Location"] == "/manage/"
    reservation.refresh_from_db()
    assert reservation.status == Reservation.STATUS_CANCELLED
    assert reservation.cancelled_by_id == canceller.id
    assert AuditEvent.objects.filter(action=AuditEvent.ACTION_RESERVATION_CANCELLED).count() == 1

    # Neither the mutation response nor the landing discloses owner data.
    assert CANARY_EMAIL.encode() not in response.content
    landing = client.get("/manage/")
    assert landing.status_code == 200
    assert CANARY_EMAIL.encode() not in landing.content
    assert CANARY_PURPOSE.encode() not in landing.content
    # Direct GET on the detail stays refused afterwards.
    assert client.get(f"/manage/reservations/{reservation.id}/").status_code == 403
    client.logout()

    # Release-only analogue: safe redirect, owner data never rendered.
    active_now = make_reservation(
        owner,
        asset,
        timezone.now() - timedelta(minutes=30),
        timezone.now() + timedelta(minutes=30),
    )
    releaser = grant(
        User.objects.create_user(email="releaser-050@example.com", password="not-a-secret"),
        "release_others_reservations",
    )
    client.force_login(releaser)
    assert client.get(f"/manage/reservations/{active_now.id}/").status_code == 403
    csrf = client.get("/manage/").cookies["csrftoken"].value
    response = client.post(
        f"/manage/reservations/{active_now.id}/release/", {}, HTTP_X_CSRFTOKEN=csrf
    )
    assert response.status_code == 302
    assert response["Location"] == "/manage/"
    active_now.refresh_from_db()
    assert active_now.status == Reservation.STATUS_RELEASED
    assert CANARY_EMAIL.encode() not in response.content


@pytest.mark.django_db
def test_service_guards_recheck_after_revocation(
    owner: User, asset: Asset, policy: ReservationPolicy
) -> None:
    manager = grant(
        User.objects.create_user(email="svc-mgr-050@example.com", password="not-a-secret"),
        "manage_booking_policies",
        "manage_maintenance_blackouts",
        "cancel_others_reservations",
    )

    # Policy mutation works; after revocation the same principal is refused
    # at the row-locked recheck, with no audit on denial.
    result = create_policy(
        actor_user=manager,
        name="050 service policy",
        asset=None,
        min_duration_minutes=15,
        max_duration_minutes=120,
        booking_horizon_days=30,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=10,
        max_concurrent_per_principal=2,
    )
    audit_count = AuditEvent.objects.count()
    revoke(manager, "manage_booking_policies")
    with pytest.raises(
        ReservationDomainError, check=lambda e: e.code == POLICY_MUTATION_NOT_AUTHORIZED
    ):
        update_policy(policy=result.policy, actor_user=manager, name="denied")
    assert AuditEvent.objects.count() == audit_count

    # Blackout guard: the same revocation pattern.
    start = timezone.now() + timedelta(days=10, hours=3)
    blackout = create_blackout(
        asset=asset,
        actor_user=manager,
        reason="service blackout",
        start_at=start,
        end_at=start + timedelta(hours=1),
    ).blackout
    revoke(manager, "manage_maintenance_blackouts")
    with pytest.raises(
        ReservationDomainError, check=lambda e: e.code == POLICY_MUTATION_NOT_AUTHORIZED
    ):
        deactivate_blackout(blackout=blackout, actor_user=manager)
    blackout.refresh_from_db()
    assert blackout.active

    # Cross-user cancel works; after revocation the same principal can no
    # longer cancel someone else's reservation.
    start2 = timezone.now() + timedelta(days=7, hours=3)
    reservation = make_reservation(owner, asset, start2, start2 + timedelta(hours=1))
    cancel_reservation(
        reservation=reservation,
        requested_by_user=manager,
        reason="first",
        source=Reservation.SOURCE_ADMIN,
    )
    reservation.refresh_from_db()
    assert reservation.status == Reservation.STATUS_CANCELLED
    start3 = timezone.now() + timedelta(days=8, hours=3)
    reservation2 = make_reservation(owner, asset, start3, start3 + timedelta(hours=1))
    revoke(manager, "cancel_others_reservations")
    with pytest.raises(ReservationDomainError, check=lambda e: e.code == RESERVATION_NOT_OWNED):
        cancel_reservation(
            reservation=reservation2,
            requested_by_user=manager,
            reason="second",
            source=Reservation.SOURCE_ADMIN,
        )
    reservation2.refresh_from_db()
    assert reservation2.status == Reservation.STATUS_CONFIRMED


@pytest.mark.django_db
def test_owner_lifecycle_retained_after_capability_and_group_loss(
    member_booker: User, asset: Asset, policy: ReservationPolicy
) -> None:
    start = timezone.now() + timedelta(days=3, hours=3)
    reservation = make_reservation(member_booker, asset, start, start + timedelta(hours=1))
    # Lose every capability and any group membership: owner rights remain.
    revoke(member_booker, "book_assets")
    member_booker.groups.clear()
    member_booker.refresh_from_db()

    cancel_reservation(
        reservation=reservation,
        requested_by_user=member_booker,
        reason="owner cancel",
        source=Reservation.SOURCE_WEB,
    )
    reservation.refresh_from_db()
    assert reservation.status == Reservation.STATUS_CANCELLED
    assert reservation.cancelled_by_id == member_booker.id

    active = make_reservation(
        member_booker,
        asset,
        timezone.now() - timedelta(minutes=10),
        timezone.now() + timedelta(minutes=10),
    )
    from slaif_reservation.reservations.services import release_reservation

    release_reservation(
        reservation=active,
        requested_by_user=member_booker,
        source=Reservation.SOURCE_WEB,
    )
    active.refresh_from_db()
    assert active.status == Reservation.STATUS_RELEASED


@pytest.mark.django_db
def test_service_account_owner_and_superuser_boundaries(
    asset: Asset,
) -> None:
    # A service account can never use the owner path or hold capabilities.
    svc = User.objects.create_user(
        email="svc-owner-050@example.com",
        password="not-a-secret",
        is_service_account=True,
    )
    grant(svc, "cancel_others_reservations")
    human = User.objects.create_user(email="human-050@example.com", password="not-a-secret")
    start = timezone.now() + timedelta(days=3, hours=3)
    reservation = make_reservation(human, asset, start, start + timedelta(hours=1))
    with pytest.raises(ReservationDomainError, check=lambda e: e.code == RESERVATION_NOT_OWNED):
        cancel_reservation(
            reservation=reservation,
            requested_by_user=svc,
            source=Reservation.SOURCE_ADMIN,
        )
    # Service-account superuser: human eligibility still wins.
    svc_super = User.objects.create_user(
        email="svcsuper-050@example.com",
        password="not-a-secret",
        is_staff=True,
        is_superuser=True,
        is_service_account=True,
    )
    with pytest.raises(
        ReservationDomainError, check=lambda e: e.code == POLICY_MUTATION_NOT_AUTHORIZED
    ):
        create_policy(
            actor_user=svc_super,
            name="svc super",
            asset=None,
            min_duration_minutes=15,
            max_duration_minutes=120,
            booking_horizon_days=1,
            min_lead_minutes=0,
            cancellation_cutoff_minutes=0,
            max_upcoming_per_principal=1,
            max_concurrent_per_principal=1,
        )


@pytest.mark.django_db
def test_audit_rollback_and_domain_invariants_preserved(
    monkeypatch: pytest.MonkeyPatch,
    owner: User,
    asset: Asset,
    policy: ReservationPolicy,
) -> None:
    manager = grant(
        User.objects.create_user(email="rb-050@example.com", password="not-a-secret"),
        "manage_booking_policies",
        "manage_maintenance_blackouts",
        "cancel_others_reservations",
    )

    def fail_audit(*args: object, **kwargs: object) -> None:
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr("slaif_reservation.reservations.services.append_audit_event", fail_audit)
    audit_count = AuditEvent.objects.count()

    with pytest.raises(RuntimeError):
        create_policy(
            actor_user=manager,
            name="rollback",
            asset=None,
            min_duration_minutes=15,
            max_duration_minutes=120,
            booking_horizon_days=1,
            min_lead_minutes=0,
            cancellation_cutoff_minutes=0,
            max_upcoming_per_principal=1,
            max_concurrent_per_principal=1,
        )
    assert not ReservationPolicy.objects.filter(name="rollback").exists()

    with pytest.raises(RuntimeError):
        update_policy(policy=policy, actor_user=manager, name="denied rollback")
    policy.refresh_from_db()
    assert policy.name == "Authority policy"

    start = timezone.now() + timedelta(days=11, hours=3)
    with pytest.raises(RuntimeError):
        create_blackout(
            asset=asset,
            actor_user=manager,
            reason="x",
            start_at=start,
            end_at=start + timedelta(hours=1),
        )
    assert MaintenanceBlackout.objects.count() == 0

    with pytest.raises(RuntimeError):
        deactivate_policy(policy=policy, actor_user=manager)
    policy.refresh_from_db()
    assert policy.active
    assert AuditEvent.objects.count() == audit_count
    monkeypatch.undo()

    # Cutoff and conflict domain rules are unchanged under the new authority.
    update_policy(policy=policy, actor_user=manager, cancellation_cutoff_minutes=999999)
    start2 = timezone.now() + timedelta(days=12, hours=3)
    reservation = make_reservation(owner, asset, start2, start2 + timedelta(hours=1))
    manager2 = grant(
        User.objects.create_user(email="rb2-050@example.com", password="not-a-secret"),
        "cancel_others_reservations",
    )
    with pytest.raises(ReservationDomainError, check=lambda e: e.code == "cancellation_cutoff"):
        cancel_reservation(
            reservation=reservation,
            requested_by_user=manager2,
            source=Reservation.SOURCE_ADMIN,
        )
    # Two overlapping bookings still fail closed on PostgreSQL exclusion.
    grant(owner, "book_assets")
    base = timezone.now() + timedelta(days=13, hours=2)
    create_reservation(
        asset=asset,
        requested_by_user=owner,
        start_at=base,
        end_at=base + timedelta(hours=1),
        purpose="",
    )
    with pytest.raises(ReservationDomainError, check=lambda e: e.code == "reservation_conflict"):
        create_reservation(
            asset=asset,
            requested_by_user=owner,
            start_at=base + timedelta(minutes=30),
            end_at=base + timedelta(hours=2),
            purpose="",
        )


@pytest.mark.django_db
def test_bearer_api_stays_owner_only_even_for_privileged_principals(
    client: Client, asset: Asset
) -> None:
    privileged = User.objects.create_superuser(
        email="priv-api-050@example.com", password="not-a-secret"
    )
    grant(privileged, *ALL_CAPABILITIES)
    other = User.objects.create_user(email="other-api-050@example.com", password="not-a-secret")
    start = timezone.now() + timedelta(days=3, hours=3)
    other_reservation = make_reservation(other, asset, start, start + timedelta(hours=1))

    token = issue_api_token(
        owner=privileged,
        name="050 api",
        scopes=["reservations:read", "reservations:cancel"],
        lifetime_days=1,
    ).bearer_token
    auth = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    listing = client.get("/api/v1/reservations/", **auth)
    assert listing.status_code == 200
    body = listing.content.decode()
    assert str(other_reservation.id) not in body
    detail = client.get(f"/api/v1/reservations/{other_reservation.id}/", **auth)
    assert detail.status_code == 404
    assert detail.json()["code"] == "reservation_not_found"

    cancel = client.post(
        f"/api/v1/reservations/{other_reservation.id}/cancel/",
        data={"reason": "no"},
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="050-api-cancel",
        **auth,
    )
    assert cancel.status_code == 404
    other_reservation.refresh_from_db()
    assert other_reservation.status == Reservation.STATUS_CONFIRMED


@pytest.mark.django_db
def test_dashboard_partial_access_no_unauthorized_counts_links_or_actions(
    client: Client,
    policy: ReservationPolicy,
    blackout: MaintenanceBlackout,
    reservable_reservation: Reservation,
    audit_event: AuditEvent,
) -> None:
    policy_view = grant(
        User.objects.create_user(email="pv-050@example.com", password="not-a-secret"),
        "view_booking_policies",
    )
    client.force_login(policy_view)
    response = client.get("/manage/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "/manage/policies/" in content
    assert "All reservations" not in content
    assert "/manage/blackouts/" not in content
    assert "/manage/audit/" not in content
    assert "/manage/reservations/" not in content
    assert str(blackout.id) not in content
    assert str(reservable_reservation.id) not in content
    client.logout()

    export_only = grant(
        User.objects.create_user(email="eo-050@example.com", password="not-a-secret"),
        "export_audit_history",
    )
    client.force_login(export_only)
    response = client.get("/manage/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "/manage/audit/export.csv" in content
    # No audit browser list link anywhere on the landing.
    assert 'href="/manage/audit/"' not in content
    assert "Export CSV" in content
    # The export form carries the existing filter fields, so the cap is
    # usable without the audit browser.
    for name in (
        "action",
        "target_type",
        "actor",
        "source",
        "correlation_id",
        "occurred_from",
        "occurred_to",
    ):
        assert f'name="{name}"' in content, name
    client.logout()

    cancel_only = grant(
        User.objects.create_user(email="co-050@example.com", password="not-a-secret"),
        "cancel_others_reservations",
    )
    client.force_login(cancel_only)
    response = client.get("/manage/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "limited management access" in content
    assert str(policy.id) not in content
    assert str(reservable_reservation.id) not in content
    client.logout()


@pytest.mark.django_db
def test_blackout_preview_privacy_without_read_all(
    client: Client, asset: Asset, owner: User
) -> None:
    blackout_manager = grant(
        User.objects.create_user(email="bmp-050@example.com", password="not-a-secret"),
        "manage_maintenance_blackouts",
    )
    start = timezone.now() + timedelta(days=2, hours=3)
    overlapping = make_reservation(
        owner, asset, start, start + timedelta(hours=1), purpose=CANARY_PURPOSE
    )

    client.force_login(blackout_manager)
    # GET form: no affected preview rows before submission.
    response = client.get("/manage/blackouts/new/")
    assert response.status_code == 200
    assert CANARY_EMAIL.encode() not in response.content
    assert CANARY_NAME.encode() not in response.content

    # Unconfirmed POST: safe overlap error, still no owner data.
    payload = _blackout_payload(asset, start, start + timedelta(hours=1))
    assert "confirm_overlaps" not in payload
    response = client.post("/manage/blackouts/new/", payload)
    assert response.status_code == 200
    assert "Confirm creation" in response.content.decode()
    assert CANARY_EMAIL.encode() not in response.content
    assert CANARY_NAME.encode() not in response.content
    assert str(overlapping.id) not in response.content.decode()
    assert MaintenanceBlackout.objects.count() == 0

    # Confirmed POST: created; no owner data in the success response.
    response = client.post("/manage/blackouts/new/", payload | {"confirm_overlaps": "on"})
    assert response.status_code == 302
    blackout = MaintenanceBlackout.objects.get()
    assert blackout.active
    assert CANARY_EMAIL.encode() not in response.content

    # Detail: count only, never rows/UUIDs/names/purposes.
    response = client.get(f"/manage/blackouts/{blackout.id}/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "1 confirmed or released reservation overlaps" in content
    assert CANARY_EMAIL not in content
    assert CANARY_NAME not in content
    assert str(overlapping.id) not in content
    assert CANARY_PURPOSE not in content
    assert "/manage/reservations/" not in content
    client.logout()

    # With read-all the same detail renders the full affected list.
    reader = grant(
        User.objects.create_user(email="bmp-read-050@example.com", password="not-a-secret"),
        "view_maintenance_blackouts",
        "view_all_reservations",
    )
    client.force_login(reader)
    response = client.get(f"/manage/blackouts/{blackout.id}/")
    assert response.status_code == 200
    content = response.content.decode()
    assert str(overlapping.id) in content
    assert CANARY_NAME in content
    assert "/manage/reservations/" in content
    client.logout()


@pytest.mark.django_db
def test_all_reservations_filters_and_pagination(
    client: Client, asset: Asset, owner: User, other_owner: User
) -> None:
    reader = grant(
        User.objects.create_user(email="reader-050@example.com", password="not-a-secret"),
        "view_all_reservations",
    )
    other_asset = Asset.objects.create(
        slug="authority-gpu-2",
        name="Authority GPU 2",
        kind=Asset.KIND_GPU,
        parent=asset.parent,
        active=True,
        reservable=True,
        verification_required=False,
    )
    base = timezone.now() + timedelta(days=1)
    # 52 on the first asset, 51 on the other: both the unfiltered list
    # (103) and the asset-filtered list (52) span two pages.
    for index in range(103):
        make_reservation(
            owner if index % 2 else other_owner,
            asset if index < 52 else other_asset,
            base + timedelta(hours=index),
            base + timedelta(hours=index, minutes=30),
        )

    client.force_login(reader)
    response = client.get("/manage/reservations/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "All reservations" in content
    assert "Page 1 of 3" in content
    assert "page=2" in content
    # Exactly 50 data rows on the first page plus the header row.
    assert content.count("<tr>") == 51

    # Filtered pagination: the asset filter is preserved in the page link.
    response = client.get("/manage/reservations/", {"asset": str(asset.id)})
    assert response.status_code == 200
    content = response.content.decode()
    assert f"asset={asset.id}&amp;page=2" in content or f"asset={asset.id}&page=2" in content
    page2 = client.get("/manage/reservations/", {"asset": str(asset.id), "page": "2"})
    assert page2.status_code == 200
    assert "Page 2 of 2" in page2.content.decode()

    # Invalid filter: form error, empty result, no traceback.
    response = client.get(
        "/manage/reservations/",
        {"from": (base + timedelta(days=5)).isoformat(), "to": base.isoformat()},
    )
    assert response.status_code == 200
    assert "To must be after from" in response.content.decode()
    assert "Traceback" not in response.content.decode()

    # Owner identity stays visible in the authorized browser (existing
    # management representation).
    assert owner.email in client.get("/manage/reservations/").content.decode()


@pytest.mark.django_db
def test_audit_reader_export_split(
    client: Client,
    audit_event: AuditEvent,
) -> None:
    reader = grant(
        User.objects.create_user(email="aread-050@example.com", password="not-a-secret"),
        "view_audit_history",
    )
    client.force_login(reader)
    response = client.get("/manage/audit/")
    assert response.status_code == 200
    assert "/manage/audit/export.csv" not in response.content.decode()
    assert client.get("/manage/audit/export.csv").status_code == 403
    assert client.get(f"/manage/audit/{audit_event.id}/").status_code == 200
    client.logout()

    exporter = grant(
        User.objects.create_user(email="aexp-050@example.com", password="not-a-secret"),
        "export_audit_history",
    )
    client.force_login(exporter)
    assert client.get("/manage/audit/").status_code == 403
    assert client.get(f"/manage/audit/{audit_event.id}/").status_code == 403
    response = client.get("/manage/audit/export.csv")
    assert response.status_code == 200
    body = b"".join(response.streaming_content).decode()
    assert "maintenance_blackout.created" in body
    assert "Authorization" not in body
    # The existing filtered export semantics are unchanged.
    response = client.get(
        "/manage/audit/export.csv", {"action": AuditEvent.ACTION_BLACKOUT_CREATED}
    )
    assert response.status_code == 200
    client.logout()


@pytest.mark.django_db
def test_base_navigation_reflects_capabilities(
    client: Client,
    member_booker: User,
    staff_only: User,
    superuser: User,
) -> None:
    client.force_login(member_booker)
    content = client.get("/").content.decode()
    assert "My reservations" in content
    assert "Management" not in content
    assert "All reservations" not in content
    assert "Administration" not in content
    client.logout()

    client.force_login(staff_only)
    content = client.get("/").content.decode()
    assert "Administration" in content
    assert "Management" not in content
    assert "All reservations" not in content
    client.logout()

    reader = grant(
        User.objects.create_user(email="navread-050@example.com", password="not-a-secret"),
        "view_all_reservations",
    )
    client.force_login(reader)
    content = client.get("/").content.decode()
    assert "My reservations" in content
    assert "All reservations" in content
    assert "Management" in content
    assert "Administration" not in content
    client.logout()

    client.force_login(superuser)
    content = client.get("/").content.decode()
    assert "Management" in content
    assert "Administration" in content
    assert "All reservations" in content
    client.logout()


@pytest.mark.django_db
def test_admin_change_form_guidance_capability_aware(
    client: Client,
    policy: ReservationPolicy,
) -> None:
    """Read-only admin guidance: staff alone gets the capability note (no
    link); adding the app capability renders the management link."""
    from django.contrib.contenttypes.models import ContentType

    staff_viewer = User.objects.create_user(
        email="guidance-050@example.com",
        password="not-a-secret",
        is_staff=True,
    )
    staff_viewer.user_permissions.add(
        Permission.objects.get(
            codename="view_reservationpolicy",
            content_type=ContentType.objects.get_for_model(ReservationPolicy),
        )
    )
    url = f"/admin/reservations/reservationpolicy/{policy.id}/change/"
    client.force_login(staff_viewer)
    response = client.get(url)
    assert response.status_code == 200
    content = response.content.decode()
    assert "/manage/policies/" not in content
    assert "staff status alone is not enough" in content

    grant(staff_viewer, "view_booking_policies")
    client.force_login(staff_viewer)
    response = client.get(url)
    assert response.status_code == 200
    assert "/manage/policies/" in response.content.decode()
    client.logout()
