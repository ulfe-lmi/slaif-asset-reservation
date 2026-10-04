from __future__ import annotations

import ipaddress
import json
import logging
import os
import re
import socket
import subprocess
import uuid
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
    TrustedProxyForwardingMiddleware,
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

# ---- state helpers -------------------------------------------------------
# Container rows: cid|name|state|created|project|ports_json|service|volume
state_file="${SLAIF_FAKE_DOCKER_STATE:-}"
volume_file="${SLAIF_FAKE_DOCKER_VOLUMES:-${SLAIF_FAKE_DOCKER_LOG}.volumes}"

# The state file in effect right now: with ps phases, row lookups and
# creations follow the most recent ps invocation (same phase rule as the
# ps handler); before any ps call the base state applies.
current_state() {
  if [[ -n "${SLAIF_FAKE_DOCKER_PS_PHASES:-}" ]]; then
    count_file="${SLAIF_FAKE_DOCKER_PS_COUNT_FILE:-}"
    n=0
    if [[ -n "$count_file" && -f "$count_file" ]]; then
      n="$(cat "$count_file")"
    fi
    if [[ "$n" -gt 0 ]]; then
      IFS=':' read -r -a phases <<< "$SLAIF_FAKE_DOCKER_PS_PHASES"
      idx=$((n - 1))
      if (( idx >= ${#phases[@]} )); then
        idx=$(( ${#phases[@]} - 1 ))
      fi
      printf '%s' "${phases[$idx]}"
      return 0
    fi
  fi
  printf '%s' "$state_file"
}

find_row_in() {
  local file="$1" want="$2" by_name="$3"
  local f_cid f_name f_state f_created f_proj f_ports f_service f_volume
  [[ -n "$file" && -f "$file" ]] || return 1
  while IFS='|' read -r f_cid f_name f_state f_created f_proj f_ports f_service f_volume; do
    [[ -n "$f_cid" ]] || continue
    if [[ "$by_name" == "name" && "$f_name" == "$want" ]] \
      || [[ "$by_name" == "cid" && "$f_cid" == "$want" ]]; then
      printf '%s|%s|%s|%s|%s|%s|%s|%s\n' \
        "$f_cid" "$f_name" "$f_state" "$f_created" \
        "$f_proj" "$f_ports" "${f_service:-}" "${f_volume:-}"
      return 0
    fi
  done < "$file"
  return 1
}

find_row_by_name() {
  find_row_in "$(current_state)" "$1" "name"
}

find_row_by_cid() {
  find_row_in "$(current_state)" "$1" "cid"
}

add_row() {
  local file
  file="$(current_state)"
  [[ -n "$file" ]] || return 0
  printf '%s\n' "$1" >> "$file"
}

add_volume() {
  [[ -n "$volume_file" ]] || return 0
  if ! grep -qx "$1" "$volume_file" 2>/dev/null; then
    printf '%s\n' "$1" >> "$volume_file"
  fi
}

remove_project_rows() {
  local proj="$1" kept file f_cid f_name f_state f_created f_proj f_ports f_service f_volume
  file="$(current_state)"
  [[ -n "$file" && -f "$file" ]] || return 0
  kept="$(mktemp)"
  while IFS='|' read -r f_cid f_name f_state f_created f_proj f_ports f_service f_volume; do
    [[ -n "$f_cid" ]] || continue
    if [[ "$f_proj" != "$proj" ]]; then
      printf '%s|%s|%s|%s|%s|%s|%s|%s\n' \
        "$f_cid" "$f_name" "$f_state" "$f_created" \
        "$f_proj" "$f_ports" "${f_service:-}" "${f_volume:-}" >> "$kept"
    fi
  done < "$state_file"
  mv "$kept" "$state_file"
  if [[ -n "$volume_file" && -f "$volume_file" ]]; then
    kept="$(mktemp)"
    grep -v "^${proj}_" "$volume_file" > "$kept" || true
    mv "$kept" "$volume_file"
  fi
}

compose_project() {
  # last -p value in the current args
  local project="" prev=""
  for tok in $args; do
    if [[ "$prev" == "-p" ]]; then
      project="$tok"
    fi
    prev="$tok"
  done
  printf '%s' "$project"
}

created_at="2026-09-14 02:00:00 +0200 CEST"

# ---- dispatch ------------------------------------------------------------
if [[ "$args" == *"compose"* && "$args" == *"config"* && "$args" == *"--format json"* ]]; then
  port="${SLAIF_APP_HOST_PORT:-8000}"
  printf '%s' '{"services":{"app":{"ports":[{"host_ip":"127.0.0.1","published":"' \
    | tee "$SLAIF_FAKE_DOCKER_RENDERED_CONFIG"
  printf '%s' "$port" | tee -a "$SLAIF_FAKE_DOCKER_RENDERED_CONFIG"
  printf '%s\n' '","target":8000,"protocol":"tcp"}]}}}' \
    | tee -a "$SLAIF_FAKE_DOCKER_RENDERED_CONFIG"
  exit 0
fi

if [[ "$args" == *"compose"* && "$args" == *"up -d"* ]]; then
  set -- $args
  project=""
  svc=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -p)
        project="$2"
        shift 2
        ;;
      up)
        shift
        ;;
      -d)
        shift
        ;;
      db|app)
        svc="$1"
        shift
        ;;
      *)
        shift
        ;;
    esac
  done
  name="${project}-${svc}-1"
  # Creation race simulation: if the race file is armed for this service,
  # a foreign actor claims the name at create time and the create fails,
  # exactly like a real name conflict.
  race_file="${SLAIF_FAKE_DOCKER_RACE_FILE:-}"
  race_svc="${SLAIF_FAKE_DOCKER_RACE_SVC:-}"
  conflict="Error response from daemon: Conflict. The container name \"/%s\" is already in use"
  if [[ -n "$race_file" && -f "$race_file" && ( -z "$race_svc" || "$race_svc" == "$svc" ) ]]; then
    add_row "$(cat "$race_file")"
    printf "$conflict\n" "$name" >&2
    exit 1
  fi
  row="$(find_row_by_name "$name")" || true
  if [[ -n "$row" ]]; then
    printf "$conflict\n" "$name" >&2
    exit 1
  fi
  cid="faKE$(printf '%s' "$name" | cksum | cut -d' ' -f1)"
  volume=""
  ports='{}'
  if [[ "$svc" == "db" ]]; then
    volume="${project}_postgres-data"
    ports='{"5432/tcp": null}'
    add_volume "$volume"
  else
    ports='{"8000/tcp": null}'
  fi
  add_row "${cid}|${name}|running|${created_at}|${project}|${ports}|${svc}|${volume}"
  printf "%s|%s\n" "$cid" "$SLAIF_REHEARSAL_OWNER_NONCE" >> "${SLAIF_FAKE_DOCKER_LOG}.owners"
  exit 0
fi

if [[ "$args" == *"image inspect"* ]]; then
  printf '%s\n' "${SLAIF_FAKE_DOCKER_IMAGE_USER:-10001:10001}"
  exit 0
fi

if [[ "$args" == "ps -a --filter "* ]]; then
  local_state="$state_file"
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
    local_state="${phases[$idx]}"
  fi
  if [[ -n "$local_state" && -f "$local_state" ]]; then
    while IFS='|' read -r f_cid f_name f_state f_created f_proj f_ports f_service f_volume; do
      [[ -n "$f_cid" ]] || continue
      printf '%s|%s|%s|%s|%s\n' "$f_cid" "$f_name" "$f_state" "$f_created" "$f_proj"
    done < "$local_state"
  fi
  exit 0
fi

if [[ "$args" == "volume create "* ]]; then
  vol="${!#}"
  if ! grep -qx "$vol" "$volume_file" 2>/dev/null; then
    add_volume "$vol"
    printf '%s|%s\n' "$vol" "$SLAIF_REHEARSAL_OWNER_NONCE" >> "${volume_file}.owners"
  fi
  printf '%s\n' "$vol"
  exit 0
fi
if [[ "$args" == "volume inspect "* ]]; then
  raw="${args#volume inspect }"; vol="${raw%% --format*}"
  if ! grep -qx "$vol" "$volume_file" 2>/dev/null; then exit 1; fi
  case "$raw" in
    *".CreatedAt"*) printf '%s\n' "$created_at" ;;
    *"slaif.qualification.owner"*)
      grep "^${vol}|" "${volume_file}.owners" 2>/dev/null | cut -d'|' -f2
      ;;
  esac
  exit 0
fi
if [[ "$args" == "volume rm "* ]]; then
  vol="${!#}"; kept="$(mktemp)"
  grep -vx "$vol" "$volume_file" > "$kept" || true
  mv "$kept" "$volume_file"
  exit 0
fi
if [[ "$args" == "rm -f "* ]]; then
  target="${!#}"; kept="$(mktemp)"; current="$(current_state)"
  awk -F'|' -v id="$target" '$1 != id' "$current" > "$kept"
  mv "$kept" "$current"
  exit 0
fi

if [[ "$args" == *"down -v --remove-orphans"* ]]; then
  project="$(compose_project)"
  remove_project_rows "$project"
  exit 0
fi

if [[ "$args" == "run "* ]]; then
  # run_fail models a failing one-shot management command (the
  # `run --rm --network ... --env-file ...` shape), not the image
  # asset checks (`run --rm --entrypoint test ...`).
  if [[ -n "${SLAIF_FAKE_DOCKER_RUN_FAIL:-}" && "$args" == *"--network"* ]]; then
    exit 1
  fi
  exit 0
fi

# docker inspect <name-or-cid> --format <fmt>
if [[ "$args" == "inspect "* ]]; then
  # No word splitting: the --format template contains spaces and quotes.
  raw="${args#inspect }"
  if [[ "$raw" == *" --format "* ]]; then
    target="${raw%% --format*}"
    fmt="${raw#* --format }"
  else
    target="$raw"
    fmt=""
  fi
  row="$(find_row_by_name "$target" || find_row_by_cid "$target" || true)"
  if [[ -z "$row" ]]; then
    printf 'Error: No such object: %s\n' "$target" >&2
    exit 1
  fi
  IFS='|' read -r f_cid f_name f_state f_created f_proj f_ports f_service f_volume <<< "$row"
  if [[ -z "$fmt" ]]; then
    exit 0
  fi
  case "$fmt" in
    *"slaif.qualification.owner"*)
      grep "^${f_cid}|" "${SLAIF_FAKE_DOCKER_LOG}.owners" 2>/dev/null | cut -d'|' -f2
      ;;
    *".Id"*)
      printf '%s\n' "$f_cid"
      ;;
    *"compose.project"*)
      printf '%s\n' "$f_proj"
      ;;
    *"compose.service"*)
      printf '%s\n' "${f_service:-}"
      ;;
    *".Mounts"*)
      printf '%s' "${f_volume:-}"
      ;;
    *".State.Health"*)
      printf '%s\n' "healthy"
      ;;
    *"NetworkSettings.Ports"*)
      printf '%s\n' "$f_ports"
      ;;
    *)
      exit 0
      ;;
  esac
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
    volumes: list[str] | None = None,
    race_row: str | None = None,
    race_svc: str | None = None,
    run_fail: bool = False,
) -> dict[str, str]:
    """PATH-shimmed fake docker used by the rehearsal tests.

    Every invocation is appended to SLAIF_FAKE_DOCKER_LOG. With no extra state the
    fake only renders the Compose config, exactly as before. Optionally it can
    simulate a pre-existing container inventory for the recovery modes:

    - state_file: rows "cid|name|state|created|project|ports_json|service|volume";
      `docker ps -a --filter label=com.docker.compose.project` prints the first
      five fields, `docker inspect <name-or-cid> --format <fmt>` resolves rows by
      name first then cid, `docker inspect <name>` (no format) reports existence,
      `docker volume inspect` consults the volumes file, a compose `up -d <svc>`
      creates the project-scoped row (and the db volume) unless a name conflict
      or armed race says otherwise, and a compose `down -p <project>` removes
      exactly that project's rows and volumes.
    - ps_phases: per-`ps`-invocation state files (first invocation is the startup
      scan, second is the port precheck, later invocations reuse the last phase).
    - runtime_user: value `docker image inspect --format {{.Config.User}}` prints.
    - volumes: names pre-existing in the simulated volume inventory.
    - race_row/race_svc: when set, the next `compose up -d <race_svc>` first
      appends race_row (a foreign creator winning a name race) and then fails
      with a name conflict, like a real concurrent create.
    - run_fail: make `docker run` invocations fail (one-shot stop).
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
    if volumes is not None:
        volume_path = tmp_path / "fake-docker-volumes"
        volume_path.write_text("".join(name + "\n" for name in volumes), encoding="utf-8")
        env["SLAIF_FAKE_DOCKER_VOLUMES"] = str(volume_path)
    if race_row is not None:
        race_path = tmp_path / "fake-docker-race"
        race_path.write_text(race_row + "\n", encoding="utf-8")
        env["SLAIF_FAKE_DOCKER_RACE_FILE"] = str(race_path)
        env["SLAIF_FAKE_DOCKER_RACE_SVC"] = race_svc or ""
    if run_fail:
        env["SLAIF_FAKE_DOCKER_RUN_FAIL"] = "1"
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
    cid: str,
    name: str,
    state: str,
    created: str,
    project: str,
    ports_json: str,
    service: str = "",
    volume: str = "",
) -> str:
    return f"{cid}|{name}|{state}|{created}|{project}|{ports_json}|{service}|{volume}"


def _owned_app_row(host_port: int) -> str:
    return _container_row(
        "cafe00000001",
        f"{OWNED_PROJECT}-app-1",
        "running",
        REHEARSAL_CREATED_AT,
        OWNED_PROJECT,
        f'{{"8000/tcp": [{{"HostIp": "127.0.0.1", "HostPort": "{host_port}"}}]}}',
        service="app",
    )


def _owned_db_row() -> str:
    return _container_row(
        "cafe00000002",
        f"{OWNED_PROJECT}-db-1",
        "running",
        REHEARSAL_CREATED_AT,
        OWNED_PROJECT,
        '{"5432/tcp": null}',
        service="db",
        volume=f"{OWNED_PROJECT}_postgres-data",
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


RCE_TEST_PROJECT = "slaif-alpha-rehearsal-rctest"


def _run_full_rehearsal(tmp_path: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return _run_rehearsal([], env)


def test_rehearsal_snapshot_excludes_ignored_sentinels(tmp_path: Path) -> None:
    # Sentinels in git-ignored locations (owned by this test, refused if
    # pre-existing, removed exactly as created) must be proven absent from
    # the build snapshot. The fake docker stops the run at the first
    # one-shot management command; the snapshot proof is already logged.
    sentinel_dir = REPO_ROOT / "private_exports"
    sentinel = sentinel_dir / f"oap033b-snapshot-sentinel-{uuid.uuid4().hex[:12]}.txt"
    if sentinel_dir.exists() or sentinel.exists():
        pytest.skip("private_exports present in checkout; refusing to touch")
    port = _free_loopback_port()
    state = _write_state(tmp_path, "state", [])
    try:
        sentinel_dir.mkdir(parents=True)
        sentinel.write_text("sentinel-content-not-for-builds", encoding="utf-8")
        env = fake_docker(tmp_path, state_file=state, run_fail=True)
        env["SLAIF_REHEARSAL_PROJECT"] = RCE_TEST_PROJECT
        env["SLAIF_REHEARSAL_PORT"] = str(port)

        result = _run_full_rehearsal(tmp_path, env)

        assert result.returncode == 1, result.stderr  # stopped at the one-shot
        assert "snapshot-ignored-absent=private_exports" in result.stdout
        assert "snapshot-leak" not in result.stdout
        assert " up -d app" not in _docker_log(tmp_path)
        assert not REHEARSAL_ENV.exists()
        assert not REHEARSAL_PASSWORD.exists()
    finally:
        sentinel.unlink(missing_ok=True)
        if sentinel_dir.exists() and not any(sentinel_dir.iterdir()):
            sentinel_dir.rmdir()


def test_rehearsal_refuses_foreign_container_holding_owned_name(tmp_path: Path) -> None:
    # A foreign container already holding an expected owned name must be
    # refused before any create; it must be left untouched (sentinel row
    # intact) and no project-scoped down may run.
    foreign_db = _container_row(
        "beef00000009",
        f"{RCE_TEST_PROJECT}-db-1",
        "running",
        REHEARSAL_CREATED_AT,
        FOREIGN_PROJECT,
        '{"5432/tcp": null}',
        service="db",
    )
    state = _write_state(tmp_path, "state", [foreign_db])
    env = fake_docker(tmp_path, state_file=state)
    env["SLAIF_REHEARSAL_PROJECT"] = RCE_TEST_PROJECT
    env["SLAIF_REHEARSAL_PORT"] = str(_free_loopback_port())

    result = _run_full_rehearsal(tmp_path, env)

    assert result.returncode == 1
    assert "refusing to adopt" in result.stderr
    docker_log = _docker_log(tmp_path)
    assert " up -d" not in docker_log
    assert "down" not in docker_log
    assert state.read_text(encoding="utf-8") == foreign_db + "\n"
    assert not REHEARSAL_ENV.exists()
    assert not REHEARSAL_PASSWORD.exists()


def test_rehearsal_refuses_foreign_volume(tmp_path: Path) -> None:
    foreign_volume = f"{RCE_TEST_PROJECT}_postgres-data"
    state = _write_state(tmp_path, "state", [])
    env = fake_docker(tmp_path, state_file=state, volumes=[foreign_volume])
    env["SLAIF_REHEARSAL_PROJECT"] = RCE_TEST_PROJECT
    env["SLAIF_REHEARSAL_PORT"] = str(_free_loopback_port())

    result = _run_full_rehearsal(tmp_path, env)

    assert result.returncode == 1
    assert "refusing to adopt" in result.stderr
    docker_log = _docker_log(tmp_path)
    assert " up -d" not in docker_log
    assert "down" not in docker_log
    assert (tmp_path / "fake-docker-volumes").read_text(encoding="utf-8") == (foreign_volume + "\n")


def test_rehearsal_creation_race_leaves_foreign_untouched(tmp_path: Path) -> None:
    # The pre-creation check passes (name free), then a foreign creator
    # wins the name at create time: the failed create must exit non-zero
    # and leave the foreign resource untouched, with no project down.
    foreign_db = _container_row(
        "beef0000000a",
        f"{RCE_TEST_PROJECT}-db-1",
        "running",
        REHEARSAL_CREATED_AT,
        FOREIGN_PROJECT,
        '{"5432/tcp": null}',
        service="db",
    )
    state = _write_state(tmp_path, "state", [])
    env = fake_docker(tmp_path, state_file=state, race_row=foreign_db, race_svc="db")
    env["SLAIF_REHEARSAL_PROJECT"] = RCE_TEST_PROJECT
    env["SLAIF_REHEARSAL_PORT"] = str(_free_loopback_port())

    result = _run_full_rehearsal(tmp_path, env)

    assert result.returncode == 1
    assert "already in use" in result.stderr
    docker_log = _docker_log(tmp_path)
    assert " up -d db" in docker_log
    assert " up -d app" not in docker_log
    assert "down" not in docker_log
    # The foreign row is the only content: untouched, not adopted, not
    # removed by cleanup.
    assert state.read_text(encoding="utf-8") == foreign_db + "\n"
    assert not REHEARSAL_ENV.exists()
    assert not REHEARSAL_PASSWORD.exists()


def test_rehearsal_partial_create_failure_cleanup_removes_owned_only(
    tmp_path: Path,
) -> None:
    # db is created and verified owned, then a foreign creator claims the
    # app name at create time: the run fails, cleanup removes the owned db
    # container and project volume only, and the foreign app row survives.
    foreign_app = _container_row(
        "beef0000000b",
        f"{RCE_TEST_PROJECT}-app-1",
        "running",
        REHEARSAL_CREATED_AT,
        FOREIGN_PROJECT,
        '{"8000/tcp": null}',
        service="app",
    )
    state = _write_state(tmp_path, "state", [])
    env = fake_docker(
        tmp_path,
        state_file=state,
        volumes=[],
        race_row=foreign_app,
        race_svc="app",
    )
    env["SLAIF_REHEARSAL_PROJECT"] = RCE_TEST_PROJECT
    env["SLAIF_REHEARSAL_PORT"] = str(_free_loopback_port())

    result = _run_full_rehearsal(tmp_path, env)

    assert result.returncode == 1
    assert "app container create failed" in result.stderr
    docker_log = _docker_log(tmp_path)
    # The one-shot children ran with the explicit minimal synthetic env on
    # the project network - no `compose run`, no inherited host environment.
    assert f"run --rm --network {RCE_TEST_PROJECT}_default --env-file " in docker_log
    assert "compose run" not in docker_log
    # Cleanup targets verified immutable IDs, never a project-wide delete.
    assert "rm -f faKE" in docker_log
    assert f"volume rm {RCE_TEST_PROJECT}_postgres-data" in docker_log
    assert "down -v --remove-orphans" not in docker_log
    # Owned db container and project volume are gone; the foreign app row
    # (the untouched sentinel) is the only remaining state.
    assert state.read_text(encoding="utf-8") == foreign_app + "\n"
    assert (tmp_path / "fake-docker-volumes").read_text(encoding="utf-8") == ""
    assert not REHEARSAL_ENV.exists()
    assert not REHEARSAL_PASSWORD.exists()


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


@pytest.mark.parametrize(
    "message",
    [
        "Authorization: Bearer not-a-sar-token-but-still-secret",
        "Authorization: Basic YWJjOnNlY3JldC1wYXNzd29yZA==",
        "authorization=basic other-secret-value",
        "GET /api/ HTTP/1.1 authorization: bearer tail-secret",
    ],
)
def test_json_log_formatter_redacts_generic_bearer_and_basic(settings, message: str) -> None:
    # Regression: AUTHORIZATION_RE was broken by doubled backslashes and
    # never matched, so any Bearer/Basic value that is not a sar_ API
    # token passed straight through to the log line.
    settings.API_TOKEN_PEPPER = "test-pepper-value-that-must-not-log"
    record = logging.makeLogRecord(
        {
            "name": "slaif_reservation.test",
            "levelno": logging.INFO,
            "levelname": "INFO",
            "msg": message,
        }
    )
    rendered = JsonLogFormatter().format(record)
    for secret in (
        "not-a-sar-token-but-still-secret",
        "YWJjOnNlY3JldC1wYXNzd29yZA==",
        "other-secret-value",
        "tail-secret",
    ):
        assert secret not in rendered
    assert "[redacted]" in rendered


def test_request_log_carries_normalized_peer_for_untrusted_spoof(caplog) -> None:
    # Full middleware chain: the safe request log must carry the normalized
    # one-hop client identity (the peer, for an untrusted spoofing client),
    # never the spoofed X-Forwarded-For value.
    request = RequestFactory().get(
        "/health/live",
        REMOTE_ADDR="203.0.113.7",
        HTTP_X_FORWARDED_FOR="198.51.100.66",
        SERVER_NAME="reservation.example.test",
    )
    request.resolver_match = SimpleNamespace(route="health/live")  # noqa: S105

    def app(_request):
        from django.http import JsonResponse

        return JsonResponse({"ok": True})

    caplog.set_level(logging.INFO, logger="slaif_reservation.request")
    response = TrustedProxyForwardingMiddleware(SafeRequestLogMiddleware(app))(request)

    assert response.status_code == 200
    [record] = [item for item in caplog.records if item.name == "slaif_reservation.request"]
    assert record.client == "203.0.113.7"
    formatted = JsonLogFormatter().format(record)
    assert "198.51.100.66" not in formatted


@override_settings(TRUSTED_PROXY_PEERS=[ipaddress.ip_network("172.17.0.1")])
def test_request_log_carries_one_hop_client_for_trusted_proxy(caplog) -> None:
    # Trusted one-hop proxy: the log client is the normalized XFF value,
    # the original peer stays available only on request.remote_peer and is
    # never a log field.
    request = RequestFactory().get(
        "/health/live",
        REMOTE_ADDR="172.17.0.1",
        HTTP_X_FORWARDED_FOR="198.51.100.25",
        SERVER_NAME="reservation.example.test",
    )
    request.resolver_match = SimpleNamespace(route="health/live")  # noqa: S105

    def app(_request):
        from django.http import JsonResponse

        return JsonResponse({"ok": True})

    caplog.set_level(logging.INFO, logger="slaif_reservation.request")
    response = TrustedProxyForwardingMiddleware(SafeRequestLogMiddleware(app))(request)

    assert response.status_code == 200
    [record] = [item for item in caplog.records if item.name == "slaif_reservation.request"]
    assert record.client == "198.51.100.25"


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
