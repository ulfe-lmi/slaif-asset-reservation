"""Order 048-a: deliberate upgrade of a populated pre-upgrade database.

Runs the real migration graph from the populated historical
``accounts.0004`` / ``reservations.0002`` state to the current leaf
migrations on the owned PostgreSQL test database (no SQLite, no mocked
migration executor) and proves:

- every pre-existing user/group/reservation/policy/blackout/audit/token
  row keeps its identity and content (snapshotted in memory only; no
  secret-bearing values are printed);
- the one-time data migration adds ONLY ``reservations.book_assets`` and
  ONLY to existing non-service-account users (including inactive rows);
- pre-existing direct and group grants are untouched;
- every user's new ``external_identifier`` is NULL (no inference/backfill);
- a normal re-run of ``migrate`` duplicates nothing;
- accounts created after the upgrade receive no automatic grants.

Migration state is restored to the full leaf and seeded rows are removed
in the fixture's ``finally``.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid as uuid_module
from datetime import UTC, datetime, timedelta

import pytest
from django.apps.registry import Apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.db import connection
from django.db.migrations.loader import MigrationLoader

from slaif_reservation.accounts.authorization import (
    BOOKING_BASELINE_PERMISSION,
    MANAGEMENT_PERMISSIONS,
    RESERVATIONS_PERMISSIONS,
)
from slaif_reservation.accounts.models import ApiToken, User
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.reservations.models import (
    MaintenanceBlackout,
    Reservation,
    ReservationPolicy,
)

EMAIL_PREFIX = "legacy-048-"
GROUP_NAME = "legacy-048-group"
POLICY_NAME = "legacy-048-policy"
ASSET_SLUG_PREFIX = "legacy-048-"


def _pre_upgrade_apps() -> Apps:
    """Historical app registry at the pre-upgrade migration state.

    Every app sits at its leaf except ``accounts`` (0004) and
    ``reservations`` (0002), which is exactly the database shape before
    order 048-a's migrations ran.
    """
    loader = MigrationLoader(connection)
    graph_nodes = set(loader.graph.nodes)

    def _node(app_label: str, name_prefix: str) -> tuple[str, str]:
        matches = [
            name
            for app, name in graph_nodes
            if app == app_label and name.startswith(f"{name_prefix}_")
        ]
        assert len(matches) == 1, f"ambiguous or missing {app_label} {name_prefix} migration"
        return (app_label, matches[0])

    pinned_accounts = _node("accounts", "0004")
    pinned_reservations = _node("reservations", "0002")
    nodes: list[tuple[str, str]] = []
    for app_label, leaf_name in loader.graph.leaf_nodes():
        if app_label == "accounts":
            nodes.append(pinned_accounts)
        elif app_label == "reservations":
            nodes.append(pinned_reservations)
        else:
            nodes.append((app_label, leaf_name))
    return loader.project_state(nodes).apps


def _book_assets_permission_id() -> int:
    ct = _reservation_content_type()
    return Permission.objects.get(content_type=ct, codename=BOOKING_BASELINE_PERMISSION).id


def _reservation_content_type() -> ContentType:
    return ContentType.objects.get_for_model(Reservation)


def _custom_grants(user: User) -> set[str]:
    ct = _reservation_content_type()
    return {
        permission.codename
        for permission in user.user_permissions.filter(
            content_type=ct, codename__in=list(RESERVATIONS_PERMISSIONS)
        )
    }


def _create_hist_user(hist_user: object, *, now, **fields: object) -> object:
    """Create a user on the pre-upgrade historical model.

    Migration-state models carry the custom manager but not the concrete
    model class methods (``set_password`` lives on an abstract base that
    the migration state does not render), so the password hash is set
    directly.
    """
    from django.contrib.auth.hashers import make_password

    kwargs: dict = {
        "timezone": "Europe/Ljubljana",
        "is_active": True,
        "is_staff": False,
        "is_service_account": False,
        "display_name": "",
        "date_joined": now,
    }
    kwargs.update(fields)
    user = hist_user(password=make_password("not-a-secret"), **kwargs)
    user.save()
    return user


def _cleanup_legacy_rows() -> None:
    """Deterministically remove every row seeded by this test (owned rows)."""
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM audit_auditevent WHERE actor_user_id IN "
            "(SELECT id FROM accounts_user WHERE email LIKE %s)",
            [f"{EMAIL_PREFIX}%"],
        )
        cursor.execute(
            "DELETE FROM reservations_reservation WHERE requested_by_user_id IN "
            "(SELECT id FROM accounts_user WHERE email LIKE %s)",
            [f"{EMAIL_PREFIX}%"],
        )
        cursor.execute(
            "DELETE FROM accounts_apitoken WHERE owner_id IN "
            "(SELECT id FROM accounts_user WHERE email LIKE %s)",
            [f"{EMAIL_PREFIX}%"],
        )
        cursor.execute(
            "DELETE FROM reservations_maintenanceblackout WHERE created_by_id IN "
            "(SELECT id FROM accounts_user WHERE email LIKE %s)",
            [f"{EMAIL_PREFIX}%"],
        )
        cursor.execute(
            "DELETE FROM accounts_user_user_permissions WHERE user_id IN "
            "(SELECT id FROM accounts_user WHERE email LIKE %s)",
            [f"{EMAIL_PREFIX}%"],
        )
        cursor.execute(
            "DELETE FROM accounts_user_groups WHERE user_id IN "
            "(SELECT id FROM accounts_user WHERE email LIKE %s)",
            [f"{EMAIL_PREFIX}%"],
        )
        cursor.execute(
            "DELETE FROM auth_group_permissions WHERE group_id IN "
            "(SELECT id FROM auth_group WHERE name = %s)",
            [GROUP_NAME],
        )
        cursor.execute("DELETE FROM auth_group WHERE name = %s", [GROUP_NAME])
        cursor.execute(
            "DELETE FROM reservations_reservationpolicy WHERE name = %s",
            [POLICY_NAME],
        )
        cursor.execute(
            "DELETE FROM assets_asset WHERE slug = %s",
            [f"{ASSET_SLUG_PREFIX}gpu"],
        )
        cursor.execute(
            "DELETE FROM assets_asset WHERE slug LIKE %s",
            [f"{ASSET_SLUG_PREFIX}%"],
        )
        cursor.execute(
            "DELETE FROM accounts_user WHERE email LIKE %s",
            [f"{EMAIL_PREFIX}%"],
        )


@pytest.fixture()
def upgraded_populated_db():
    """Unapply the 048 migrations, yield historical apps, then restore.

    The custom permission rows are removed first so the database is a
    faithful pre-upgrade shape (those rows are created by post_migrate
    after a full migrate, which had not happened for this target yet).
    """
    call_command("migrate", "accounts", "0004", interactive=False, verbosity=0)
    call_command("migrate", "reservations", "0002", interactive=False, verbosity=0)
    ct = _reservation_content_type()
    Permission.objects.filter(content_type=ct, codename__in=list(RESERVATIONS_PERMISSIONS)).delete()
    try:
        yield _pre_upgrade_apps()
    finally:
        call_command("migrate", interactive=False, verbosity=0)
        _cleanup_legacy_rows()


@pytest.mark.django_db(transaction=True)
def test_populated_upgrade_preserves_rows_and_grants_baseline_only(
    upgraded_populated_db,
) -> None:
    apps = upgraded_populated_db
    hist_user = apps.get_model("accounts", "User")
    hist_group = apps.get_model("auth", "Group")
    hist_permission = apps.get_model("auth", "Permission")
    hist_api_token = apps.get_model("accounts", "ApiToken")
    hist_reservation = apps.get_model("reservations", "Reservation")
    hist_policy = apps.get_model("reservations", "ReservationPolicy")
    hist_blackout = apps.get_model("reservations", "MaintenanceBlackout")
    hist_audit = apps.get_model("audit", "AuditEvent")
    hist_asset = apps.get_model("assets", "Asset")

    # --- populate the pre-upgrade database ------------------------------
    now = datetime.now(UTC)
    legacy_member = _create_hist_user(
        hist_user,
        now=now,
        email=f"{EMAIL_PREFIX}member@example.com",
        display_name="Legacy Member",
    )
    legacy_inactive = _create_hist_user(
        hist_user,
        now=now,
        email=f"{EMAIL_PREFIX}inactive@example.com",
        is_active=False,
    )
    legacy_service = _create_hist_user(
        hist_user,
        now=now,
        email=f"{EMAIL_PREFIX}service@example.com",
        is_service_account=True,
    )
    legacy_staff = _create_hist_user(
        hist_user,
        now=now,
        email=f"{EMAIL_PREFIX}staff@example.com",
        is_staff=True,
    )
    legacy_direct = _create_hist_user(
        hist_user,
        now=now,
        email=f"{EMAIL_PREFIX}direct@example.com",
    )

    old_view_perm = hist_permission.objects.get(
        codename="view_reservation", content_type__app_label="reservations"
    )
    old_add_perm = hist_permission.objects.get(
        codename="add_reservation", content_type__app_label="reservations"
    )
    legacy_group = hist_group.objects.create(name=GROUP_NAME)
    legacy_group.permissions.add(old_view_perm)
    legacy_member.groups.add(legacy_group)
    legacy_direct.user_permissions.add(old_add_perm)

    machine = hist_asset.objects.create(
        slug=f"{ASSET_SLUG_PREFIX}machine",
        name="Legacy 048 Machine",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
    )
    asset = hist_asset.objects.create(
        slug=f"{ASSET_SLUG_PREFIX}gpu",
        name="Legacy 048 GPU",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
    )
    policy = hist_policy.objects.create(
        name=POLICY_NAME,
        asset=None,
        active=True,
        min_duration_minutes=1,
        max_duration_minutes=2880,
        booking_horizon_days=7,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=50,
        max_concurrent_per_principal=8,
        purpose_required=False,
    )
    blackout = hist_blackout.objects.create(
        asset=asset,
        created_by=legacy_staff,
        reason="legacy synthetic blackout",
        start_at=now + timedelta(days=30),
        end_at=now + timedelta(days=31),
        active=False,
        deactivated_at=now,
        deactivated_by=legacy_staff,
    )
    start_at = now + timedelta(days=40)
    end_at = start_at + timedelta(hours=2)
    reservation = hist_reservation.objects.create(
        asset=asset,
        requested_by_user=legacy_member,
        source="migration",
        status="confirmed",
        start_at=start_at,
        end_at=end_at,
        effective_end_at=end_at,
    )
    token_verifier = secrets.token_hex(32)  # synthetic; never printed
    token = hist_api_token.objects.create(
        owner=legacy_member,
        name=f"{EMAIL_PREFIX}token",
        verifier=token_verifier,
        scopes=["reservations:read"],
        expires_at=now + timedelta(days=7),
    )
    # Safe preservation handle for the raw verifier: a one-way digest, so
    # no assertion message can ever print the secret itself.
    token_verifier_digest = hashlib.sha256(token_verifier.encode("utf-8")).hexdigest()
    audit = hist_audit.objects.create(
        occurred_at=now,
        actor_user=legacy_member,
        action=AuditEvent.ACTION_RESERVATION_CREATED,
        target_type="reservation",
        target_id=reservation.id,
        correlation_id=uuid_module.uuid4(),
        source=AuditEvent.SOURCE_MIGRATION,
        metadata={},
    )

    # --- snapshot (in memory only) ---------------------------------------
    snapshot_users = {
        u.pk: (u.email, u.is_active, u.is_staff, u.is_service_account)
        for u in (legacy_member, legacy_inactive, legacy_service, legacy_staff, legacy_direct)
    }
    snapshot = {
        "users": snapshot_users,
        "group_perms": set(legacy_group.permissions.values_list("id", flat=True)),
        "group_members": set(legacy_group.user_set.values_list("id", flat=True)),
        "direct_grants": set(legacy_direct.user_permissions.values_list("id", flat=True)),
        "token": (
            token.pk,
            token.name,
            list(token.scopes),
            token_verifier_digest,
            token.expires_at,
        ),
        "reservation": (
            reservation.pk,
            reservation.status,
            reservation.start_at,
            reservation.end_at,
            reservation.effective_end_at,
            reservation.requested_by_user_id,
        ),
        "policy": (policy.pk, policy.name, policy.active, policy.min_duration_minutes),
        "blackout": (blackout.pk, blackout.active, blackout.reason),
        "audit": (audit.pk, audit.action, audit.target_id, audit.correlation_id),
    }

    # --- run the upgrade ---------------------------------------------------
    call_command("migrate", interactive=False, verbosity=0)

    # --- preservation -------------------------------------------------------
    for pk, (email, is_active, is_staff, is_service_account) in snapshot["users"].items():
        user = User.objects.get(pk=pk)
        assert (user.email, user.is_active, user.is_staff, user.is_service_account) == (
            email,
            is_active,
            is_staff,
            is_service_account,
        )
        # No inference or backfill: the new field is unset for every
        # pre-existing account.
        assert user.external_identifier is None
    assert User.objects.filter(external_identifier__isnull=False).count() == 0

    group = Group.objects.get(name=GROUP_NAME)
    assert set(group.permissions.values_list("id", flat=True)) == snapshot["group_perms"]
    assert set(group.user_set.values_list("id", flat=True)) == snapshot["group_members"]
    assert set(
        User.objects.get(pk=legacy_direct.pk).user_permissions.values_list("id", flat=True)
    ) == (snapshot["direct_grants"] | {_book_assets_permission_id()})

    tok = ApiToken.objects.get(pk=snapshot["token"][0])
    assert (
        tok.name,
        list(tok.scopes),
        hashlib.sha256(tok.verifier.encode("utf-8")).hexdigest(),
        tok.expires_at,
    ) == snapshot["token"][1:]

    res = Reservation.objects.get(pk=snapshot["reservation"][0])
    assert (
        res.status,
        res.start_at,
        res.end_at,
        res.effective_end_at,
        res.requested_by_user_id,
    ) == snapshot["reservation"][1:]

    pol = ReservationPolicy.objects.get(pk=snapshot["policy"][0])
    assert (pol.name, pol.active, pol.min_duration_minutes) == snapshot["policy"][1:]
    bo = MaintenanceBlackout.objects.get(pk=snapshot["blackout"][0])
    assert (bo.active, bo.reason) == snapshot["blackout"][1:]
    ev = AuditEvent.objects.get(pk=snapshot["audit"][0])
    assert (ev.action, ev.target_id, ev.correlation_id) == snapshot["audit"][1:]

    # --- baseline grant scope -------------------------------------------------
    assert _custom_grants(User.objects.get(pk=legacy_member.pk)) == {BOOKING_BASELINE_PERMISSION}
    # Inactive rows are included so a later normal reactivation keeps the
    # former booking baseline.
    assert _custom_grants(User.objects.get(pk=legacy_inactive.pk)) == {BOOKING_BASELINE_PERMISSION}
    assert _custom_grants(User.objects.get(pk=legacy_staff.pk)) == {BOOKING_BASELINE_PERMISSION}
    assert _custom_grants(User.objects.get(pk=legacy_direct.pk)) == {BOOKING_BASELINE_PERMISSION}
    # Service accounts are excluded from the baseline grant entirely.
    assert _custom_grants(User.objects.get(pk=legacy_service.pk)) == set()
    # No management/read-all capability was granted to anyone by the upgrade.
    ct = _reservation_content_type()
    assert (
        Permission.objects.filter(
            content_type=ct, codename__in=list(MANAGEMENT_PERMISSIONS), user__isnull=False
        ).count()
        == 0
    )
    # All ten permission records exist exactly once.
    assert Permission.objects.filter(
        content_type=ct, codename__in=list(RESERVATIONS_PERMISSIONS)
    ).count() == len(RESERVATIONS_PERMISSIONS)

    # --- subsequently created accounts exist BEFORE the re-run ---------------
    later_member = User.objects.create_user(
        email=f"{EMAIL_PREFIX}later@example.com", password="not-a-secret"
    )
    later_staff = User.objects.create_user(
        email=f"{EMAIL_PREFIX}later-staff@example.com", password="not-a-secret", is_staff=True
    )

    # --- idempotence: a normal re-run of migrate changes nothing -------------
    grants_before = {u.pk: _custom_grants(u) for u in User.objects.all()}
    member_grant_rows_before = (
        User.objects.get(pk=legacy_member.pk).user_permissions.filter(content_type=ct).count()
    )
    call_command("migrate", interactive=False, verbosity=0)
    grants_after = {u.pk: _custom_grants(u) for u in User.objects.all()}
    assert grants_before == grants_after
    assert (
        User.objects.get(pk=legacy_member.pk).user_permissions.filter(content_type=ct).count()
        == member_grant_rows_before
    )

    # --- no automatic grants for subsequently created accounts ---------------
    # The new accounts already exist when the re-run happens: it must not
    # grant them anything, and the original baseline/legacy rows are
    # unchanged (covered by the grants_before/grants_after equality above).
    assert later_member.user_permissions.count() == 0
    assert later_member.groups.count() == 0
    assert later_staff.user_permissions.count() == 0
    assert later_staff.groups.count() == 0
    assert _custom_grants(User.objects.get(pk=legacy_member.pk)) == {BOOKING_BASELINE_PERMISSION}
    assert _custom_grants(User.objects.get(pk=legacy_staff.pk)) == {BOOKING_BASELINE_PERMISSION}
    assert _custom_grants(User.objects.get(pk=legacy_service.pk)) == set()
