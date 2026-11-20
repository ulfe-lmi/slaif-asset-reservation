from __future__ import annotations

import uuid
from datetime import timedelta

import psycopg
import pytest
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.db import connection
from django.utils import timezone

from slaif_reservation.accounts.models import User
from slaif_reservation.config.env import postgres_database_from_url


@pytest.mark.django_db(transaction=True)
def test_migrations_are_applied_to_postgresql_database() -> None:
    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"

    with psycopg.connect(
        dbname=settings.DATABASES["default"]["NAME"],
        user=settings.DATABASES["default"].get("USER"),
        password=settings.DATABASES["default"].get("PASSWORD"),
        host=settings.DATABASES["default"].get("HOST"),
        port=settings.DATABASES["default"].get("PORT"),
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute("select 1")
            assert cursor.fetchone() == (1,)


def test_database_url_parser_returns_postgresql_backend() -> None:
    config = postgres_database_from_url("postgres://user:pass@localhost:5432/example")

    assert config["ENGINE"] == "django.db.backends.postgresql"
    assert config["NAME"] == "example"
    assert config["USER"] == "user"


@pytest.mark.django_db(transaction=True)
def test_onboarding_state_migration_leaves_existing_accounts_untouched() -> None:
    """Real PostgreSQL upgrade path 0005 -> 0006 (SAR-055).

    An account created while the database was still at 0005 must come
    through the upgrade with the new nullable column NULL, still active,
    and still able to sign in with its stored hash. The pre-upgrade row
    is written with raw SQL because the ORM model already references the
    column that 0006 adds.
    """
    call_command("migrate", "accounts", "0005")
    try:
        email = "preupgrade@example.com"
        plaintext = "PreUpgrade123!"
        now = timezone.now()
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO accounts_user ("
                "id, password, last_login, is_superuser, email, display_name,"
                " timezone, is_active, is_staff, is_service_account,"
                " external_identifier, date_joined, created_at, updated_at"
                ") VALUES (%s, %s, NULL, %s, %s, %s, %s, %s, %s, %s, NULL,"
                " %s, %s, %s)",
                (
                    uuid.uuid4(),
                    make_password(plaintext),
                    False,
                    email,
                    "Pre Upgrade",
                    "Europe/Ljubljana",
                    True,
                    False,
                    False,
                    now,
                    now,
                    now,
                ),
            )
        call_command("migrate", "accounts", "0006")
        user = User.objects.get(email=email)
        assert user.onboarding_password_expires_at is None
        assert user.is_active is True
        assert user.check_password(plaintext)
        # The new authentication backend does not disturb pre-existing
        # accounts: the stored hash still signs in.
        assert authenticate(request=None, username=email, password=plaintext) is not None
    finally:
        # This test commits migration state (transaction=True); restore
        # the full migration set for the rest of the session.
        call_command("migrate", "accounts")


@pytest.mark.django_db(transaction=True)
def test_booking_denylist_migration_preserves_existing_rows() -> None:
    """Real PostgreSQL upgrade path assets 0003 -> 0004 (SAR-057).

    A populated pre-upgrade database (asset with its allow-list, an
    accepted reservation) must come through the migration with every
    existing row preserved byte-for-byte and the NEW
    ``excluded_booking_groups`` M2M empty — no data backfill, no
    allow-list rewrite, no reservation or audit mutation. The pre-upgrade
    rows are written with raw SQL because the ORM model already
    references the table that 0004 adds.
    """
    call_command("migrate", "assets", "0003")
    try:
        user_id = uuid.uuid4()
        asset_id = uuid.uuid4()
        reservation_id = uuid.uuid4()
        now = timezone.now()
        start = now - timedelta(hours=1)
        end = now + timedelta(hours=1)
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO accounts_user ("
                "id, password, last_login, is_superuser, email, display_name,"
                " timezone, is_active, is_staff, is_service_account,"
                " external_identifier, date_joined, created_at, updated_at"
                ") VALUES (%s, %s, NULL, %s, %s, %s, %s, %s, %s, %s, NULL,"
                " %s, %s, %s)",
                (
                    user_id,
                    make_password("PreUpgrade123!"),
                    False,
                    "denylist-upgrade@example.com",
                    "Denylist Upgrade",
                    "Europe/Ljubljana",
                    True,
                    False,
                    False,
                    now,
                    now,
                    now,
                ),
            )
            cursor.execute(
                "INSERT INTO auth_group (name) VALUES (%s) RETURNING id",
                ("denylist-allowed-group",),
            )
            group_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO assets_asset ("
                "id, parent_id, slug, name, kind, booking_mode, description,"
                " location, timezone, active, reservable, booking_restricted,"
                " capabilities, verification_required, physical_locator,"
                " legacy_source, legacy_id, legacy_metadata, created_at, updated_at"
                ") VALUES (%s, NULL, %s, %s, %s, %s, '', '', %s, %s, %s, %s,"
                " %s, %s, '', NULL, NULL, %s, %s, %s)",
                (
                    asset_id,
                    "denylist-upgrade-asset",
                    "Denylist Upgrade Asset",
                    "gpu",
                    "exclusive",
                    "Europe/Ljubljana",
                    True,
                    True,
                    True,
                    "{}",
                    True,
                    "{}",
                    now,
                    now,
                ),
            )
            cursor.execute(
                "INSERT INTO assets_asset_allowed_booking_groups (asset_id, group_id)"
                " VALUES (%s, %s)",
                (asset_id, group_id),
            )
            cursor.execute(
                "INSERT INTO reservations_reservation ("
                "id, asset_id, requested_by_user_id, source, status, start_at,"
                " end_at, effective_end_at, purpose, released_at, cancelled_at,"
                " cancelled_by_id, cancellation_reason, created_at, updated_at"
                ") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, NULL, NULL,"
                " '', %s, %s)",
                (
                    reservation_id,
                    asset_id,
                    user_id,
                    "web",
                    "confirmed",
                    start,
                    end,
                    end,
                    "accepted before the denylist upgrade",
                    now,
                    now,
                ),
            )
        call_command("migrate", "assets", "0004")

        # ORM-visible state after the upgrade: the new M2M is empty and
        # every pre-upgrade row is intact (allow-list, asset flags, the
        # accepted reservation).
        from slaif_reservation.assets.models import Asset
        from slaif_reservation.reservations.models import Reservation

        asset = Asset.objects.get(id=asset_id)
        assert list(asset.excluded_booking_groups.values_list("id", flat=True)) == []
        assert list(asset.allowed_booking_groups.values_list("id", flat=True)) == [group_id]
        assert asset.booking_restricted is True
        assert asset.slug == "denylist-upgrade-asset"
        reservation = Reservation.objects.get(id=reservation_id)
        assert reservation.status == Reservation.STATUS_CONFIRMED
        assert reservation.purpose == "accepted before the denylist upgrade"
        # And the denylist is already effective at the new schema: a dual
        # member (allowed + excluded group) is denied on this exact asset,
        # while the plain allowed-only member stays eligible.
        from django.contrib.auth.models import Group, Permission

        from slaif_reservation.accounts.models import User
        from slaif_reservation.assets.authorization import user_can_book_asset

        excluded_group = Group.objects.create(name="denylist-excluded-group")
        dual_member = User.objects.create_user(
            email="denylist-dual@example.com", password="PreUpgrade123!"
        )
        dual_member.user_permissions.add(
            Permission.objects.get(codename="book_assets", content_type__app_label="reservations")
        )
        plain_member = User.objects.create_user(
            email="denylist-plain@example.com", password="PreUpgrade123!"
        )
        plain_member.user_permissions.add(
            Permission.objects.get(codename="book_assets", content_type__app_label="reservations")
        )
        for member in (dual_member, plain_member):
            member.groups.add(Group.objects.get(id=group_id))
        assert user_can_book_asset(dual_member, asset) is True
        assert user_can_book_asset(plain_member, asset) is True

        asset.excluded_booking_groups.add(excluded_group)
        dual_member.groups.add(excluded_group)
        assert user_can_book_asset(dual_member, asset) is False
        assert user_can_book_asset(plain_member, asset) is True
    finally:
        # This test commits migration state (transaction=True); restore
        # the full migration set for the rest of the session.
        call_command("migrate", "assets")
