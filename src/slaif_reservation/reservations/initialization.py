"""Trusted fresh-install default reservation policy initialization.

Supports the exact A-15/SAR-041 fresh initialization path: a dedicated,
explicit, operator-run command that atomically creates the active global
fallback policy ``default`` only when no policy rows exist. It never
overwrites, reactivates or audits any pre-existing policy configuration,
including deliberate inactive or asset-specific rows. Migrations and
application startup never invoke it; repeated or concurrent runs create at
most one policy and one coupled audit event.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from django.db import connection, transaction

from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.audit.services import append_audit_event
from slaif_reservation.reservations.models import ReservationPolicy

# Chosen explicit defaults for the fresh-install fallback policy. They are
# documentation-visible caps, not permission to change policy evaluation:
# existing duration/horizon/lead/cutoff/principal-limit semantics apply.
DEFAULT_POLICY_NAME = "default"
DEFAULT_MIN_DURATION_MINUTES = 1
DEFAULT_MAX_DURATION_MINUTES = 2880  # 48 hours / 2 days
DEFAULT_BOOKING_HORIZON_DAYS = 7  # measured by reservation START
DEFAULT_MIN_LEAD_MINUTES = 0
DEFAULT_CANCELLATION_CUTOFF_MINUTES = 0
DEFAULT_MAX_UPCOMING_PER_PRINCIPAL = 50
DEFAULT_MAX_CONCURRENT_PER_PRINCIPAL = 8  # proposed-interval overlap count
DEFAULT_PURPOSE_REQUIRED = False

INITIALIZED_REASON = "created"
PRESERVED_REASON = "existing-policy-configuration"


@dataclass(frozen=True)
class InitializationResult:
    created: bool
    policy: ReservationPolicy | None
    correlation_id: uuid.UUID
    reason: str


def default_policy_values() -> dict[str, Any]:
    return {
        "name": DEFAULT_POLICY_NAME,
        "asset": None,
        "active": True,
        "min_duration_minutes": DEFAULT_MIN_DURATION_MINUTES,
        "max_duration_minutes": DEFAULT_MAX_DURATION_MINUTES,
        "booking_horizon_days": DEFAULT_BOOKING_HORIZON_DAYS,
        "min_lead_minutes": DEFAULT_MIN_LEAD_MINUTES,
        "cancellation_cutoff_minutes": DEFAULT_CANCELLATION_CUTOFF_MINUTES,
        "max_upcoming_per_principal": DEFAULT_MAX_UPCOMING_PER_PRINCIPAL,
        "max_concurrent_per_principal": DEFAULT_MAX_CONCURRENT_PER_PRINCIPAL,
        "purpose_required": DEFAULT_PURPOSE_REQUIRED,
    }


def _hold_policy_table_exclusive_lock() -> None:
    """Serialize this absence+insert decision against all policy writers.

    An EXCLUSIVE table lock conflicts with the ROW EXCLUSIVE lock that
    INSERT/UPDATE/DELETE take, so ordinary policy writers (management
    services, API, import) cannot insert or change policy rows while this
    transaction is deciding absence and inserting. EXCLUSIVE locks also
    conflict with each other, so concurrent initializers serialize here.
    Plain reads are unaffected, and the existing active-global unique
    constraint stays as the final guard.
    """
    with connection.cursor() as cursor:
        cursor.execute(f"LOCK TABLE {ReservationPolicy._meta.db_table} IN EXCLUSIVE MODE")


def initialize_default_policy() -> InitializationResult:
    """Atomically create the fresh-install default policy when no policies exist.

    Any pre-existing policy row (active or inactive, global or asset
    specific) makes this a no-op: no writes, no audit, no reactivation.
    The policy insert and its ``reservation_policy.created`` audit are
    coupled in one transaction; an audit failure rolls both back.
    """
    correlation = uuid.uuid4()
    with transaction.atomic():
        _hold_policy_table_exclusive_lock()
        if ReservationPolicy.objects.exists():
            return InitializationResult(
                created=False,
                policy=None,
                correlation_id=correlation,
                reason=PRESERVED_REASON,
            )
        policy = ReservationPolicy(**default_policy_values())
        policy.full_clean()
        policy.save()
        append_audit_event(
            action=AuditEvent.ACTION_POLICY_CREATED,
            target_type="reservation_policy",
            target_id=policy.id,
            correlation_id=correlation,
            source=AuditEvent.SOURCE_ADMIN,
            actor_user=None,
            metadata={
                "asset_id": None,
                "initialization": "initialize_default_policy",
            },
        )
        return InitializationResult(
            created=True,
            policy=policy,
            correlation_id=correlation,
            reason=INITIALIZED_REASON,
        )
