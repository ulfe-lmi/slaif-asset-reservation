from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from slaif_reservation.legacy_import.importer import build_safe_report
from slaif_reservation.legacy_import.management.commands._common import (
    add_common_import_arguments,
    load_plan,
    print_counts,
    write_report,
)


class Command(BaseCommand):
    help = "Plan a synthetic SmartScheduling import. This command never writes reservations."

    def add_arguments(self, parser: CommandParser) -> None:
        add_common_import_arguments(parser)

    def handle(self, *args: Any, **options: Any) -> None:
        plan = load_plan(options)
        self.stdout.write("mode=dry-run")
        self.stdout.write(f"legacy_source={plan.export.legacy_source}")
        print_counts(self, plan.counts)
        write_report(options.get("report_json"), build_safe_report(plan))
