from __future__ import annotations

from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from slaif_reservation.assets.bootstrap import (
    BootstrapAssetError,
    apply_bootstrap_import,
    load_bootstrap_plan,
    preview_bootstrap_import,
)


class Command(BaseCommand):
    help = "Validate and optionally import the sanitized bootstrap asset inventory."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--input",
            required=True,
            help="Path to sanitized bootstrap assets YAML.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply the import atomically. Omit for dry-run validation only.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        input_path = Path(options["input"])
        apply_mode = bool(options["apply"])
        try:
            plan = load_bootstrap_plan(input_path)
            counts = apply_bootstrap_import(plan) if apply_mode else preview_bootstrap_import(plan)
        except BootstrapAssetError as exc:
            raise CommandError(str(exc)) from exc

        mode = "apply" if apply_mode else "dry-run"
        self.stdout.write(f"mode={mode}")
        for key, value in counts.as_dict().items():
            self.stdout.write(f"{key}={value}")

        if counts.conflicted:
            raise CommandError("Bootstrap import conflicts with existing asset records.")
