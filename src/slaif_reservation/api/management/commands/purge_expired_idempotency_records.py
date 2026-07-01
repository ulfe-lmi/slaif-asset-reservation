from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import DatabaseError, transaction
from django.utils import timezone

from slaif_reservation.api.models import IdempotencyRecord


class Command(BaseCommand):
    help = "Dry-run or purge expired API idempotency records."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Delete expired records. Omit for dry-run only.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Maximum expired records to delete per transaction in apply mode.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        apply_mode = bool(options["apply"])
        batch_size = int(options["batch_size"])
        if batch_size < 1:
            raise CommandError("batch_size must be at least 1")

        now = timezone.now()
        expired = IdempotencyRecord.objects.filter(expires_at__lte=now)
        try:
            expired_count = expired.count()
        except DatabaseError as exc:
            raise CommandError(
                "Idempotency records are unavailable; run migrations first."
            ) from exc
        deleted_count = 0

        if apply_mode:
            while True:
                ids = list(
                    IdempotencyRecord.objects.filter(expires_at__lte=now)
                    .order_by("expires_at", "id")
                    .values_list("id", flat=True)[:batch_size]
                )
                if not ids:
                    break
                with transaction.atomic():
                    deleted, _ = IdempotencyRecord.objects.filter(id__in=ids).delete()
                    deleted_count += deleted

        self.stdout.write(f"mode={'apply' if apply_mode else 'dry-run'}")
        self.stdout.write(f"expired={expired_count}")
        self.stdout.write(f"deleted={deleted_count}")
        self.stdout.write(
            f"remaining_expired={IdempotencyRecord.objects.filter(expires_at__lte=now).count()}"
        )
