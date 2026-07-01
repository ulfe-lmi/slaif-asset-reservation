from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from slaif_reservation.legacy_import.exceptions import LegacyImportError
from slaif_reservation.legacy_import.importer import apply_import, build_safe_report
from slaif_reservation.legacy_import.management.commands._common import (
    add_common_import_arguments,
    load_plan,
    print_counts,
    write_report,
)


class Command(BaseCommand):
    help = "Dry-run or apply a synthetic SmartScheduling import plan."

    def add_arguments(self, parser: CommandParser) -> None:
        add_common_import_arguments(parser)
        parser.add_argument("--apply", action="store_true", help="Create eligible reservations.")

    def handle(self, *args: Any, **options: Any) -> None:
        plan = load_plan(options)
        if not options["apply"]:
            self.stdout.write("mode=dry-run")
            self.stdout.write(f"legacy_source={plan.export.legacy_source}")
            print_counts(self, plan.counts)
            write_report(options.get("report_json"), build_safe_report(plan))
            return

        try:
            result = apply_import(plan)
        except LegacyImportError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write("mode=apply")
        self.stdout.write(f"legacy_source={plan.export.legacy_source}")
        self.stdout.write(f"batch_id={result.batch.id}")
        print_counts(self, result.counts)
        write_report(options.get("report_json"), build_safe_report(result.plan))
