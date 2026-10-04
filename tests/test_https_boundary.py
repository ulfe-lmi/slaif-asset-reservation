"""Owned real-HTTPS boundary qualification wrapper (OAP 033-a).

These tests drive ``deploy/rehearse_https_boundary.sh`` as a bounded
subprocess. The script itself owns every resource it touches (a fresh
work directory, a fresh source copy, uniquely named PostgreSQL 17
container/volume, loopback ports, owned process sessions) and refuses
foreign resources; the tests here add the ownership guarantees that a
subprocess wrapper must enforce:

- an honest skip (42) when the pinned Caddy or tooling is absent, never
  a fake pass;
- the captured script output never carries the synthetic database
  password (sentinel value set by this test);
- rehearsal-owned container/volume identities are gone after a run;
- a foreign container that merely holds the rehearsal's owned name is
  refused, not adopted: the run fails and the foreign container is left
  untouched.

No public exposure, no OS trust-store change, no inherited environment:
the script unsets DATABASE_URL/TEST_DATABASE_URL and never loads the
repository .env.
"""

from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
REHEARSAL_SCRIPT = REPO_ROOT / "deploy" / "rehearse_https_boundary.sh"
# Synthetic sentinel: if it ever appears in captured output, a secret
# leaked. Held in memory only; it is a test-owned synthetic value.
DB_PASSWORD_SENTINEL = "synthetic-oap-033a-boundary-db-password-000000"
RUN_TIMEOUT_S = 900.0
OWNED_CONTAINER_PREFIX = "slaif033a-bdb-"
OWNED_VOLUME_PREFIX = "slaif033a-bvol-"


def _docker(*args: str) -> str:
    result = subprocess.run(["docker", *args], capture_output=True, text=True, check=False)
    return result.stdout


def _script_env(**extra: str) -> dict[str, str]:
    env = dict(os.environ)
    # Never let inherited product configuration into the rehearsal.
    for name in ("DATABASE_URL", "TEST_DATABASE_URL", "DJANGO_SETTINGS_MODULE"):
        env.pop(name, None)
    env.update(extra)
    return env


def _run_rehearsal(**extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(REHEARSAL_SCRIPT)],
        cwd=REPO_ROOT,
        env=_script_env(**extra),
        capture_output=True,
        text=True,
        timeout=RUN_TIMEOUT_S,
        check=False,
    )


@pytest.fixture(scope="module")
def rehearsal(**extra: str) -> subprocess.CompletedProcess[str]:
    return _run_rehearsal(SLAIF033A_BOUNDARY_DB_PASSWORD=DB_PASSWORD_SENTINEL)


def test_https_boundary_rehearsal_passes(rehearsal: subprocess.CompletedProcess[str]) -> None:
    if rehearsal.returncode == 42:
        pytest.skip(
            "HTTPS boundary qualification prerequisites missing "
            "(pinned Caddy v2.11.6 / openssl / curl / docker); "
            "the rehearsal script exited 42, no check was faked"
        )
    assert rehearsal.returncode == 0, (
        f"rehearsal exited {rehearsal.returncode}:\n"
        f"stdout:\n{rehearsal.stdout}\nstderr:\n{rehearsal.stderr}"
    )
    assert "https-boundary=FAIL" not in rehearsal.stdout
    assert rehearsal.stdout.strip().splitlines()[-1] == "https-boundary=ok"


def test_https_boundary_output_leaks_no_db_password(
    rehearsal: subprocess.CompletedProcess[str],
) -> None:
    if rehearsal.returncode == 42:
        pytest.skip("rehearsal prerequisites missing (script exited 42)")
    output = f"{rehearsal.stdout}\n{rehearsal.stderr}"
    assert DB_PASSWORD_SENTINEL not in output, "database password leaked in output"


def test_no_owned_residue_after_rehearsal(
    rehearsal: subprocess.CompletedProcess[str],
) -> None:
    if rehearsal.returncode == 42:
        pytest.skip("rehearsal prerequisites missing (script exited 42)")
    containers = [
        line
        for line in _docker(
            "ps", "-a", "--filter", f"name={OWNED_CONTAINER_PREFIX}", "--format", "{{.Names}}"
        ).splitlines()
        if line.strip()
    ]
    volumes = [
        line
        for line in _docker(
            "volume", "ls", "--filter", f"name={OWNED_VOLUME_PREFIX}", "--quiet"
        ).splitlines()
        if line.strip()
    ]
    assert containers == [], f"owned rehearsal containers remain: {containers}"
    assert volumes == [], f"owned rehearsal volumes remain: {volumes}"


def test_https_boundary_refuses_foreign_container() -> None:
    # A container that already holds the rehearsal's owned name is
    # foreign: the script must refuse (non-zero exit, not 42) and leave
    # the container running and untouched. The container below is owned
    # by this test and removed in the finally block.
    foreign = f"{OWNED_CONTAINER_PREFIX}foreign-{uuid.uuid4().hex[:12]}"
    created = _docker(
        "run",
        "-d",
        "--name",
        foreign,
        "alpine:3.20",
        "sleep",
        "600",
    )
    assert created.strip(), "could not create test-owned foreign container"
    try:
        result = _run_rehearsal(SLAIF033A_BOUNDARY_CONTAINER=foreign)
        assert result.returncode != 0, (
            "rehearsal must refuse a foreign container holding its owned name"
        )
        assert result.returncode != 42, "expected the ownership refusal, not a prerequisites skip"
        assert "foreign-container" in result.stdout + result.stderr
        state = _docker("inspect", foreign, "--format", "{{.State.Running}}").strip()
        assert state == "true", "foreign container was touched by the rehearsal"
    finally:
        subprocess.run(["docker", "rm", "-f", foreign], capture_output=True, check=False)
        assert _docker("inspect", foreign, "--format", "{{.Id}}").strip() == "", (
            "test-owned foreign container could not be removed"
        )
