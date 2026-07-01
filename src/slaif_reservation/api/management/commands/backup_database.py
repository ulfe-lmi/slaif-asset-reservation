from __future__ import annotations

from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from slaif_reservation.api.management.commands._postgres_tools import (
    database_url_from_env,
    ensure_tool,
    postgres_command_parts,
    require_parent_directory,
    run_postgres_tool,
)


class Command(BaseCommand):
    help = "Create a PostgreSQL custom-format backup through pg_dump."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--output", required=True, help="Backup artifact path to create.")
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Run pg_dump. Omit for validation-only dry-run.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        output_path = Path(options["output"])
        database_url = database_url_from_env()
        parts, env = postgres_command_parts(database_url)
        require_parent_directory(output_path)
        if output_path.exists() and options["apply"]:
            raise CommandError("Refusing to overwrite an existing backup artifact.")

        self.stdout.write(f"mode={'apply' if options['apply'] else 'dry-run'}")
        self.stdout.write(f"output={output_path}")
        if not options["apply"]:
            self.stdout.write("validated=true")
            return

        pg_dump = ensure_tool("pg_dump")
        run_postgres_tool(
            [pg_dump, "--format=custom", "--file", str(output_path), *parts],
            env=env,
        )
        self.stdout.write("created=true")
