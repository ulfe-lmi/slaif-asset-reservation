"""Bounded removal of expired security counters; read-only by default."""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from slaif_reservation.config.abuse import purge_expired


class Command(BaseCommand):
    help = "Inspect expired abuse counters; --apply removes at most --batch-size rows."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--batch-size", type=int, default=1000)

    def handle(self, *args: Any, **options: Any) -> None:
        batch = options["batch_size"]
        if not 1 <= batch <= 10000:
            raise CommandError("Batch size must be between 1 and 10000.")
        try:
            count = purge_expired(apply=options["apply"], batch=batch)
        except DatabaseError:
            raise CommandError("Security-counter cleanup is temporarily unavailable.") from None
        verb = "removed" if options["apply"] else "expired (dry-run)"
        self.stdout.write(f"Security counters: {count} {verb}.")
