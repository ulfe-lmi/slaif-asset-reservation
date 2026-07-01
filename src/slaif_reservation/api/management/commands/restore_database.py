from __future__ import annotations

from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from slaif_reservation.api.management.commands._postgres_tools import (
    database_url_from_env,
    ensure_tool,
    postgres_command_parts,
    run_postgres_tool,
)


class Command(BaseCommand):
    help = "Restore a PostgreSQL custom-format backup through pg_restore."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--input", required=True, help="Backup artifact path to restore.")
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Run pg_restore. Omit for validation-only dry-run.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        input_path = Path(options["input"])
        database_url = database_url_from_env()
        parts, env = postgres_command_parts(database_url)
        if not input_path.exists():
            raise CommandError("Input backup artifact does not exist.")

        self.stdout.write(f"mode={'apply' if options['apply'] else 'dry-run'}")
        self.stdout.write(f"input={input_path}")
        if not options["apply"]:
            self.stdout.write("validated=true")
            return

        pg_restore = ensure_tool("pg_restore")
        run_postgres_tool(
            [pg_restore, "--clean", "--if-exists", "--no-owner", *parts, str(input_path)],
            env=env,
        )
        self.stdout.write("restored=true")
