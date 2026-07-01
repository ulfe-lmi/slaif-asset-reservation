from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from slaif_reservation.config.operational import (
    critical_settings_errors,
    missing_static_assets,
    required_management_commands_present,
    unapplied_migrations_exist,
    validate_bootstrap_assets,
)


class Command(BaseCommand):
    help = "Run production-shaped deployment smoke checks without mutating application data."

    def handle(self, *args: Any, **options: Any) -> None:
        failures: list[str] = []

        try:
            connection.ensure_connection()
        except Exception:
            failures.append("database connectivity failed")
        else:
            self.stdout.write("database=ok")

        try:
            if unapplied_migrations_exist():
                failures.append("unapplied migrations exist")
            else:
                self.stdout.write("migrations=ok")
        except Exception:
            failures.append("migration state check failed")

        missing_assets = missing_static_assets()
        if missing_assets:
            failures.append("static assets missing")
        else:
            self.stdout.write("static=ok")

        failures.extend(critical_settings_errors())

        try:
            validate_bootstrap_assets()
        except Exception:
            failures.append("bootstrap inventory validation failed")
        else:
            self.stdout.write("bootstrap=ok")

        if required_management_commands_present():
            self.stdout.write("idempotency_cleanup_command=ok")
        else:
            failures.append("idempotency cleanup command missing")

        if failures:
            for failure in failures:
                self.stderr.write(failure)
            raise CommandError("operational check failed")

        self.stdout.write("operational_check=ok")
