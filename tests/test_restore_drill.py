"""Real PostgreSQL round-trip tests for the codified backup/restore drill (017-a).

These tests run against a real PostgreSQL server: the CI test job provides
the postgres:17 service, and locally any disposable PostgreSQL instance
works (the drill is specified for PostgreSQL 17). The drill's source
database is the pytest test database itself; the drill creates and drops
its own target database on the same server, so the connecting user needs
CREATEDB. All seed data flows through real product entry points: the
bootstrap asset import command, the reservation/policy/blackout service
functions, the API token service, and one real bearer API call (with
Idempotency-Key) to produce an idempotency record.
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
import uuid
from datetime import timedelta
from io import StringIO
from pathlib import Path
from unittest import mock
from urllib.parse import quote

import psycopg
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TransactionTestCase
from django.utils import timezone
from psycopg.sql import SQL, Identifier
from rest_framework.test import APIClient

from slaif_reservation.accounts.models import User
from slaif_reservation.accounts.services import issue_api_token
from slaif_reservation.api.management.commands.restore_drill import COUNT_MODELS
from slaif_reservation.assets.models import Asset
from slaif_reservation.reservations import services
from slaif_reservation.reservations.models import Reservation

REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_ASSETS = REPO_ROOT / "data" / "bootstrap" / "assets.yaml"


def _build_url(database_name: str, *, password: str | None = None) -> str:
    settings = connection.settings_dict
    user = settings.get("USER")
    secret = password if password is not None else settings.get("PASSWORD")
    auth = ""
    if user:
        auth = quote(str(user), safe="")
        if secret:
            auth += f":{quote(str(secret), safe='')}"
        auth += "@"
    host = settings.get("HOST") or "localhost"
    port = settings.get("PORT")
    netloc = f"{host}:{port}" if port else host
    return f"postgres://{auth}{netloc}/{quote(database_name, safe='')}"


def _source_url() -> str:
    return _build_url(connection.settings_dict["NAME"])


def _fresh_target_name(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _maintenance_connection():
    return psycopg.connect(_build_url("postgres"), autocommit=True)


def _db_exists(name: str) -> bool:
    with _maintenance_connection() as conn:
        row = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", [name]).fetchone()
    return row is not None


def _ensure_database(name: str) -> None:
    with _maintenance_connection() as conn:
        conn.execute(SQL("CREATE DATABASE {}").format(Identifier(name)))


def _drop_database(name: str) -> None:
    with _maintenance_connection() as conn:
        conn.execute(SQL("DROP DATABASE IF EXISTS {}").format(Identifier(name)))


def _sentinel_snapshot(database_name: str) -> tuple[tuple[str, ...], tuple[tuple[int], ...]]:
    with psycopg.connect(_build_url(database_name), autocommit=True) as conn:
        tables = tuple(
            row[0]
            for row in conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            )
        )
        rows = tuple((row[0],) for row in conn.execute("SELECT v FROM drill_sentinel ORDER BY v"))
    return tables, rows


def _seed_source() -> dict:
    """Seed committed data through real product entry points."""
    output = StringIO()
    call_command(
        "import_bootstrap_assets", "--input", str(BOOTSTRAP_ASSETS), "--apply", stdout=output
    )
    staff = User.objects.create_user(
        email="drill-staff@example.com", password="not-a-secret", is_staff=True
    )
    member = User.objects.create_user(email="drill-member@example.com", password="not-a-secret")
    services.create_policy(
        actor_user=staff,
        name="drill-global",
        asset=None,
        min_duration_minutes=15,
        max_duration_minutes=480,
        booking_horizon_days=30,
        min_lead_minutes=0,
        cancellation_cutoff_minutes=0,
        max_upcoming_per_principal=10,
        max_concurrent_per_principal=10,
        purpose_required=False,
    )
    now = timezone.now()
    asset = Asset.objects.get(slug="gpx1-gpu")
    seed_reservation = services.create_reservation(
        asset=asset,
        requested_by_user=member,
        start_at=now + timedelta(hours=2),
        end_at=now + timedelta(hours=3),
        purpose="restore drill seed",
        source=Reservation.SOURCE_WEB,
    ).reservation
    services.create_blackout(
        asset=Asset.objects.get(slug="gpx2-gpu"),
        actor_user=staff,
        reason="restore drill seed blackout",
        start_at=now + timedelta(days=5),
        end_at=now + timedelta(days=6),
    )
    issued = issue_api_token(
        owner=member,
        name="drill api token",
        scopes=["reservations:read", "reservations:create"],
        lifetime_days=1,
    )
    # Real bearer API call: creates a reservation plus an idempotency record.
    client = APIClient()
    response = client.post(
        "/api/v1/reservations/",
        {
            "asset_id": str(asset.id),
            "start_at": (now + timedelta(hours=4)).isoformat(),
            "end_at": (now + timedelta(hours=5)).isoformat(),
            "purpose": "restore drill seed via api",
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {issued.bearer_token}",
        HTTP_IDEMPOTENCY_KEY="drill-seed-create-0001",
    )
    assert response.status_code == 201, response.content
    return {"member": member, "bearer": issued.bearer_token, "seed_reservation": seed_reservation}


class RestoreDrillRoundTrip(TransactionTestCase):
    def setUp(self) -> None:
        self.td = Path(tempfile.mkdtemp(prefix="restore-drill-"))
        self.seeded = _seed_source()
        self.before_counts = {key: model.objects.count() for key, model in COUNT_MODELS}

    def tearDown(self) -> None:
        shutil.rmtree(self.td, ignore_errors=True)
        super().tearDown()

    def test_real_round_trip_verifies_and_cleans_up(self) -> None:
        target_name = _fresh_target_name("slaif_drill")
        target_url = _build_url(target_name)
        workdir = self.td / "drill-workdir"
        output = StringIO()

        with mock.patch.dict(os.environ, {"RESTORE_DRILL_TOKEN_PROBE": self.seeded["bearer"]}):
            call_command(
                "restore_drill",
                source_url=_source_url(),
                target_url=target_url,
                workdir=str(workdir),
                apply=True,
                stdout=output,
            )

        text = output.getvalue()
        for expected in (
            "mode=apply",
            "dump=ok",
            "target_created=true",
            "restore=ok",
            "row_counts_equal=true",
            "migrations_equal=true",
            f"exclusion_constraint.name={Reservation.EXCLUSION_CONSTRAINT_NAME}",
            "exclusion_constraint.present=true",
            "exclusion_constraint.blocks_overlap=true",
            "token_round_trip=true",
            "post_backup_probe.created=true",
            "post_backup_probe.absent_on_target=true",
            "source_unchanged=true",
            "cleanup.target_dropped=true",
            "cleanup.workdir_removed=true",
            "completed=true",
        ):
            assert expected in text, f"missing {expected!r} in:\n{text}"

        # Reported counts must match the actual pre-drill source state.
        for key, _model in COUNT_MODELS:
            count = self.before_counts[key]
            line = f"counts.{key}.source={count} counts.{key}.target={count}"
            assert line in text, f"missing {line!r} in:\n{text}"

        # Cleanup really happened: no target database, no workdir.
        assert not _db_exists(target_name)
        assert not workdir.exists()

        # Source is intact; the only additions are the probe reservation and its audit event.
        assert (
            Reservation.objects.get(id=self.seeded["seed_reservation"].id).status
            == Reservation.STATUS_CONFIRMED
        )
        assert Reservation.objects.count() == self.before_counts["reservations"] + 1
        probe_match = re.search(r"post_backup_probe.id=([0-9a-f-]{36})", text)
        assert probe_match is not None
        probe = Reservation.objects.get(id=probe_match.group(1))
        assert probe.status == Reservation.STATUS_CONFIRMED
        assert probe.purpose == "restore drill point-in-time probe"

        # No credential-bearing material in the output.
        assert _source_url() not in text
        assert target_url not in text


class RestoreDrillNegatives(TransactionTestCase):
    def setUp(self) -> None:
        self.td = Path(tempfile.mkdtemp(prefix="restore-drill-neg-"))
        self.seeded = _seed_source()
        self.before_counts = {key: model.objects.count() for key, model in COUNT_MODELS}

    def tearDown(self) -> None:
        shutil.rmtree(self.td, ignore_errors=True)
        super().tearDown()

    def _assert_source_untouched(self) -> None:
        for key, model in COUNT_MODELS:
            assert model.objects.count() == self.before_counts[key], f"source {key} count changed"

    def test_target_equal_to_source_refused(self) -> None:
        output = StringIO()
        with pytest.raises(CommandError, match="not distinct from the source database"):
            call_command(
                "restore_drill",
                source_url=_source_url(),
                target_url=_source_url(),
                workdir=str(self.td / "wd"),
                stdout=output,
            )
        assert not (self.td / "wd").exists()
        self._assert_source_untouched()

    def test_preexisting_target_refused_and_untouched(self) -> None:
        target_name = _fresh_target_name("slaif_drill_pre")
        _ensure_database(target_name)
        try:
            with psycopg.connect(_build_url(target_name), autocommit=True) as conn:
                conn.execute("CREATE TABLE drill_sentinel(v int)")
                conn.execute("INSERT INTO drill_sentinel VALUES (1), (2), (3)")
            snapshot_before = _sentinel_snapshot(target_name)
            output = StringIO()

            with pytest.raises(CommandError, match="already exists on the target server"):
                call_command(
                    "restore_drill",
                    source_url=_source_url(),
                    target_url=_build_url(target_name),
                    workdir=str(self.td / "wd"),
                    apply=True,
                    stdout=output,
                )

            assert _db_exists(target_name)
            assert _sentinel_snapshot(target_name) == snapshot_before
            assert not (self.td / "wd").exists()
            self._assert_source_untouched()
        finally:
            _drop_database(target_name)

    def test_dry_run_has_zero_side_effects(self) -> None:
        target_name = _fresh_target_name("slaif_drill")
        workdir = self.td / "dry-wd"
        output = StringIO()

        call_command(
            "restore_drill",
            source_url=_source_url(),
            target_url=_build_url(target_name),
            workdir=str(workdir),
            stdout=output,
        )

        text = output.getvalue()
        assert "mode=dry-run" in text
        assert "plan=dump;create-target-database;restore;verify;cleanup" in text
        assert "validated=true" in text
        assert not workdir.exists()
        assert not _db_exists(target_name)
        self._assert_source_untouched()

    def test_missing_pg_tools_refused(self) -> None:
        empty_bin = self.td / "empty-bin"
        empty_bin.mkdir()
        output = StringIO()

        with mock.patch.dict(os.environ, {"PATH": str(empty_bin)}):
            with pytest.raises(CommandError, match="pg_dump is required on PATH"):
                call_command(
                    "restore_drill",
                    source_url=_source_url(),
                    target_url=_build_url(_fresh_target_name("slaif_drill")),
                    workdir=str(self.td / "wd"),
                    stdout=output,
                )

    def test_non_postgres_urls_refused(self) -> None:
        output = StringIO()
        with pytest.raises(CommandError, match="target URL is not a usable PostgreSQL URL"):
            call_command(
                "restore_drill",
                source_url=_source_url(),
                target_url="mysql://slaif:slaif@localhost:3306/some_db",
                workdir=str(self.td / "wd"),
                stdout=output,
            )
        output = StringIO()
        with pytest.raises(CommandError, match="source URL is not a usable PostgreSQL URL"):
            call_command(
                "restore_drill",
                source_url="sqlite:///tmp/not-postgres.db",
                target_url=_build_url(_fresh_target_name("slaif_drill")),
                workdir=str(self.td / "wd"),
                stdout=output,
            )

    def test_unwritable_workdir_refused(self) -> None:
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            pytest.skip("running as root; W_OK checks are not meaningful")
        parent = self.td / "ro"
        parent.mkdir()
        workdir = parent / "wd"
        os.chmod(parent, 0o555)
        try:
            output = StringIO()
            with pytest.raises(CommandError, match="would not be writable"):
                call_command(
                    "restore_drill",
                    source_url=_source_url(),
                    target_url=_build_url(_fresh_target_name("slaif_drill")),
                    workdir=str(workdir),
                    stdout=output,
                )
        finally:
            os.chmod(parent, 0o755)

    def test_stale_artifact_refused(self) -> None:
        workdir = self.td / "stale"
        workdir.mkdir()
        (workdir / "drill.dump").write_bytes(b"stale")
        output = StringIO()

        with pytest.raises(CommandError, match="stale drill artifact"):
            call_command(
                "restore_drill",
                source_url=_source_url(),
                target_url=_build_url(_fresh_target_name("slaif_drill")),
                workdir=str(workdir),
                stdout=output,
            )

    def test_no_credential_leak_in_failure_output(self) -> None:
        canary = f"drill-canary-{uuid.uuid4().hex}"
        bad_url = _build_url(_fresh_target_name("slaif_drill"), password=canary)
        output = StringIO()

        with pytest.raises(CommandError, match="Target precheck failed") as excinfo:
            call_command(
                "restore_drill",
                source_url=_source_url(),
                target_url=bad_url,
                workdir=str(self.td / "wd"),
                stdout=output,
            )

        text = output.getvalue() + str(excinfo.value)
        assert canary not in text
        assert bad_url not in text
