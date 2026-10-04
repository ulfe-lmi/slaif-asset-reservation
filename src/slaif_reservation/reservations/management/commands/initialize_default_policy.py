from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from slaif_reservation.reservations.initialization import (
    PRESERVED_REASON,
    initialize_default_policy,
)


class Command(BaseCommand):
    help = (
        "Create the fresh-install default reservation policy when, and only when, "
        "no policy rows exist. Run it deliberately immediately after migrate on "
        "the supported fresh path. Safe to repeat; never writes, audits or "
        "reactivates any pre-existing policy configuration."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            result = initialize_default_policy()
        except DatabaseError as exc:
            raise CommandError(
                "Default policy initialization failed; run migrations first."
            ) from exc

        if result.created:
            policy = result.policy
            assert policy is not None
            self.stdout.write(
                "status=created"
                f" policy_id={policy.id}"
                f" name={policy.name}"
                " asset=null"
                " active=true"
                f" min_duration_minutes={policy.min_duration_minutes}"
                f" max_duration_minutes={policy.max_duration_minutes}"
                f" booking_horizon_days={policy.booking_horizon_days}"
                f" min_lead_minutes={policy.min_lead_minutes}"
                f" cancellation_cutoff_minutes={policy.cancellation_cutoff_minutes}"
                f" max_upcoming_per_principal={policy.max_upcoming_per_principal}"
                f" max_concurrent_per_principal={policy.max_concurrent_per_principal}"
                f" purpose_required={str(policy.purpose_required).lower()}"
                f" correlation={result.correlation_id}"
            )
        else:
            self.stdout.write(
                f"status=skipped reason={PRESERVED_REASON} correlation={result.correlation_id}"
            )
