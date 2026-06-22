from __future__ import annotations

import psycopg
import pytest
from django.conf import settings

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
