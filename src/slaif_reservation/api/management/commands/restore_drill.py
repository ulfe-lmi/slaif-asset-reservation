"""Codified isolated backup/restore drill (OAP order 017-a).

Runs a real, isolated PostgreSQL round trip against loopback/disposable
infrastructure, with no mocks:

1. ``pg_dump --format=custom`` from the source database into a drill
   artifact, reusing ``backup_database`` by import.
2. ``CREATE DATABASE`` for a drill-created target database on the target
   server. The drill never touches pre-existing databases: a target
   database that already exists is refused.
3. ``pg_restore --clean --if-exists --no-owner`` into the target database,
   reusing ``restore_database`` by import.
4. Verification with structured key=value evidence: row-count equality for
   all domain tables and ``django_migrations``; the named GiST exclusion
   constraint present and actually blocking a conflicting overlapping
   insert; an optional API token round trip through the real verifier path
   against the restored database; a point-in-time probe (a reservation
   created on the source after the backup must be absent from the target);
   source-unchanged accounting; and migration equality.
5. Scoped cleanup: ``DROP DATABASE`` for the drill-created target only and
   removal of the drill workdir. On failure the target database is dropped
   (when the drill created it) and the artifact path is retained in the
   output for operator inspection.

Dry-run is the default and performs all validations with zero side
effects (no artifact, no target database, no source write).

The connecting user must have CREATEDB on the target server; a disposable
local PostgreSQL 17 instance is sufficient (see
``docs/runbooks/backup-and-restore.md``). The source database must contain
at least one confirmed reservation (the drill overlaps it to prove the
exclusion constraint) and at least one active, reservable, exclusive asset
with a resolvable policy (the point-in-time probe).

Set ``RESTORE_DRILL_TOKEN_PROBE`` to a bearer token plaintext so the drill
can prove that one restored token authenticates through the real verifier
path using the restored database's stored verifier. The value is read from
the environment deliberately so it never appears in argv or in output; when
unset, the drill reports ``token_round_trip=skipped`` and completes the
other verifications.
"""

from __future__ import annotations

import os
import shutil
import uuid
from dataclasses import dataclass
from datetime import timedelta
from io import StringIO
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

import psycopg
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import connection, connections
from django.db.backends.postgresql.base import DatabaseWrapper
from django.utils import timezone
from psycopg.sql import SQL, Identifier

from slaif_reservation.accounts.models import ApiToken, User
from slaif_reservation.accounts.tokens import (
    api_token_verifier,
    api_token_verifier_matches,
    parse_bearer_token,
)
from slaif_reservation.api.management.commands._postgres_tools import (
    database_url_from_env,
    ensure_tool,
    postgres_command_parts,
)
from slaif_reservation.api.management.commands.backup_database import (
    Command as BackupDatabaseCommand,
)
from slaif_reservation.api.management.commands.restore_database import (
    Command as RestoreDatabaseCommand,
)
from slaif_reservation.api.models import IdempotencyRecord
from slaif_reservation.assets.models import Asset
from slaif_reservation.audit.models import AuditEvent
from slaif_reservation.config.env import postgres_database_from_url
from slaif_reservation.reservations.exceptions import ReservationDomainError
from slaif_reservation.reservations.models import (
    MaintenanceBlackout,
    Reservation,
    ReservationPolicy,
)
from slaif_reservation.reservations.services import create_reservation, resolve_effective_policy

ARTIFACT_NAME = "drill.dump"
DEFAULT_WORKDIR = Path("build") / "restore-drill"
TARGET_ALIAS = "restore_drill_target"
TOKEN_PROBE_ENV = "RESTORE_DRILL_TOKEN_PROBE"
CONNECT_TIMEOUT_SECONDS = 10

COUNT_MODELS: list[tuple[str, Any]] = [
    ("users", User),
    ("assets", Asset),
    ("reservation_policies", ReservationPolicy),
    ("reservations", Reservation),
    ("maintenance_blackouts", MaintenanceBlackout),
    ("audit_events", AuditEvent),
    ("api_tokens", ApiToken),
    ("idempotency_records", IdempotencyRecord),
]

# Candidate point-in-time probe windows: (start offset minutes, duration minutes).
PROBE_WINDOWS: tuple[tuple[int, int], ...] = (
    (30, 30),
    (60, 30),
    (120, 60),
    (240, 60),
    (480, 120),
    (1440, 120),
    (2880, 120),
    (4320, 240),
)


@dataclass(frozen=True)
class _BeforeSnapshot:
    """Source state captured before the dump; the reference for all equality checks."""

    counts: dict[str, int]
    migrations: tuple[tuple[str, str], ...]
    reservation_ids: tuple[uuid.UUID, ...]


class _DatabaseUrlOverridden:
    """Temporarily point DATABASE_URL at the URL a sibling command should use."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.previous: str | None = None

    def __enter__(self) -> _DatabaseUrlOverridden:
        self.previous = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = self.url
        return self

    def __exit__(self, *exc_info: object) -> None:
        if self.previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self.previous


def _database_name(database_url: str) -> str:
    return unquote(urlsplit(database_url).path.lstrip("/"))


def _maintenance_url(database_url: str) -> str:
    parts = urlsplit(database_url)
    return parts._replace(path="/postgres").geturl()


class Command(BaseCommand):
    help = (
        "Codified isolated backup/restore drill: dump the source, restore into a "
        "drill-created target database, verify the round trip, and clean up. "
        "Dry-run by default; --target-url is required; --apply executes."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--source-url",
            default=None,
            help="PostgreSQL source URL. Defaults to the DATABASE_URL environment variable.",
        )
        parser.add_argument(
            "--target-url",
            required=True,
            help=(
                "PostgreSQL target URL. The database named here must not exist yet: the "
                "drill creates it and drops it again, and never restores over pre-existing data."
            ),
        )
        parser.add_argument(
            "--workdir",
            default=None,
            help=(
                "Directory for the drill artifact. Default: <repo>/build/restore-drill "
                "(git-ignored). Relative paths are resolved against the current directory."
            ),
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Execute the drill. Omit for validation-only dry-run.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        source_url = (options["source_url"] or "").strip() or database_url_from_env()
        target_url = (options["target_url"] or "").strip()
        if options["workdir"]:
            workdir = Path(options["workdir"]).expanduser()
            if not workdir.is_absolute():
                workdir = Path.cwd() / workdir
        else:
            workdir = Path(settings.BASE_DIR) / DEFAULT_WORKDIR

        self._validate_urls(source_url, target_url)
        target_db = _database_name(target_url)
        self._refuse_if_target_exists(target_url, target_db)
        ensure_tool("pg_dump")
        ensure_tool("pg_restore")
        self._validate_workdir(workdir, apply_mode=bool(options["apply"]))
        artifact = workdir / ARTIFACT_NAME
        self._target_url = target_url
        self._target_db = target_db

        self.stdout.write(f"mode={'apply' if options['apply'] else 'dry-run'}")
        self._emit_identity(source_url, target_url)
        self.stdout.write(f"workdir={workdir}")
        self.stdout.write(f"artifact={artifact}")

        if not options["apply"]:
            self.stdout.write("plan=dump;create-target-database;restore;verify;cleanup")
            self.stdout.write("validated=true")
            return

        target_created = False
        try:
            self._dump(source_url, artifact)
            self.stdout.write("dump=ok")
            self._create_target_database()
            target_created = True
            self.stdout.write("target_created=true")
            self._restore(artifact)
            self.stdout.write("restore=ok")
            before = self._capture_before()
            self._verify(before)
        except CommandError as exc:
            self.stdout.write(f"failed=true reason={exc}")
            self._scoped_cleanup(target_created, workdir, retain_artifact=True)
            self.stdout.write(f"artifact={artifact}")
            raise
        except Exception as exc:  # truthful, credential-free failure evidence
            self.stdout.write(f"failed=true reason=unexpected {type(exc).__name__}")
            self._scoped_cleanup(target_created, workdir, retain_artifact=True)
            self.stdout.write(f"artifact={artifact}")
            raise CommandError(f"restore_drill failed: {type(exc).__name__}") from None

        self._scoped_cleanup(target_created, workdir, retain_artifact=False)
        self.stdout.write("completed=true")

    # ------------------------------------------------------------------ validation

    def _validate_urls(self, source_url: str, target_url: str) -> None:
        try:
            postgres_command_parts(source_url)
        except CommandError:
            raise CommandError(
                "Refusing drill: source URL is not a usable PostgreSQL URL."
            ) from None
        try:
            postgres_command_parts(target_url)
        except CommandError:
            raise CommandError(
                "Refusing drill: target URL is not a usable PostgreSQL URL."
            ) from None
        source = urlsplit(source_url)
        target = urlsplit(target_url)
        if (
            source.hostname
            and source.hostname == target.hostname
            and source.port == target.port
            and _database_name(source_url) == _database_name(target_url)
        ):
            raise CommandError(
                "Refusing drill: target database is not distinct from the source database."
            )

    def _refuse_if_target_exists(self, target_url: str, target_db: str) -> None:
        try:
            with psycopg.connect(
                _maintenance_url(target_url),
                autocommit=True,
                connect_timeout=CONNECT_TIMEOUT_SECONDS,
            ) as conn:
                row = conn.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s", [target_db]
                ).fetchone()
        except psycopg.Error as exc:
            raise CommandError(
                "Target precheck failed (target server unreachable, or no 'postgres' "
                f"maintenance database): {type(exc).__name__}"
            ) from None
        if row is not None:
            raise CommandError(
                f"Refusing drill: target database {target_db} already exists on the target server."
            )

    def _validate_workdir(self, workdir: Path, *, apply_mode: bool) -> None:
        if workdir.exists():
            if workdir.is_file():
                raise CommandError(f"Refusing drill: workdir {workdir} is a file.")
            if not os.access(workdir, os.W_OK):
                raise CommandError(f"Refusing drill: workdir {workdir} is not writable.")
        elif apply_mode:
            workdir.mkdir(parents=True)
            if not os.access(workdir, os.W_OK):
                raise CommandError(f"Refusing drill: workdir {workdir} is not writable.")
        else:
            anchor = workdir
            while not anchor.exists():
                anchor = anchor.parent
            if not anchor.is_dir() or not os.access(anchor, os.W_OK):
                raise CommandError(f"Refusing drill: workdir {workdir} would not be writable.")
        if (workdir / ARTIFACT_NAME).exists():
            raise CommandError(
                f"Refusing drill: stale drill artifact {workdir / ARTIFACT_NAME} from a "
                "previous run; remove it first."
            )

    # ------------------------------------------------------------------- execution

    def _dump(self, source_url: str, artifact: Path) -> None:
        with _DatabaseUrlOverridden(source_url):
            backup = BackupDatabaseCommand(stdout=StringIO())
            backup.handle(output=str(artifact), apply=True)

    def _restore(self, artifact: Path) -> None:
        with _DatabaseUrlOverridden(self._target_url):
            restore = RestoreDatabaseCommand(stdout=StringIO())
            restore.handle(input=str(artifact), apply=True)

    def _create_target_database(self) -> None:
        try:
            with psycopg.connect(
                _maintenance_url(self._target_url),
                autocommit=True,
                connect_timeout=CONNECT_TIMEOUT_SECONDS,
            ) as conn:
                conn.execute(SQL("CREATE DATABASE {}").format(Identifier(self._target_db)))
        except psycopg.Error as exc:
            raise CommandError(f"Target database creation failed: {type(exc).__name__}") from None

    # ----------------------------------------------------------------- verification

    def _capture_before(self) -> _BeforeSnapshot:
        counts = {key: model.objects.count() for key, model in COUNT_MODELS}
        with connection.cursor() as cur:
            cur.execute("SELECT app, name FROM django_migrations ORDER BY app, name")
            migrations = tuple((str(app), str(name)) for app, name in cur.fetchall())
        reservation_ids = tuple(Reservation.objects.values_list("id", flat=True))
        return _BeforeSnapshot(
            counts=counts, migrations=migrations, reservation_ids=reservation_ids
        )

    def _verify(self, before: _BeforeSnapshot) -> None:
        failures: list[str] = []
        target = self._register_target_connection()
        try:
            target.ensure_connection()
            self._verify_counts(before, failures)
            self._verify_migrations(before, failures)
            self._verify_exclusion_constraint(failures)
            self._verify_token_round_trip(failures)
            if not failures:
                probe = self._create_probe_reservation()
                self._verify_probe_and_source(before, probe, failures)
            if failures:
                raise CommandError("Verification failed: " + "; ".join(failures))
        finally:
            target.close()
            del connections[TARGET_ALIAS]

    def _verify_counts(self, before: _BeforeSnapshot, failures: list[str]) -> None:
        mismatched: list[str] = []
        for key, model in COUNT_MODELS:
            source_count = before.counts[key]
            target_count = model.objects.using(TARGET_ALIAS).count()
            self.stdout.write(
                f"counts.{key}.source={source_count} counts.{key}.target={target_count}"
            )
            if source_count != target_count:
                mismatched.append(key)
        if mismatched:
            self.stdout.write(f"row_counts_equal=false mismatched={','.join(mismatched)}")
            failures.append(f"row count mismatch for {', '.join(mismatched)}")
        else:
            self.stdout.write("row_counts_equal=true")

    def _verify_migrations(self, before: _BeforeSnapshot, failures: list[str]) -> None:
        with connections[TARGET_ALIAS].cursor() as cur:
            cur.execute("SELECT app, name FROM django_migrations ORDER BY app, name")
            target_rows = frozenset((str(app), str(name)) for app, name in cur.fetchall())
        source_rows = frozenset(before.migrations)
        self.stdout.write(
            f"migrations.source={len(source_rows)} migrations.target={len(target_rows)}"
        )
        if source_rows != target_rows:
            self.stdout.write("migrations_equal=false")
            failures.append(
                "django_migrations mismatch "
                f"missing={len(source_rows - target_rows)} extra={len(target_rows - source_rows)}"
            )
        else:
            self.stdout.write("migrations_equal=true")

    def _verify_exclusion_constraint(self, failures: list[str]) -> None:
        constraint_name = Reservation.EXCLUSION_CONSTRAINT_NAME
        self.stdout.write(f"exclusion_constraint.name={constraint_name}")
        conn = psycopg.connect(
            self._target_url, autocommit=False, connect_timeout=CONNECT_TIMEOUT_SECONDS
        )
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_constraint WHERE conname = %s", [constraint_name])
                present = cur.fetchone() is not None
                self.stdout.write(f"exclusion_constraint.present={str(present).lower()}")
                if not present:
                    failures.append("named GiST exclusion constraint missing on restored target")
                    return
                cur.execute(
                    "SELECT id, asset_id, requested_by_user_id, start_at, effective_end_at "
                    "FROM reservations_reservation WHERE status = 'confirmed' "
                    "ORDER BY start_at, id LIMIT 1"
                )
                anchor = cur.fetchone()
                if anchor is None:
                    failures.append(
                        "no confirmed reservation in restored data; overlap "
                        "blocking cannot be proven"
                    )
                    return
                _anchor_id, asset_id, user_id, start_at, _effective_end_at = anchor
                probe_end = start_at + timedelta(seconds=1)
                now = timezone.now()
                try:
                    cur.execute(
                        "INSERT INTO reservations_reservation ("
                        "id, asset_id, requested_by_user_id, source, status, start_at, end_at, "
                        "effective_end_at, purpose, released_at, cancelled_at, cancelled_by_id, "
                        "cancellation_reason, created_at, updated_at"
                        ") VALUES (%s, %s, %s, 'admin', 'confirmed', %s, %s, %s, '', "
                        "NULL, NULL, NULL, '', %s, %s)",
                        (uuid.uuid4(), asset_id, user_id, start_at, probe_end, probe_end, now, now),
                    )
                except psycopg.errors.ExclusionViolation as exc:
                    if exc.diag.constraint_name != constraint_name:
                        failures.append(
                            f"unexpected constraint {exc.diag.constraint_name} "
                            "blocked the probe insert"
                        )
                    else:
                        self.stdout.write("exclusion_constraint.blocks_overlap=true")
                else:
                    failures.append("conflicting overlapping insert unexpectedly succeeded")
            conn.rollback()
        except psycopg.Error as exc:
            conn.rollback()
            failures.append(f"exclusion constraint check error: {type(exc).__name__}")
        finally:
            conn.close()

    def _verify_token_round_trip(self, failures: list[str]) -> None:
        probe = os.environ.get(TOKEN_PROBE_ENV, "").strip()
        if not probe:
            self.stdout.write(f"token_round_trip=skipped reason={TOKEN_PROBE_ENV} not set")
            return
        try:
            parsed = parse_bearer_token(probe)
        except ValueError:
            failures.append("token round trip failed: probe is not a well-formed bearer token")
            return
        try:
            token = (
                ApiToken.objects.using(TARGET_ALIAS).select_related("owner").get(pk=parsed.token_id)
            )
        except ApiToken.DoesNotExist:
            failures.append("token round trip failed: token not present in restored database")
            return
        try:
            if token.owner is None:
                raise CommandError("owner row missing in restored database")
            candidate = api_token_verifier(bearer_token=probe, pepper=settings.API_TOKEN_PEPPER)
            if not api_token_verifier_matches(candidate=candidate, expected=token.verifier):
                raise CommandError("restored verifier does not match the real verifier path")
            if not token.owner.is_active or token.owner.is_service_account:
                raise CommandError("token owner is not an active human user")
            if token.revoked_at is not None:
                raise CommandError("token is revoked in the restored database")
            if token.expires_at <= timezone.now():
                raise CommandError("token is expired in the restored database")
        except CommandError as exc:
            failures.append(f"token round trip failed: {exc}")
            return
        self.stdout.write("token_round_trip=true")

    def _create_probe_reservation(self) -> Reservation:
        principal = (
            User.objects.filter(is_active=True, is_service_account=False).order_by("id").first()
        )
        if principal is None:
            raise CommandError("point-in-time probe failed: no active human user on the source")
        asset: Asset | None = None
        for candidate in Asset.objects.filter(
            active=True, reservable=True, booking_mode=Asset.BOOKING_EXCLUSIVE
        ).order_by("id"):
            try:
                resolve_effective_policy(candidate)
            except ReservationDomainError:
                continue
            asset = candidate
            break
        if asset is None:
            raise CommandError(
                "point-in-time probe failed: no active, reservable, exclusive asset with a "
                "resolvable policy on the source"
            )
        now = timezone.now()
        last_error: ReservationDomainError | None = None
        for offset_minutes, duration_minutes in PROBE_WINDOWS:
            start_at = now + timedelta(minutes=offset_minutes)
            end_at = start_at + timedelta(minutes=duration_minutes)
            try:
                result = create_reservation(
                    asset=asset,
                    requested_by_user=principal,
                    start_at=start_at,
                    end_at=end_at,
                    purpose="restore drill point-in-time probe",
                    source=Reservation.SOURCE_ADMIN,
                    now=now,
                )
            except ReservationDomainError as exc:
                last_error = exc
                continue
            self.stdout.write("post_backup_probe.created=true")
            self.stdout.write(f"post_backup_probe.id={result.reservation.id}")
            self.stdout.write(f"post_backup_probe.asset_slug={asset.slug}")
            return result.reservation
        detail = str(last_error) if last_error is not None else "no probe window attempted"
        raise CommandError(f"point-in-time probe failed: {detail}")

    def _verify_probe_and_source(
        self, before: _BeforeSnapshot, probe: Reservation, failures: list[str]
    ) -> None:
        if Reservation.objects.using(TARGET_ALIAS).filter(id=probe.id).exists():
            self.stdout.write("post_backup_probe.absent_on_target=false")
            failures.append("post-backup probe reservation present on the target")
        else:
            self.stdout.write("post_backup_probe.absent_on_target=true")

        after_counts = {key: model.objects.count() for key, model in COUNT_MODELS}
        expected = dict(before.counts)
        expected["reservations"] = before.counts["reservations"] + 1
        expected["audit_events"] = before.counts["audit_events"] + 1
        drift = [key for key, _model in COUNT_MODELS if after_counts[key] != expected[key]]
        if drift:
            self.stdout.write(f"source_unchanged=false drifted={','.join(drift)}")
            failures.append(f"source row counts drifted for {', '.join(drift)}")
        preserved = (
            0
            if not before.reservation_ids
            else Reservation.objects.filter(id__in=before.reservation_ids).count()
        )
        if preserved != len(before.reservation_ids):
            self.stdout.write("source_unchanged=false reservation_ids_missing=true")
            failures.append("pre-drill reservation rows missing from the source")
        if not drift and preserved == len(before.reservation_ids):
            self.stdout.write(f"source.reservations.after={after_counts['reservations']}")
            self.stdout.write(f"source.audit_events.after={after_counts['audit_events']}")
            self.stdout.write("source_unchanged=true")

    # ------------------------------------------------------------------ connection

    def _register_target_connection(self) -> DatabaseWrapper:
        if TARGET_ALIAS in connections:
            raise CommandError("internal error: target alias already registered")
        config: dict[str, Any] = postgres_database_from_url(self._target_url)
        # Mirror the per-database defaults ConnectionHandler.configure_settings applies.
        config.setdefault("ATOMIC_REQUESTS", False)
        config.setdefault("AUTOCOMMIT", True)
        config.setdefault("CONN_MAX_AGE", 0)
        config.setdefault("CONN_HEALTH_CHECKS", False)
        config.setdefault("OPTIONS", {})
        config.setdefault("TIME_ZONE", None)
        wrapper = DatabaseWrapper(config, TARGET_ALIAS)
        connections[TARGET_ALIAS] = wrapper
        return wrapper

    # -------------------------------------------------------------------- cleanup

    def _scoped_cleanup(
        self, target_created: bool, workdir: Path, *, retain_artifact: bool
    ) -> None:
        if target_created:
            try:
                with psycopg.connect(
                    _maintenance_url(self._target_url),
                    autocommit=True,
                    connect_timeout=CONNECT_TIMEOUT_SECONDS,
                ) as conn:
                    conn.execute(SQL("DROP DATABASE {}").format(Identifier(self._target_db)))
                self.stdout.write("cleanup.target_dropped=true")
            except psycopg.Error as exc:
                self.stdout.write(f"cleanup.target_dropped=false reason={type(exc).__name__}")
        else:
            self.stdout.write("cleanup.target_dropped=not-created")
        if retain_artifact:
            self.stdout.write("cleanup.workdir_removed=skipped artifact_retained=true")
            return
        if workdir.exists():
            try:
                shutil.rmtree(workdir)
                self.stdout.write("cleanup.workdir_removed=true")
            except OSError as exc:
                self.stdout.write(f"cleanup.workdir_removed=false reason={type(exc).__name__}")

    # -------------------------------------------------------------------- identity

    def _emit_identity(self, source_url: str, target_url: str) -> None:
        for role, url in (("source", source_url), ("target", target_url)):
            parts = urlsplit(url)
            self.stdout.write(f"{role}_host={parts.hostname}")
            if parts.port is not None:
                self.stdout.write(f"{role}_port={parts.port}")
            self.stdout.write(f"{role}_database={_database_name(url)}")
