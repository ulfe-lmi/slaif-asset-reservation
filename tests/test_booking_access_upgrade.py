"""Order 049-a: deliberate upgrade of a populated pre-upgrade database.

Runs the real migration graph from the populated historical
``assets.0002`` state (everything else at the post-048 leaves) to the
current leaf migrations on the owned PostgreSQL test database (no
SQLite, no mocked migration executor) and proves:

- every pre-existing asset becomes ``booking_restricted=False`` with NO
  allowed groups, keeping its identity and every other field
  (machine/child hierarchy, legacy provenance, capabilities, flags,
  tags);
- every other product row (users, groups, reservations, policies,
  blackouts, audit events, API tokens) keeps its identity and content;
- a normal re-run of ``migrate`` changes nothing;
- assets created after the upgrade default to unrestricted.

Migration state is restored to the full leaf and seeded rows are
removed in the fixture's ``finally``.
"""

from __future__ import annotations

import uuid as uuid_module
from datetime import UTC, datetime, timedelta

import pytest
from django.apps.registry import Apps
from django.core.management import call_command
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.utils import timezone

from slaif_reservation.accounts.models import ApiToken, User
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.reservations.models import (
    MaintenanceBlackout,
    Reservation,
    ReservationPolicy,
)

EMAIL_PREFIX = "legacy-049-"
GROUP_NAME = "legacy-049-group"
ASSET_SLUG_PREFIX = "legacy-049-"
TAG_SLUG = "legacy-049-tag"


def _pre_upgrade_apps() -> Apps:
    """Historical app registry at the pre-upgrade migration state.

    Every app sits at its leaf except ``assets`` (0002), which is exactly
    the database shape before order 049-a's migration ran (048-a's
    accounts/reservations migrations are already merged).
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

    pinned_assets = _node("assets", "0002")
    nodes: list[tuple[str, str]] = []
    for app_label, leaf_name in loader.graph.leaf_nodes():
        if app_label == "assets":
            nodes.append(pinned_assets)
        else:
            nodes.append((app_label, leaf_name))
    return loader.project_state(nodes).apps


def _cleanup_legacy_rows() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM reservations_reservation WHERE asset_id IN "
            "(SELECT id FROM assets_asset WHERE slug LIKE %s)",
            [f"{ASSET_SLUG_PREFIX}%"],
        )
        cursor.execute(
            "DELETE FROM reservations_maintenanceblackout WHERE asset_id IN "
            "(SELECT id FROM assets_asset WHERE slug LIKE %s)",
            [f"{ASSET_SLUG_PREFIX}%"],
        )
        cursor.execute(
            "DELETE FROM reservations_reservationpolicy WHERE asset_id IN "
            "(SELECT id FROM assets_asset WHERE slug LIKE %s)",
            [f"{ASSET_SLUG_PREFIX}%"],
        )
        cursor.execute(
            "DELETE FROM assets_asset_tags WHERE asset_id IN "
            "(SELECT id FROM assets_asset WHERE slug LIKE %s)",
            [f"{ASSET_SLUG_PREFIX}%"],
        )
        cursor.execute(
            "DELETE FROM assets_asset WHERE slug LIKE %s",
            [f"{ASSET_SLUG_PREFIX}%"],
        )
        cursor.execute(
            "DELETE FROM assets_assettag WHERE slug = %s",
            [TAG_SLUG],
        )
        cursor.execute(
            "DELETE FROM accounts_apitoken WHERE owner_id IN "
            "(SELECT id FROM accounts_user WHERE email LIKE %s)",
            [f"{EMAIL_PREFIX}%"],
        )
        cursor.execute(
            "DELETE FROM accounts_user_groups WHERE user_id IN "
            "(SELECT id FROM accounts_user WHERE email LIKE %s)",
            [f"{EMAIL_PREFIX}%"],
        )
        cursor.execute(
            "DELETE FROM accounts_user_user_permissions WHERE user_id IN "
            "(SELECT id FROM accounts_user WHERE email LIKE %s)",
            [f"{EMAIL_PREFIX}%"],
        )
        cursor.execute(
            "DELETE FROM auth_group_permissions WHERE group_id IN "
            "(SELECT id FROM auth_group WHERE name = %s)",
            [GROUP_NAME],
        )
        cursor.execute(
            "DELETE FROM auth_group WHERE name = %s",
            [GROUP_NAME],
        )
        cursor.execute(
            "DELETE FROM audit_auditevent WHERE actor_user_id IN "
            "(SELECT id FROM accounts_user WHERE email LIKE %s)",
            [f"{EMAIL_PREFIX}%"],
        )
        cursor.execute(
            "DELETE FROM accounts_user WHERE email LIKE %s",
            [f"{EMAIL_PREFIX}%"],
        )


@pytest.fixture()
def upgraded_populated_db():
    """Unapply the 049 migration, yield historical apps, then restore."""
    call_command("migrate", "assets", "0002", interactive=False, verbosity=0)
    try:
        yield _pre_upgrade_apps()
    finally:
        call_command("migrate", interactive=False, verbosity=0)
        _cleanup_legacy_rows()


def _create_hist_user(hist_user, *, email: str, **extra: object):
    now = datetime.now(UTC)
    return hist_user.objects.create(
        email=email,
        display_name=email.split("@")[0],
        password="unusable-password-for-upgrade-test",
        date_joined=now,
        **extra,
    )


@pytest.mark.django_db(transaction=True)
def test_populated_upgrade_migrates_assets_unrestricted_and_preserves_rows(
    upgraded_populated_db,
) -> None:
    apps = upgraded_populated_db
    hist_user = apps.get_model("accounts", "User")
    hist_group = apps.get_model("auth", "Group")
    hist_permission = apps.get_model("auth", "Permission")
    hist_api_token = apps.get_model("accounts", "ApiToken")
    hist_asset = apps.get_model("assets", "Asset")
    hist_tag = apps.get_model("assets", "AssetTag")
    hist_reservation = apps.get_model("reservations", "Reservation")
    hist_policy = apps.get_model("reservations", "ReservationPolicy")
    hist_blackout = apps.get_model("reservations", "MaintenanceBlackout")
    hist_audit = apps.get_model("audit", "AuditEvent")

    # --- populate the pre-upgrade database ------------------------------
    now = datetime.now(UTC)
    member = _create_hist_user(hist_user, email=f"{EMAIL_PREFIX}member@example.com")
    staff = _create_hist_user(hist_user, email=f"{EMAIL_PREFIX}staff@example.com", is_staff=True)
    group = hist_group.objects.create(name=GROUP_NAME)
    book_perm = hist_permission.objects.get(
        codename="book_assets", content_type__app_label="reservations"
    )
    group.permissions.add(book_perm)
    member.groups.add(group)
    member.user_permissions.add(
        hist_permission.objects.get(
            codename="view_reservation", content_type__app_label="reservations"
        )
    )

    tag = hist_tag.objects.create(slug=TAG_SLUG, name="Legacy 049 Tag")

    machine = hist_asset.objects.create(
        slug=f"{ASSET_SLUG_PREFIX}machine",
        name="Legacy 049 Machine",
        kind=Asset.KIND_MACHINE,
        active=True,
        reservable=False,
        timezone="Europe/Ljubljana",
        capabilities={"vcpus": 64},
        physical_locator="room-1",
    )
    machine.tags.add(tag)
    gpu = hist_asset.objects.create(
        slug=f"{ASSET_SLUG_PREFIX}gpu",
        name="Legacy 049 GPU",
        kind=Asset.KIND_GPU,
        parent=machine,
        active=True,
        reservable=True,
        timezone="UTC",
        capabilities={"cuda": 9},
        legacy_source="smartscheduling-synthetic",
        legacy_id="legacy-049-gpu",
        legacy_metadata={"vendor": "synthetic"},
    )
    cpu_pool = hist_asset.objects.create(
        slug=f"{ASSET_SLUG_PREFIX}cpu",
        name="Legacy 049 CPU Pool",
        kind=Asset.KIND_CPU_POOL,
        active=True,
        reservable=True,
    )
    service = hist_asset.objects.create(
        slug=f"{ASSET_SLUG_PREFIX}service",
        name="Legacy 049 Service",
        kind=Asset.KIND_SERVICE,
        active=True,
        reservable=False,
    )
    other = hist_asset.objects.create(
        slug=f"{ASSET_SLUG_PREFIX}other",
        name="Legacy 049 Other",
        kind=Asset.KIND_OTHER,
        active=False,
        reservable=False,
    )

    policy = hist_policy.objects.create(
        name=f"{ASSET_SLUG_PREFIX}policy",
        asset=gpu,
        min_duration_minutes=15,
        max_duration_minutes=240,
        booking_horizon_days=30,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=10,
        max_concurrent_per_principal=5,
        purpose_required=False,
    )
    start = timezone.now() + timedelta(days=1)
    end = start + timedelta(hours=2)
    reservation = hist_reservation.objects.create(
        asset=gpu,
        requested_by_user=member,
        source=Reservation.SOURCE_WEB,
        status=Reservation.STATUS_CONFIRMED,
        start_at=start,
        end_at=end,
        effective_end_at=end,
        purpose="legacy purpose",
    )
    blackout = hist_blackout.objects.create(
        asset=cpu_pool,
        created_by=staff,
        active=True,
        start_at=start,
        end_at=end,
        reason="legacy maintenance",
    )
    hist_audit.objects.create(
        action=AuditEvent.ACTION_RESERVATION_CREATED,
        target_type="reservation",
        target_id=reservation.id,
        correlation_id=uuid_module.uuid4(),
        source=AuditEvent.SOURCE_WEB,
        actor_user=member,
        occurred_at=now,
        metadata={"asset_id": str(gpu.id)},
    )
    token = hist_api_token.objects.create(
        owner=member,
        name="legacy token",
        scopes=["reservations:read"],
        expires_at=timezone.now() + timedelta(days=1),
    )

    # Snapshot identities/content (in memory only; no secrets printed).
    snapshot = {
        "machine": {
            "id": machine.id,
            "slug": machine.slug,
            "name": machine.name,
            "kind": machine.kind,
            "parent_id": machine.parent_id,
            "active": machine.active,
            "reservable": machine.reservable,
            "capabilities": machine.capabilities,
            "physical_locator": machine.physical_locator,
            "tags": sorted(t.slug for t in machine.tags.all()),
        },
        "gpu": {
            "id": gpu.id,
            "slug": gpu.slug,
            "parent_id": gpu.parent_id,
            "active": gpu.active,
            "reservable": gpu.reservable,
            "timezone": gpu.timezone,
            "capabilities": gpu.capabilities,
            "legacy_source": gpu.legacy_source,
            "legacy_id": gpu.legacy_id,
            "legacy_metadata": gpu.legacy_metadata,
            "created_at": gpu.created_at,
            "updated_at": gpu.updated_at,
        },
        "cpu_pool_id": cpu_pool.id,
        "service_id": service.id,
        "other_id": other.id,
        "policy_id": policy.id,
        "reservation": {
            "id": reservation.id,
            "asset_id": reservation.asset_id,
            "requested_by_user_id": reservation.requested_by_user_id,
            "status": reservation.status,
            "start_at": reservation.start_at,
            "end_at": reservation.end_at,
            "effective_end_at": reservation.effective_end_at,
            "purpose": reservation.purpose,
        },
        "blackout_id": blackout.id,
        "audit_count": hist_audit.objects.count(),
        "token_id": token.id,
        "member_id": member.id,
        "group_id": group.id,
        "staff_id": staff.id,
    }

    # --- run the real upgrade --------------------------------------------
    call_command("migrate", interactive=False, verbosity=0)

    # Every existing asset migrates unrestricted with no allowed groups,
    # and every field keeps its pre-upgrade value.
    current_assets = {
        asset.slug: asset for asset in Asset.objects.filter(slug__startswith=ASSET_SLUG_PREFIX)
    }
    assert set(current_assets) == {
        f"{ASSET_SLUG_PREFIX}machine",
        f"{ASSET_SLUG_PREFIX}gpu",
        f"{ASSET_SLUG_PREFIX}cpu",
        f"{ASSET_SLUG_PREFIX}service",
        f"{ASSET_SLUG_PREFIX}other",
    }
    for asset in current_assets.values():
        assert asset.booking_restricted is False
        assert asset.allowed_booking_groups.count() == 0

    machine_now = current_assets[f"{ASSET_SLUG_PREFIX}machine"]
    gpu_now = current_assets[f"{ASSET_SLUG_PREFIX}gpu"]
    assert machine_now.id == snapshot["machine"]["id"]
    assert machine_now.name == snapshot["machine"]["name"]
    assert machine_now.kind == snapshot["machine"]["kind"]
    assert machine_now.capabilities == snapshot["machine"]["capabilities"]
    assert machine_now.physical_locator == snapshot["machine"]["physical_locator"]
    assert machine_now.tags.count() == 1 and machine_now.tags.first().slug == TAG_SLUG
    assert gpu_now.id == snapshot["gpu"]["id"]
    assert gpu_now.parent_id == snapshot["gpu"]["parent_id"]
    assert gpu_now.timezone == snapshot["gpu"]["timezone"]
    assert gpu_now.capabilities == snapshot["gpu"]["capabilities"]
    assert gpu_now.legacy_source == snapshot["gpu"]["legacy_source"]
    assert gpu_now.legacy_id == snapshot["gpu"]["legacy_id"]
    assert gpu_now.legacy_metadata == snapshot["gpu"]["legacy_metadata"]
    assert gpu_now.created_at == snapshot["gpu"]["created_at"]
    assert gpu_now.updated_at == snapshot["gpu"]["updated_at"]

    # All other product rows are preserved.
    reservation_now = Reservation.objects.get(id=snapshot["reservation"]["id"])
    assert reservation_now.asset_id == snapshot["reservation"]["asset_id"]
    assert reservation_now.requested_by_user_id == snapshot["reservation"]["requested_by_user_id"]
    assert reservation_now.status == snapshot["reservation"]["status"]
    assert reservation_now.start_at == snapshot["reservation"]["start_at"]
    assert reservation_now.end_at == snapshot["reservation"]["end_at"]
    assert reservation_now.effective_end_at == snapshot["reservation"]["effective_end_at"]
    assert reservation_now.purpose == snapshot["reservation"]["purpose"]
    assert ReservationPolicy.objects.get(id=snapshot["policy_id"]).asset_id == gpu_now.id
    assert (
        MaintenanceBlackout.objects.get(id=snapshot["blackout_id"]).asset_id
        == current_assets[f"{ASSET_SLUG_PREFIX}cpu"].id
    )
    assert AuditEvent.objects.count() == snapshot["audit_count"]
    assert ApiToken.objects.get(id=snapshot["token_id"]).owner_id == snapshot["member_id"]
    member_now = User.objects.get(id=snapshot["member_id"])
    assert member_now.groups.get().name == GROUP_NAME
    assert member_now.has_perm("reservations.book_assets")
    assert User.objects.get(id=snapshot["staff_id"]).is_staff

    # Idempotence: a normal re-run of migrate changes nothing.
    before = Asset.objects.order_by("id").values_list("id", "booking_restricted", "updated_at")
    call_command("migrate", interactive=False, verbosity=0)
    after = Asset.objects.order_by("id").values_list("id", "booking_restricted", "updated_at")
    assert list(before) == list(after)

    # New assets default to unrestricted.
    fresh = Asset.objects.create(
        slug=f"{ASSET_SLUG_PREFIX}fresh",
        name="Legacy 049 Fresh",
        kind=Asset.KIND_OTHER,
        active=True,
        reservable=False,
    )
    assert fresh.booking_restricted is False
    assert fresh.allowed_booking_groups.count() == 0
