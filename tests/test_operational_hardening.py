from __future__ import annotations

import json
import logging
import os
import re
import socket
import subprocess
from datetime import timedelta
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import RequestFactory, override_settings
from django.utils import timezone

from slaif_reservation.accounts.models import User
from slaif_reservation.accounts.services import issue_api_token
from slaif_reservation.api.models import IdempotencyRecord
from slaif_reservation.config.logging import JsonLogFormatter
from slaif_reservation.config.middleware import (
    UNMATCHED_ROUTE,
    SafeRequestLogMiddleware,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REHEARSAL_SCRIPT = REPO_ROOT / "deploy" / "rehearse_internal_alpha_deployment.sh"
REHEARSAL_ENV = REPO_ROOT / "deploy" / "env.production"
REHEARSAL_PASSWORD = REPO_ROOT / "deploy" / "secrets" / "postgres_password"


def user(email: str = "ops-member@example.com") -> User:
    return User.objects.create_user(email=email, password="not-a-secret")


def token_for(owner: User):
    return issue_api_token(
        owner=owner,
        name="Operations test token",
        scopes=["reservations:read"],
        lifetime_days=1,
    ).token


FAKE_DOCKER_SCRIPT = r"""#!/usr/bin/env bash
printf '%s\n' "$*" >> "$SLAIF_FAKE_DOCKER_LOG"
args="$*"
if [[ "$args" == *"compose"* && "$args" == *"config"* && "$args" == *"--format json"* ]]; then
  port="${SLAIF_APP_HOST_PORT:-8000}"
  printf '%s' '{"services":{"app":{"ports":[{"host_ip":"127.0.0.1","published":"' \
    | tee "$SLAIF_FAKE_DOCKER_RENDERED_CONFIG"
  printf '%s' "$port" | tee -a "$SLAIF_FAKE_DOCKER_RENDERED_CONFIG"
  printf '%s\n' '","target":8000,"protocol":"tcp"}]}}}' \
    | tee -a "$SLAIF_FAKE_DOCKER_RENDERED_CONFIG"
fi
if [[ "$args" == *"image inspect"* ]]; then
  printf '%s\n' "${SLAIF_FAKE_DOCKER_IMAGE_USER:-10001:10001}"
fi
if [[ "$args" == "ps -a --filter "* ]]; then
  state_file="${SLAIF_FAKE_DOCKER_STATE:-}"
  if [[ -n "${SLAIF_FAKE_DOCKER_PS_PHASES:-}" ]]; then
    count_file="${SLAIF_FAKE_DOCKER_PS_COUNT_FILE:-}"
    n=0
    if [[ -n "$count_file" && -f "$count_file" ]]; then
      n="$(cat "$count_file")"
    fi
    n=$((n + 1))
    if [[ -n "$count_file" ]]; then
      printf '%s\n' "$n" > "$count_file"
    fi
    IFS=':' read -r -a phases <<< "$SLAIF_FAKE_DOCKER_PS_PHASES"
    idx=$((n - 1))
    if (( idx >= ${#phases[@]} )); then
      idx=$(( ${#phases[@]} - 1 ))
    fi
    state_file="${phases[$idx]}"
  fi
  if [[ -n "$state_file" && -f "$state_file" ]]; then
    while IFS='|' read -r f_cid f_name f_state f_created f_proj f_ports; do
      [[ -n "$f_cid" ]] || continue
      printf '%s|%s|%s|%s|%s\n' "$f_cid" "$f_name" "$f_state" "$f_created" "$f_proj"
    done < "$state_file"
  fi
  exit 0
fi
if [[ "$args" == *"--format {{json .NetworkSettings.Ports}}"* ]]; then
  rest="${args#*inspect }"
  cid="${rest%% *}"
  state_file="${SLAIF_FAKE_DOCKER_STATE:-}"
  if [[ -n "${SLAIF_FAKE_DOCKER_PS_PHASES:-}" ]]; then
    IFS=':' read -r -a phases <<< "$SLAIF_FAKE_DOCKER_PS_PHASES"
    state_file="${phases[$(( ${#phases[@]} - 1 ))]}"
  fi
  if [[ -n "$state_file" && -f "$state_file" ]]; then
    while IFS='|' read -r f_cid f_name f_state f_created f_proj f_ports; do
      if [[ "$f_cid" == "$cid" ]]; then
        printf '%s\n' "$f_ports"
        break
      fi
    done < "$state_file"
  fi
  exit 0
fi
if [[ "$args" == *"compose"* && "$args" == *down* ]]; then
  set -- $args
  project=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -p)
        project="$2"
        shift 2
        ;;
      *)
        shift
        ;;
    esac
  done
  if [[ -n "$project" && -n "${SLAIF_FAKE_DOCKER_STATE:-}" && -f "$SLAIF_FAKE_DOCKER_STATE" ]]; then
    kept="$(mktemp)"
    while IFS='|' read -r f_cid f_name f_state f_created f_proj f_ports; do
      [[ -n "$f_cid" ]] || continue
      if [[ "$f_proj" != "$project" ]]; then
        printf '%s|%s|%s|%s|%s|%s\n' \
          "$f_cid" "$f_name" "$f_state" "$f_created" "$f_proj" "$f_ports" >> "$kept"
      fi
    done < "$SLAIF_FAKE_DOCKER_STATE"
    mv "$kept" "$SLAIF_FAKE_DOCKER_STATE"
  fi
  exit 0
fi
exit 0
"""


def fake_docker(
    tmp_path: Path,
    *,
    state_file: Path | None = None,
    ps_phases: list[str] | None = None,
    runtime_user: str = "10001:10001",
) -> dict[str, str]:
    """PATH-shimmed fake docker used by the rehearsal tests.

    Every invocation is appended to SLAIF_FAKE_DOCKER_LOG. With no extra state the
    fake only renders the Compose config, exactly as before. Optionally it can
    simulate a pre-existing container inventory for the recovery modes:

    - state_file: rows "cid|name|state|created|project|ports_json"; `docker ps -a
      --filter label=com.docker.compose.project` prints the first five fields,
      `docker inspect <cid>` prints ports_json, and a compose `down -p <project>`
      removes exactly that project's rows.
    - ps_phases: per-`ps`-invocation state files (first invocation is the startup
      scan, second is the port precheck, later invocations reuse the last phase).
    - runtime_user: value `docker image inspect --format {{.Config.User}}` prints.
    """
    log_path = tmp_path / "docker.log"
    rendered_config_path = tmp_path / "rendered-compose.json"
    docker_path = tmp_path / "docker"
    docker_path.write_text(FAKE_DOCKER_SCRIPT, encoding="utf-8")
    docker_path.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    env["SLAIF_FAKE_DOCKER_LOG"] = str(log_path)
    env["SLAIF_FAKE_DOCKER_RENDERED_CONFIG"] = str(rendered_config_path)
    env["SLAIF_FAKE_DOCKER_IMAGE_USER"] = runtime_user
    if state_file is not None:
        env["SLAIF_FAKE_DOCKER_STATE"] = str(state_file)
    if ps_phases is not None:
        env["SLAIF_FAKE_DOCKER_PS_PHASES"] = ":".join(ps_phases)
        env["SLAIF_FAKE_DOCKER_PS_COUNT_FILE"] = str(tmp_path / "fake-docker-pscount")
    return env


def test_rehearsal_config_only_uses_temporary_env_and_cleans_up(tmp_path: Path) -> None:
    assert not REHEARSAL_ENV.exists()
    assert not REHEARSAL_PASSWORD.exists()

    result = subprocess.run(
        [str(REHEARSAL_SCRIPT), "--config-only"],
        cwd=REPO_ROOT,
        env=fake_docker(tmp_path),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "config-only=ok" in result.stdout
    assert not REHEARSAL_ENV.exists()
    assert not REHEARSAL_PASSWORD.exists()
    docker_log = (tmp_path / "docker.log").read_text(encoding="utf-8")
    assert "compose.production.example.yaml" in docker_log
    assert " config" in docker_log


def test_rehearsal_config_only_uses_configured_port_without_base_port(tmp_path: Path) -> None:
    env = fake_docker(tmp_path)
    env["SLAIF_REHEARSAL_PORT"] = "18081"

    result = subprocess.run(
        [str(REHEARSAL_SCRIPT), "--config-only"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert not REHEARSAL_ENV.exists()
    assert not REHEARSAL_PASSWORD.exists()
    rendered_config = json.loads((tmp_path / "rendered-compose.json").read_text(encoding="utf-8"))
    app_ports = rendered_config["services"]["app"]["ports"]
    assert {
        "host_ip": "127.0.0.1",
        "published": "18081",
        "target": 8000,
        "protocol": "tcp",
    } in app_ports
    assert all(
        not (
            item.get("host_ip") == "127.0.0.1"
            and str(item.get("published")) == "8000"
            and str(item.get("target")) == "8000"
        )
        for item in app_ports
    )


def test_rehearsal_refuses_to_overwrite_existing_production_env(tmp_path: Path) -> None:
    REHEARSAL_ENV.write_text("already-present=true\n", encoding="utf-8")
    try:
        result = subprocess.run(
            [str(REHEARSAL_SCRIPT), "--config-only"],
            cwd=REPO_ROOT,
            env=fake_docker(tmp_path),
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        REHEARSAL_ENV.unlink(missing_ok=True)

    assert result.returncode == 1
    assert "already exists" in result.stderr
    assert "already-present=true" not in result.stdout


def test_rehearsal_generated_env_remains_ignored() -> None:
    result = subprocess.run(
        ["git", "check-ignore", "deploy/env.production"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "deploy/env.production"


OWNED_PROJECT = "slaif-alpha-rehearsal-99999"
FOREIGN_PROJECT = "other-project"
REHEARSAL_CREATED_AT = "2026-09-14 02:00:00 +0200 CEST"
CLEANUP_COMMAND = "deploy/rehearse_internal_alpha_deployment.sh --cleanup-owned"


def _container_row(
    cid: str, name: str, state: str, created: str, project: str, ports_json: str
) -> str:
    return f"{cid}|{name}|{state}|{created}|{project}|{ports_json}"


def _owned_app_row(host_port: int) -> str:
    return _container_row(
        "cafe00000001",
        f"{OWNED_PROJECT}-app-1",
        "running",
        REHEARSAL_CREATED_AT,
        OWNED_PROJECT,
        f'{{"8000/tcp": [{{"HostIp": "127.0.0.1", "HostPort": "{host_port}"}}]}}',
    )


def _owned_db_row() -> str:
    return _container_row(
        "cafe00000002",
        f"{OWNED_PROJECT}-db-1",
        "running",
        REHEARSAL_CREATED_AT,
        OWNED_PROJECT,
        '{"5432/tcp": null}',
    )


def _foreign_row(host_port: int) -> str:
    return _container_row(
        "beef00000001",
        f"{FOREIGN_PROJECT}-app-1",
        "running",
        REHEARSAL_CREATED_AT,
        FOREIGN_PROJECT,
        f'{{"8000/tcp": [{{"HostIp": "127.0.0.1", "HostPort": "{host_port}"}}]}}',
    )


def _write_state(tmp_path: Path, name: str, rows: list[str]) -> Path:
    state = tmp_path / name
    state.write_text("".join(row + "\n" for row in rows), encoding="utf-8")
    return state


def _run_rehearsal(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(REHEARSAL_SCRIPT), *args],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _docker_log(tmp_path: Path) -> str:
    return (tmp_path / "docker.log").read_text(encoding="utf-8")


def test_rehearsal_full_mode_refuses_owned_residue_without_up_or_down(
    tmp_path: Path,
) -> None:
    assert not REHEARSAL_ENV.exists()
    assert not REHEARSAL_PASSWORD.exists()
    state = _write_state(
        tmp_path,
        "state",
        [_owned_app_row(18080), _owned_db_row(), _foreign_row(18081)],
    )
    env = fake_docker(tmp_path, state_file=state)

    result = _run_rehearsal([], env)

    assert result.returncode == 1
    assert f"project={OWNED_PROJECT}" in result.stderr
    assert CLEANUP_COMMAND in result.stderr
    assert FOREIGN_PROJECT not in result.stderr
    docker_log = _docker_log(tmp_path)
    assert " up -d" not in docker_log
    assert "down" not in docker_log
    assert "ps -a --filter" in docker_log
    assert not REHEARSAL_ENV.exists()
    assert not REHEARSAL_PASSWORD.exists()


def test_rehearsal_cleanup_owned_removes_only_owned_project(tmp_path: Path) -> None:
    state = _write_state(
        tmp_path,
        "state",
        [_owned_app_row(18080), _owned_db_row(), _foreign_row(18081)],
    )
    env = fake_docker(tmp_path, state_file=state)

    result = _run_rehearsal(["--cleanup-owned"], env)

    assert result.returncode == 0, result.stderr
    assert f"project={OWNED_PROJECT}" in result.stdout
    assert "cleanup=ok" in result.stdout
    docker_log = _docker_log(tmp_path)
    assert docker_log.count("down -v --remove-orphans") == 1
    assert f"-p {OWNED_PROJECT} down -v --remove-orphans" in docker_log
    assert f"-p {FOREIGN_PROJECT}" not in docker_log
    assert docker_log.count("ps -a --filter") == 2
    remaining = state.read_text(encoding="utf-8")
    assert f"{FOREIGN_PROJECT}-app-1" in remaining
    assert f"{OWNED_PROJECT}-app-1" not in remaining
    assert f"{OWNED_PROJECT}-db-1" not in remaining


def test_rehearsal_cleanup_owned_noop_without_residue(tmp_path: Path) -> None:
    state = _write_state(tmp_path, "state", [_foreign_row(18081)])
    env = fake_docker(tmp_path, state_file=state)

    result = _run_rehearsal(["--cleanup-owned"], env)

    assert result.returncode == 0, result.stderr
    assert "no rehearsal-owned projects found" in result.stdout
    assert "down" not in _docker_log(tmp_path)
    assert state.read_text(encoding="utf-8") == _foreign_row(18081) + "\n"


def test_rehearsal_status_lists_owned_residue_read_only(tmp_path: Path) -> None:
    state = _write_state(
        tmp_path,
        "state",
        [_owned_app_row(18080), _owned_db_row(), _foreign_row(18081)],
    )
    env = fake_docker(tmp_path, state_file=state)

    result = _run_rehearsal(["--status"], env)

    assert result.returncode == 0, result.stderr
    assert (
        f"project={OWNED_PROJECT} container={OWNED_PROJECT}-app-1 state=running age="
        in result.stdout
    )
    assert (
        f"project={OWNED_PROJECT} container={OWNED_PROJECT}-db-1 state=running age="
        in result.stdout
    )
    assert re.search(r"state=running age=\d+[dhm]", result.stdout)
    assert f"{FOREIGN_PROJECT}-app-1" not in result.stdout
    docker_log = _docker_log(tmp_path)
    assert docker_log.count("ps -a --filter") == 1
    for mutation in ("down", "up", "build", "inspect", "run"):
        assert mutation not in docker_log, mutation
    assert state.read_text(encoding="utf-8") == "".join(
        row + "\n" for row in [_owned_app_row(18080), _owned_db_row(), _foreign_row(18081)]
    )


def test_rehearsal_status_none_found_is_read_only(tmp_path: Path) -> None:
    state = _write_state(tmp_path, "state", [])
    env = fake_docker(tmp_path, state_file=state)

    result = _run_rehearsal(["--status"], env)

    assert result.returncode == 0, result.stderr
    assert "no rehearsal-owned projects found" in result.stdout
    assert _docker_log(tmp_path).count("ps -a --filter") == 1


def _free_loopback_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def test_rehearsal_port_precheck_refuses_owned_occupant(tmp_path: Path) -> None:
    port = _free_loopback_port()
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", port))
    listener.listen(1)
    phase_empty = _write_state(tmp_path, "phase-empty", [])
    phase_owned = _write_state(tmp_path, "phase-owned", [_owned_app_row(port)])
    env = fake_docker(
        tmp_path,
        state_file=phase_empty,
        ps_phases=[str(phase_empty), str(phase_owned)],
    )
    env["SLAIF_REHEARSAL_PORT"] = str(port)

    try:
        result = _run_rehearsal([], env)
    finally:
        listener.close()

    assert result.returncode == 1
    assert (
        f"host port {port} is occupied by rehearsal-owned container "
        f"{OWNED_PROJECT}-app-1 (project {OWNED_PROJECT})" in result.stderr
    )
    assert CLEANUP_COMMAND in result.stderr
    docker_log = _docker_log(tmp_path)
    assert "kill" not in docker_log
    assert " up -d db" in docker_log
    assert " up -d app" not in docker_log


def test_rehearsal_port_precheck_refuses_foreign_occupant(tmp_path: Path) -> None:
    port = _free_loopback_port()
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", port))
    listener.listen(1)
    phase_empty = _write_state(tmp_path, "phase-empty", [])
    phase_foreign = _write_state(tmp_path, "phase-foreign", [_foreign_row(port)])
    env = fake_docker(
        tmp_path,
        state_file=phase_empty,
        ps_phases=[str(phase_empty), str(phase_foreign)],
    )
    env["SLAIF_REHEARSAL_PORT"] = str(port)

    try:
        result = _run_rehearsal([], env)
    finally:
        listener.close()

    assert result.returncode == 1
    assert (
        f"host port {port} is in use by a non-rehearsal process; "
        "choose another SLAIF_REHEARSAL_PORT" in result.stderr
    )
    assert "kill" not in _docker_log(tmp_path)
    assert " up -d app" not in _docker_log(tmp_path)


def idempotency_record(*, owner: User, expires_at: timezone.datetime) -> IdempotencyRecord:
    api_token = token_for(owner)
    return IdempotencyRecord.objects.create(
        owner=owner,
        api_token=api_token,
        action="reservations:create",
        idempotency_key=f"ops-key-{IdempotencyRecord.objects.count():04d}",
        canonical_request_hash="0" * 64,
        request_method="POST",
        request_path="/api/v1/reservations/",
        response_status=201,
        response_body={"ok": True},
        target_type="reservation",
        correlation_id=timezone.now()
        .date()
        .replace(year=2026)
        .strftime("00000000-0000-4000-8000-%m%d00000000"),
        expires_at=expires_at,
    )


def test_json_log_formatter_redacts_secret_fields(settings) -> None:
    settings.API_TOKEN_PEPPER = "test-pepper-value-that-must-not-log"
    record = logging.makeLogRecord(
        {
            "name": "slaif_reservation.test",
            "levelno": logging.INFO,
            "levelname": "INFO",
            "msg": (
                "Authorization: Bearer "
                "sar_0123456789abcdef0123456789abcdef_secretsecretsecretsecretsecret12"
            ),
            "authorization": "Bearer not-for-logs",
            "cookie": "sessionid=not-for-logs",
            "pepper": settings.API_TOKEN_PEPPER,
            "path": "/api/v1/me/",
            "status_code": 401,
        }
    )

    payload = json.loads(JsonLogFormatter().format(record))

    rendered = json.dumps(payload)
    assert "sar_0123456789abcdef0123456789abcdef" not in rendered
    assert "not-for-logs" not in rendered
    assert settings.API_TOKEN_PEPPER not in rendered
    assert payload["authorization"] == "[redacted]"
    assert payload["cookie"] == "[redacted]"
    assert payload["pepper"] == "[redacted]"
    assert payload["path"] == "/api/v1/me/"
    assert payload["status_code"] == 401


def test_request_logging_middleware_emits_route_template_without_headers_or_body(caplog) -> None:
    request = RequestFactory().post(
        "/api/v1/reservations/",
        data='{"purpose":"private"}',
        content_type="application/json",
        HTTP_AUTHORIZATION="Bearer not-for-logs",
        HTTP_X_REQUEST_ID="2bb51aa8-c66b-4b09-9534-31ac1e17e1d1",
    )
    request.resolver_match = SimpleNamespace(  # noqa: S105
        route="api/v1/reservations/<int:pk>/"
    )

    def app(_request):
        from django.http import JsonResponse

        return JsonResponse({"ok": True}, status=202)

    caplog.set_level(logging.INFO, logger="slaif_reservation.request")
    response = SafeRequestLogMiddleware(app)(request)

    assert response.status_code == 202
    [record] = [item for item in caplog.records if item.name == "slaif_reservation.request"]
    assert record.path == "api/v1/reservations/<int:pk>/"
    assert record.method == "POST"
    assert record.status_code == 202
    assert record.request_id == "2bb51aa8-c66b-4b09-9534-31ac1e17e1d1"
    assert "not-for-logs" not in record.getMessage()
    assert "private" not in record.getMessage()


def test_request_logging_middleware_never_logs_raw_unmatched_path(caplog) -> None:
    request = RequestFactory().get("/%zz-canary-unmatched-path/?probe=PRIVATE-QUERY-VALUE")

    def app(_request):
        from django.http import JsonResponse

        return JsonResponse({"detail": "not found"}, status=404)

    caplog.set_level(logging.INFO, logger="slaif_reservation.request")
    response = SafeRequestLogMiddleware(app)(request)

    assert response.status_code == 404
    [record] = [item for item in caplog.records if item.name == "slaif_reservation.request"]
    assert record.path == UNMATCHED_ROUTE
    formatted = JsonLogFormatter().format(record)
    assert "zz-canary-unmatched-path" not in formatted
    assert "PRIVATE-QUERY-VALUE" not in formatted


@pytest.mark.django_db
def test_operational_check_success() -> None:
    output = StringIO()

    call_command("operational_check", stdout=output)

    rendered = output.getvalue()
    assert "database=ok" in rendered
    assert "migrations=ok" in rendered
    assert "static=ok" in rendered
    assert "bootstrap=ok" in rendered
    assert "idempotency_cleanup_command=ok" in rendered
    assert "operational_check=ok" in rendered


@pytest.mark.django_db
def test_operational_check_reports_static_failure(monkeypatch) -> None:
    import slaif_reservation.api.management.commands.operational_check as command_module

    monkeypatch.setattr(command_module, "missing_static_assets", lambda: ["web/site.css"])

    with pytest.raises(CommandError, match="operational check failed"):
        call_command("operational_check", stdout=StringIO(), stderr=StringIO())


@pytest.mark.django_db
def test_purge_expired_idempotency_records_dry_run_and_apply() -> None:
    owner = user()
    expired = idempotency_record(owner=owner, expires_at=timezone.now() - timedelta(hours=1))
    active = idempotency_record(owner=owner, expires_at=timezone.now() + timedelta(hours=1))

    dry_run_output = StringIO()
    call_command("purge_expired_idempotency_records", stdout=dry_run_output)

    assert "mode=dry-run" in dry_run_output.getvalue()
    assert "expired=1" in dry_run_output.getvalue()
    assert IdempotencyRecord.objects.filter(id=expired.id).exists()
    assert IdempotencyRecord.objects.filter(id=active.id).exists()

    apply_output = StringIO()
    call_command(
        "purge_expired_idempotency_records",
        "--apply",
        "--batch-size",
        "1",
        stdout=apply_output,
    )

    assert "mode=apply" in apply_output.getvalue()
    assert "deleted=1" in apply_output.getvalue()
    assert not IdempotencyRecord.objects.filter(id=expired.id).exists()
    assert IdempotencyRecord.objects.filter(id=active.id).exists()


def test_purge_expired_idempotency_records_rejects_invalid_batch_size() -> None:
    with pytest.raises(CommandError, match="batch_size must be at least 1"):
        call_command("purge_expired_idempotency_records", "--batch-size", "0", stdout=StringIO())


def test_backup_database_refuses_missing_database_url(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(CommandError, match="DATABASE_URL is required"):
        call_command(
            "backup_database",
            "--output",
            str(tmp_path / "backup.dump"),
            stdout=StringIO(),
        )


def test_backup_database_dry_run_does_not_print_password(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgres://slaif:super-secret-password@localhost:5432/slaif_reservation",
    )
    output = StringIO()

    call_command("backup_database", "--output", str(tmp_path / "backup.dump"), stdout=output)

    rendered = output.getvalue()
    assert "mode=dry-run" in rendered
    assert "validated=true" in rendered
    assert "super-secret-password" not in rendered


def test_restore_database_refuses_missing_database_url(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    artifact = tmp_path / "backup.dump"
    artifact.write_bytes(b"not-a-real-backup")

    with pytest.raises(CommandError, match="DATABASE_URL is required"):
        call_command("restore_database", "--input", str(artifact), stdout=StringIO())


def test_restore_database_dry_run_does_not_print_password(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgres://slaif:super-secret-password@localhost:5432/slaif_reservation",
    )
    artifact = tmp_path / "backup.dump"
    artifact.write_bytes(b"not-a-real-backup")
    output = StringIO()

    call_command("restore_database", "--input", str(artifact), stdout=output)

    rendered = output.getvalue()
    assert "mode=dry-run" in rendered
    assert "validated=true" in rendered
    assert "super-secret-password" not in rendered


@override_settings(
    LOGGING={
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"json": {"()": "slaif_reservation.config.logging.JsonLogFormatter"}},
        "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
        "root": {"handlers": ["console"], "level": "INFO"},
    }
)
def test_production_json_logging_configuration_loads(settings) -> None:
    assert settings.LOGGING["formatters"]["json"]["()"] == (
        "slaif_reservation.config.logging.JsonLogFormatter"
    )
