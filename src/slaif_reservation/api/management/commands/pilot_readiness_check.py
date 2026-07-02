from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone

from slaif_reservation.accounts.models import ApiToken, User
from slaif_reservation.api.models import IdempotencyRecord
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.config.operational import unapplied_migrations_exist
from slaif_reservation.reservations import services as reservation_services
from slaif_reservation.reservations.models import MaintenanceBlackout, ReservationPolicy

RECENT_AUDIT_WINDOW = timedelta(days=7)


@dataclass(frozen=True)
class ReadinessCheck:
    id: str
    level: str
    required: bool
    detail: str


class Command(BaseCommand):
    help = "Report read-only internal-alpha pilot readiness counts and gates."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--json",
            action="store_true",
            dest="json_output",
            help="Emit deterministic JSON output.",
        )
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Exit non-zero when required pilot readiness gates fail.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        report = build_readiness_report()
        if options["json_output"]:
            self.stdout.write(json.dumps(report, sort_keys=True, separators=(",", ":")))
        else:
            self._write_human_report(report)

        if options["strict"] and report["status"] == "fail":
            raise CommandError("pilot readiness check failed")

    def _write_human_report(self, report: dict[str, Any]) -> None:
        self.stdout.write(f"pilot_readiness={report['status']}")
        self.stdout.write("counts:")
        for key, value in report["counts"].items():
            self.stdout.write(f"  {key}={value}")
        self.stdout.write("checks:")
        for check in report["checks"]:
            self.stdout.write(f"  {check['level'].upper()} {check['id']}: {check['detail']}")


def build_readiness_report() -> dict[str, Any]:
    now = timezone.now()
    counts = readiness_counts(now=now)
    checks = readiness_checks(counts=counts)
    status = readiness_status(checks)
    return {
        "schema_version": 1,
        "status": status,
        "counts": counts,
        "checks": [asdict(check) for check in checks],
    }


def readiness_counts(*, now: datetime) -> dict[str, int]:
    recent_audit_cutoff = now - RECENT_AUDIT_WINDOW
    active_tokens = ApiToken.objects.filter(revoked_at__isnull=True, expires_at__gt=now)
    expired_tokens = ApiToken.objects.filter(revoked_at__isnull=True, expires_at__lte=now)
    revoked_tokens = ApiToken.objects.filter(revoked_at__isnull=False)
    active_reservable_assets = Asset.objects.filter(
        active=True,
        reservable=True,
        booking_mode=Asset.BOOKING_EXCLUSIVE,
    )
    counts = {
        "active_staff_users": User.objects.filter(
            is_active=True,
            is_staff=True,
            is_service_account=False,
        ).count(),
        "active_human_users": User.objects.filter(
            is_active=True,
            is_service_account=False,
        ).count(),
        "active_non_staff_human_users": User.objects.filter(
            is_active=True,
            is_staff=False,
            is_service_account=False,
        ).count(),
        "active_assets": Asset.objects.filter(active=True).count(),
        "active_reservable_exclusive_assets": active_reservable_assets.count(),
        "active_reservation_policies": ReservationPolicy.objects.filter(active=True).count(),
        "assets_without_effective_policy": assets_without_effective_policy_count(
            active_reservable_assets
        ),
        "active_blackouts": MaintenanceBlackout.objects.filter(active=True).count(),
        "recent_audit_events": AuditEvent.objects.filter(
            occurred_at__gte=recent_audit_cutoff
        ).count(),
        "successful_blackout_audit_events": AuditEvent.objects.filter(
            action=AuditEvent.ACTION_BLACKOUT_CREATED
        ).count(),
        "api_tokens_present": ApiToken.objects.count(),
        "api_tokens_active": active_tokens.count(),
        "api_tokens_expired": expired_tokens.count(),
        "api_tokens_revoked": revoked_tokens.count(),
        "expired_idempotency_records": IdempotencyRecord.objects.filter(
            expires_at__lte=now
        ).count(),
    }
    migration_ready = database_migration_ready()
    counts["database_migration_ready"] = int(migration_ready)
    return counts


def assets_without_effective_policy_count(assets: Any) -> int:
    missing = 0
    for asset in assets.only("id", "parent_id"):
        try:
            reservation_services.resolve_effective_policy(asset)
        except Exception:
            missing += 1
    return missing


def database_migration_ready() -> bool:
    try:
        connection.ensure_connection()
        return not unapplied_migrations_exist()
    except Exception:
        return False


def readiness_checks(*, counts: dict[str, int]) -> list[ReadinessCheck]:
    checks = [
        required_count_check(
            "active_staff_user",
            counts["active_staff_users"],
            "at least one active non-service-account staff user is required",
        ),
        required_count_check(
            "active_reservable_exclusive_asset",
            counts["active_reservable_exclusive_assets"],
            "at least one active reservable exclusive asset is required",
        ),
        required_count_check(
            "active_reservation_policy",
            counts["active_reservation_policies"],
            "at least one active reservation policy is required",
        ),
        ReadinessCheck(
            id="database_migration_ready",
            level="pass" if counts["database_migration_ready"] else "fail",
            required=True,
            detail=(
                "database connection and migration state are ready"
                if counts["database_migration_ready"]
                else "database connection or migration readiness failed"
            ),
        ),
        warning_count_check(
            "ordinary_pilot_users",
            counts["active_non_staff_human_users"],
            "no active ordinary pilot users found",
        ),
        ReadinessCheck(
            id="assets_without_effective_policy",
            level="warn" if counts["assets_without_effective_policy"] else "pass",
            required=False,
            detail=(
                "all active reservable exclusive assets have an effective policy"
                if counts["assets_without_effective_policy"] == 0
                else (
                    f"{counts['assets_without_effective_policy']} active reservable exclusive "
                    "asset(s) lack an effective policy"
                )
            ),
        ),
        warning_count_check(
            "recent_audit_events",
            counts["recent_audit_events"],
            "no audit events occurred in the recent readiness window",
        ),
        ReadinessCheck(
            id="expired_idempotency_records",
            level="warn" if counts["expired_idempotency_records"] else "pass",
            required=False,
            detail=(
                "no expired idempotency records found"
                if counts["expired_idempotency_records"] == 0
                else (
                    f"{counts['expired_idempotency_records']} expired idempotency record(s) "
                    "should be purged before pilot use"
                )
            ),
        ),
        warning_count_check(
            "successful_blackout_exercise",
            counts["successful_blackout_audit_events"],
            "no successful blackout creation audit event found",
        ),
    ]
    return sorted(checks, key=lambda item: item.id)


def required_count_check(check_id: str, count: int, failure_detail: str) -> ReadinessCheck:
    return ReadinessCheck(
        id=check_id,
        level="pass" if count > 0 else "fail",
        required=True,
        detail=failure_detail if count == 0 else "required gate has evidence",
    )


def warning_count_check(check_id: str, count: int, warning_detail: str) -> ReadinessCheck:
    return ReadinessCheck(
        id=check_id,
        level="pass" if count > 0 else "warn",
        required=False,
        detail="recommended evidence is present" if count > 0 else warning_detail,
    )


def readiness_status(checks: list[ReadinessCheck]) -> str:
    if any(check.required and check.level == "fail" for check in checks):
        return "fail"
    if any(check.level == "warn" for check in checks):
        return "warn"
    return "pass"
