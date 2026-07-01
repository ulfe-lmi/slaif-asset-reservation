"""Shared operational checks used by health and management commands."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management import get_commands
from django.db import DEFAULT_DB_ALIAS, connection
from django.db.migrations.executor import MigrationExecutor

from slaif_reservation.assets.bootstrap import load_bootstrap_plan

REQUIRED_STATIC_ASSETS = (
    "admin/css/base.css",
    "web/site.css",
    "drf_spectacular_sidecar/swagger-ui-dist/swagger-ui-bundle.js",
)


def database_is_ready() -> bool:
    try:
        connection.ensure_connection()
        return not unapplied_migrations_exist()
    except Exception:
        return False


def unapplied_migrations_exist() -> bool:
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    return bool(executor.migration_plan(targets))


def missing_static_assets(assets: Iterable[str] = REQUIRED_STATIC_ASSETS) -> list[str]:
    return [asset for asset in assets if finders.find(asset) is None]


def critical_settings_errors() -> list[str]:
    errors: list[str] = []
    if not getattr(settings, "SECRET_KEY", ""):
        errors.append("SECRET_KEY is not configured")
    default_database = settings.DATABASES.get(DEFAULT_DB_ALIAS, {})
    if default_database.get("ENGINE") != "django.db.backends.postgresql":
        errors.append("default database is not PostgreSQL")
    if not getattr(settings, "API_TOKEN_PEPPER", ""):
        errors.append("API_TOKEN_PEPPER is not configured")
    if not getattr(settings, "ALLOWED_HOSTS", []):
        errors.append("ALLOWED_HOSTS is empty")
    return errors


def validate_bootstrap_assets() -> None:
    load_bootstrap_plan(Path(settings.BASE_DIR) / "data" / "bootstrap" / "assets.yaml")


def required_management_commands_present() -> bool:
    commands = get_commands()
    return "purge_expired_idempotency_records" in commands
