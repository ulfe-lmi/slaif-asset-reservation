from __future__ import annotations

import uuid

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
