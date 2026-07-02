from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from slaif_reservation.legacy_import.management.commands._common import (
    add_common_import_arguments,
    load_export,
    write_report,
)


class Command(BaseCommand):
    help = "Inspect a synthetic SmartScheduling export without mutating the database."

    def add_arguments(self, parser: CommandParser) -> None:
        add_common_import_arguments(parser)

    def handle(self, *args: Any, **options: Any) -> None:
        export = load_export(options)
        summary = {
            "legacy_source": export.legacy_source,
            "source_checksum": export.source_checksum,
            "synthetic": export.synthetic,
            "resource_count": len(export.resources),
            "person_count": len(export.people),
            "appointment_count": len(export.appointments),
        }
        self.stdout.write("mode=inspect")
        self.stdout.write(f"legacy_source={summary['legacy_source']}")
        self.stdout.write(f"synthetic={str(summary['synthetic']).lower()}")
        self.stdout.write(f"resources={summary['resource_count']}")
        self.stdout.write(f"people={summary['person_count']}")
        self.stdout.write(f"appointments={summary['appointment_count']}")
        write_report(options.get("report_json"), summary)
