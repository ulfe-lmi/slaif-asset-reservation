#!/usr/bin/env bash
set -Eeuo pipefail

if [[ "${SLAIF_REHEARSAL_ENV_CLEANED:-}" != "1" ]]; then
  exec python3 - "$0" "$@" <<'PY'
import os
import sys
allowed = {"PATH", "TMPDIR", "SLAIF_REHEARSAL_PORT", "SLAIF_REHEARSAL_PROJECT",
           "SLAIF_REHEARSAL_IMAGE"}
env = {key: value for key, value in os.environ.items()
       if key in allowed or key.startswith("SLAIF_FAKE_DOCKER_")}
env["SLAIF_REHEARSAL_ENV_CLEANED"] = "1"
env["DOCKER_HOST"] = "unix:///var/run/docker.sock"
os.execve("/bin/bash", ["bash", *sys.argv[1:]], env)
PY
fi

usage() {
  cat <<'EOF'
Usage: deploy/rehearse_internal_alpha_deployment.sh [--config-only|--status|--cleanup-owned]

Runs a disposable internal-alpha deployment rehearsal using compose.production.example.yaml.

Modes:
  (no flag)      Full rehearsal: build the image from a tracked-file snapshot,
                 start disposable PostgreSQL and the app, run smoke checks,
                 then clean up. Refuses to start while rehearsal-owned
                 residue from a previously crashed or abandoned run exists.
  --config-only  Create synthetic ignored production env files, render Compose
                 config, then clean up without building or starting containers.
  --status       Read-only: list rehearsal-owned Compose projects with their
                 containers (name, state, age). Never mutates Docker state.
  --cleanup-owned  Remove only rehearsal-owned Compose projects (scoped
                 down -v --remove-orphans per project), verify absence, and
                 report cleanup=ok. Destructive and explicit; its own mode,
                 never part of a full rehearsal run.

Ownership contract (SAR-031):
- The image is built from a SNAPSHOT of tracked files (plus an explicit,
  empty-by-default untracked allowlist), never from the live checkout:
  ignored valuable files (.env, deploy/secrets, private exports, role data,
  local SQLite/statics) must not enter the build context even if a
  .dockerignore entry is later removed. The snapshot step proves, for every
  sensitive path that is both git-ignored and present in the checkout, that
  it is absent from the snapshot (snapshot-ignored-absent=... lines).
- Expected container/volume names are pre-checked BEFORE any create: an
  existing resource with an expected name is a refusal, never an adoption.
  Volumes are explicitly created and nonce-verified before PostgreSQL can
  mount them. Containers and networks carry the same per-run nonce.
  Automatic cleanup uses verified IDs and volume creation identity; it
  never deletes a resource merely because its name matches the project.
- Every one-shot child process (migrate/seed/check) runs with an EXPLICIT
  minimal synthetic environment via `docker run --env-file` on the project
  network: no host environment, no inherited SLAIF settings, no PG* client
  credentials, and only the rehearsal's own database.
- Rehearsal-owned means a Compose container whose com.docker.compose.project
  label starts with slaif-alpha-rehearsal- (the default project name, and any
  SLAIF_REHEARSAL_PROJECT value the script uses, always starts with that
  prefix). Foreign projects are never touched, and the script never kills
  port occupants automatically.

Environment overrides:
  SLAIF_REHEARSAL_PORT       Host port for the temporary app, default 18080.
  SLAIF_REHEARSAL_PROJECT    Compose project name, default includes the process id.
                             Keep the slaif-alpha-rehearsal- prefix so residue stays
                             discoverable by --status and removable by --cleanup-owned.
  SLAIF_REHEARSAL_IMAGE      Image tag, default slaif-asset-reservation:internal-alpha.

The script writes only ignored temporary deployment files under deploy/ and a mktemp directory.
It refuses to run if deploy/env.production or deploy/secrets/postgres_password already exists.
EOF
}

mode="full"
case "${1:-}" in
  "")
    ;;
  "--config-only")
    mode="config-only"
    ;;
  "--status")
    mode="status"
    ;;
  "--cleanup-owned")
    mode="cleanup-owned"
    ;;
  "-h" | "--help")
    usage
    exit 0
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

compose_file="$repo_root/compose.production.example.yaml"
deploy_dir="$repo_root/deploy"
env_file="$deploy_dir/env.production"
secrets_dir="$deploy_dir/secrets"
password_file="$secrets_dir/postgres_password"
project_prefix="slaif-alpha-rehearsal-"
project="${SLAIF_REHEARSAL_PROJECT:-${project_prefix}$$}"
port="${SLAIF_REHEARSAL_PORT:-18080}"
image="${SLAIF_REHEARSAL_IMAGE:-slaif-asset-reservation:internal-alpha}"
# Explicit allowlist of untracked files copied into the build snapshot.
# Intentionally EMPTY: every build input (Dockerfile, pyproject.toml,
# uv.lock, manage.py, src/, data/bootstrap/, .dockerignore) is tracked.
snapshot_allowlist=()
# Sensitive relative paths that must never enter the build snapshot. Only
# paths that are git-ignored AND present in the checkout are asserted.
sensitive_paths=(
  .env
  deploy/env.production
  deploy/secrets
  private_exports
  legacy_exports
  smartscheduling_exports
  migration_artifacts/private
  oap/leases
  oap/tmp
  backups
  db.sqlite3
  staticfiles
  instance
  local_settings.py
  .venv
)
tmp_dir=""
override_file=""
rendered_config_file=""
snapshot_dir=""
created_env=0
created_password=0
compose_started=0
db_cid=""
db_volume=""
app_cid=""
run_owner="$(python3 -c 'import secrets; print(secrets.token_hex(16))')"
export SLAIF_REHEARSAL_OWNER_NONCE="$run_owner"
volume_created=""
network_id=""
resources_started=0

log() {
  printf 'rehearsal: %s\n' "$1"
}

die() {
  printf 'rehearsal: %s\n' "$1" >&2
  exit 1
}

compose() {
  docker compose -f "$compose_file" -f "$override_file" -p "$project" "$@"
}

cleanup() {
  local status=$?
  if [[ "$resources_started" == "1" ]]; then
  # Recover partially created IDs, but never adopt a name alone.
  for name in "${project}-app-1" "${project}-db-1"; do
    identity="$(docker inspect "$name" --format '{{.Id}}' 2>/dev/null || true)"
    if [[ -n "$identity" ]] && \
       [[ "$(docker inspect "$identity" --format '{{index .Config.Labels "slaif.qualification.owner"}}' 2>/dev/null)" == "$run_owner" ]]; then
      docker rm -f "$identity" >/dev/null 2>&1 || status=1
    fi
  done
  if [[ -n "$volume_created" ]] && \
     [[ "$(docker volume inspect "$db_volume" --format '{{.CreatedAt}}' 2>/dev/null)" == "$volume_created" ]] && \
     [[ "$(docker volume inspect "$db_volume" --format '{{index .Labels "slaif.qualification.owner"}}' 2>/dev/null)" == "$run_owner" ]]; then
    docker volume rm "$db_volume" >/dev/null 2>&1 || status=1
  fi
  identity="$(docker network inspect "${project}_default" --format '{{.Id}}' 2>/dev/null || true)"
  if [[ -n "$identity" ]] && \
     [[ "$(docker network inspect "$identity" --format '{{index .Labels "slaif.qualification.owner"}}' 2>/dev/null)" == "$run_owner" ]]; then
    docker network rm "$identity" >/dev/null 2>&1 || status=1
  fi
  if [[ "$compose_started" == "1" ]]; then
    for identity in "$db_cid" "$app_cid"; do
      if [[ -n "$identity" ]] && docker inspect "$identity" >/dev/null 2>&1; then
        log "cleanup=incomplete container=$identity still present"
        status=1
      fi
    done
    if [[ -n "$db_volume" ]] && docker volume inspect "$db_volume" >/dev/null 2>&1; then
      log "cleanup=incomplete volume=$db_volume still present"
      status=1
    fi
  fi
  fi
  if [[ "$created_env" == "1" ]]; then
    rm -f "$env_file"
  fi
  if [[ "$created_password" == "1" ]]; then
    rm -f "$password_file"
    rmdir "$secrets_dir" >/dev/null 2>&1 || true
  fi
  if [[ -n "$tmp_dir" ]]; then
    rm -rf "$tmp_dir"
  fi
  exit "$status"
}
trap cleanup EXIT

# Rehearsal-owned residue helpers. A Compose container is rehearsal-owned iff its
# com.docker.compose.project label starts with $project_prefix; the default project
# name and any SLAIF_REHEARSAL_PROJECT value the script uses always do. A foreign
# project that merely contains the substring elsewhere is not owned.

list_compose_containers() {
  docker ps -a \
    --filter "label=com.docker.compose.project" \
    --format '{{.ID}}|{{.Names}}|{{.State}}|{{.CreatedAt}}|{{.Label "com.docker.compose.project"}}'
}

scan_owned_projects() {
  # Print rehearsal-owned Compose project names, one per line (may repeat per container).
  local ps_out line cid name state created proj
  ps_out="$(list_compose_containers)" \
    || die "docker ps failed; cannot enumerate rehearsal-owned containers"
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    IFS='|' read -r cid name state created proj <<< "$line"
    if [[ "$proj" == "${project_prefix}"* ]]; then
      printf '%s\n' "$proj"
    fi
  done <<< "$ps_out"
}

container_age() {
  python3 - "$1" <<'PY'
from datetime import datetime, timezone
import sys

raw = sys.argv[1].strip()
parsed = None
for fmt in (
    "%Y-%m-%d %H:%M:%S %z %Z",
    "%Y-%m-%d %H:%M:%S %z",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S%z",
):
    try:
        parsed = datetime.strptime(raw, fmt)
        break
    except ValueError:
        continue
if parsed is None:
    print("unknown")
    raise SystemExit(0)
if parsed.tzinfo is None:
    parsed = parsed.replace(tzinfo=timezone.utc)
age = max(0, int((datetime.now(timezone.utc) - parsed).total_seconds()))
days, rem = divmod(age, 86400)
hours, rem = divmod(rem, 3600)
minutes, seconds = divmod(rem, 60)
if days:
    print(f"{days}d{hours}h")
elif hours:
    print(f"{hours}h{minutes}m")
elif minutes:
    print(f"{minutes}m{seconds}s")
else:
    print(f"{seconds}s")
PY
}

status_mode() {
  local ps_out line cid name state created proj found=0
  ps_out="$(list_compose_containers)" \
    || die "docker ps failed; cannot enumerate rehearsal-owned containers"
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    IFS='|' read -r cid name state created proj <<< "$line"
    if [[ "$proj" != "${project_prefix}"* ]]; then
      continue
    fi
    found=1
    printf 'rehearsal: owned project=%s container=%s state=%s age=%s\n' \
      "$proj" "$name" "$state" "$(container_age "$created")"
  done <<< "$ps_out"
  if [[ "$found" == "1" ]]; then
    printf 'rehearsal: residue=found remove=deploy/rehearse_internal_alpha_deployment.sh --cleanup-owned\n'
  else
    printf 'rehearsal: no rehearsal-owned projects found\n'
  fi
  exit 0
}

cleanup_owned_mode() {
  local projects project after
  projects="$(scan_owned_projects | sort -u)"
  if [[ -z "$projects" ]]; then
    printf 'rehearsal: no rehearsal-owned projects found\n'
    exit 0
  fi
  while IFS= read -r project; do
    [[ -n "$project" ]] || continue
    log "removing owned project=$project"
    docker compose -f "$compose_file" -p "$project" down -v --remove-orphans \
      || die "removing rehearsal-owned project $project failed"
    log "removed owned project=$project"
  done <<< "$projects"
  after="$(scan_owned_projects | sort -u)"
  if [[ -n "$after" ]]; then
    {
      printf 'rehearsal: cleanup=incomplete residue remains:\n'
      printf '%s\n' "$after" | sed 's/^/rehearsal:   project=/'
    } >&2
    exit 1
  fi
  printf 'rehearsal: cleanup=ok\n'
  exit 0
}

startup_residue_scan() {
  local projects
  projects="$(scan_owned_projects | sort -u)"
  if [[ -z "$projects" ]]; then
    return 0
  fi
  {
    printf 'rehearsal: rehearsal-owned residue from a previous crashed or abandoned run:\n'
    printf '%s\n' "$projects" | sed 's/^/rehearsal:   project=/'
    printf 'rehearsal: refusing to start; remove the residue first with:\n'
    printf 'rehearsal:   deploy/rehearse_internal_alpha_deployment.sh --cleanup-owned\n'
  } >&2
  exit 1
}

port_publishes_host_port() {
  python3 - "$1" "$2" <<'PY'
import json
import sys

try:
    ports = json.loads(sys.argv[1] or "null")
except ValueError:
    ports = None
if not isinstance(ports, dict):
    raise SystemExit(1)
for binding in ports.values():
    if not isinstance(binding, list):
        continue
    for item in binding:
        if isinstance(item, dict) and str(item.get("HostPort", "")) == sys.argv[2]:
            raise SystemExit(0)
raise SystemExit(1)
PY
}

port_precheck() {
  local occupied ps_out line cid name state created proj ports
  occupied="$(python3 - "$port" <<'PY'
import socket
import sys

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sock.bind(("127.0.0.1", int(sys.argv[1])))
except OSError:
    print("occupied")
else:
    print("free")
finally:
    sock.close()
PY
)" || die "port precheck for SLAIF_REHEARSAL_PORT=$port failed"
  if [[ "$occupied" == "free" ]]; then
    return 0
  fi
  ps_out="$(list_compose_containers)" \
    || die "docker ps failed during port precheck"
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    IFS='|' read -r cid name state created proj <<< "$line"
    if [[ "$proj" != "${project_prefix}"* ]]; then
      continue
    fi
    ports="$(docker inspect "$cid" --format '{{json .NetworkSettings.Ports}}')" \
      || continue
    if port_publishes_host_port "$ports" "$port"; then
      die "host port $port is occupied by rehearsal-owned container $name (project $proj); remove it with: deploy/rehearse_internal_alpha_deployment.sh --cleanup-owned"
    fi
  done <<< "$ps_out"
  die "host port $port is in use by a non-rehearsal process; choose another SLAIF_REHEARSAL_PORT"
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "$1 is required on PATH"
}

require_command docker
require_command curl
require_command python3
require_command git

[[ -f "$compose_file" ]] || die "compose.production.example.yaml is missing"
[[ -d "$deploy_dir" ]] || die "deploy directory is missing"
[[ "$repo_root" != "/" ]] || die "refusing to run with filesystem root as repository root"

if [[ "$mode" == "status" ]]; then
  status_mode
fi
if [[ "$mode" == "cleanup-owned" ]]; then
  cleanup_owned_mode
fi

[[ ! -e "$env_file" ]] || die "deploy/env.production already exists; refusing to overwrite a real deployment env file"
[[ ! -e "$password_file" ]] || die "deploy/secrets/postgres_password already exists; refusing to overwrite a real secret file"
[[ "$port" =~ ^[0-9]+$ ]] || die "SLAIF_REHEARSAL_PORT must be a TCP port number"
export SLAIF_APP_HOST_PORT="$port"

tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/slaif-alpha-rehearsal.XXXXXX")"
override_file="$tmp_dir/compose.override.yaml"
rendered_config_file="$tmp_dir/rendered-compose.json"
snapshot_dir="$tmp_dir/snapshot"

mkdir -p "$secrets_dir"
umask 077
cat > "$password_file" <<'EOF'
synthetic-rehearsal-postgres-password
EOF
created_password=1
cat > "$env_file" <<'EOF'
DJANGO_SETTINGS_MODULE=slaif_reservation.config.settings.production
SLAIF_DJANGO_SECRET_KEY=synthetic-rehearsal-secret-key-not-for-deployment-32-bytes
SLAIF_ALLOWED_HOSTS=127.0.0.1,localhost
SLAIF_CSRF_TRUSTED_ORIGINS=http://127.0.0.1,http://localhost
SLAIF_ENABLE_API_DOCS=false
SLAIF_PUBLIC_API_DOCS=false
# Deliberate plain-loopback rehearsal choice, explicitly OUTSIDE the
# supported Internet deployment shape: this synthetic deployment has no
# TLS-terminating proxy, so the redirect is off and the origins are http.
# A real service deployment (deploy/env.production) keeps the redirect on
# with https origins and the explicit trusted proxy peers. This is a
# documented rehearsal exception, never a production bypass.
SLAIF_SECURE_SSL_REDIRECT=false
SLAIF_SECURE_HSTS_SECONDS=0
SLAIF_SECURE_HSTS_INCLUDE_SUBDOMAINS=false
SLAIF_SECURE_HSTS_PRELOAD=false
SLAIF_API_TOKEN_PEPPER=synthetic-rehearsal-api-token-pepper-not-for-deployment-32-bytes
SLAIF_API_TOKEN_MAX_LIFETIME_DAYS=90
# In-container healthcheck peer only; the rehearsal smoke probes arrive
# from the host via the Docker bridge gateway and are treated as direct
# (untrusted) clients, which is exactly the contract under test.
SLAIF_TRUSTED_PROXY_PEERS=127.0.0.1
DATABASE_URL=postgres://slaif:synthetic-rehearsal-postgres-password@db:5432/slaif_reservation
EOF
created_env=1
umask 022

cat > "$override_file" <<EOF
services:
  db:
    labels:
      slaif.qualification.owner: "$run_owner"
  app:
    image: ${image}
    labels:
      slaif.qualification.owner: "$run_owner"
networks:
  default:
    labels:
      slaif.qualification.owner: "$run_owner"
EOF

log "rendering production Compose config with synthetic env"
compose config >/dev/null
compose config --format json > "$rendered_config_file"
python3 - "$rendered_config_file" "$port" <<'PY'
from __future__ import annotations

import json
import sys

config_path, expected_port = sys.argv[1:3]
with open(config_path, encoding="utf-8") as handle:
    config = json.load(handle)

ports = config["services"]["app"].get("ports", [])
matches = []
extra_base_bindings = []
for item in ports:
    if not isinstance(item, dict):
        continue
    target = str(item.get("target", ""))
    published = str(item.get("published", ""))
    host_ip = str(item.get("host_ip", ""))
    if target == "8000" and published == expected_port and host_ip == "127.0.0.1":
        matches.append(item)
    if expected_port != "8000" and target == "8000" and published == "8000" and host_ip == "127.0.0.1":
        extra_base_bindings.append(item)

if len(matches) != 1 or extra_base_bindings:
    raise SystemExit("rehearsal Compose config does not publish exactly the requested app port")
PY

if [[ "$mode" == "config-only" ]]; then
  log "config-only=ok"
  exit 0
fi

# ---------------------------------------------------------------------------
# Build snapshot: tracked files + explicit (empty) untracked allowlist.
# Never cp -a the live checkout: ignored valuable files must not enter the
# build context even if a .dockerignore entry is later removed.
# ---------------------------------------------------------------------------
log "creating tracked-file build snapshot"
mkdir -p "$snapshot_dir"
git ls-files -z | while IFS= read -r -d '' tracked_path; do
  dest="$snapshot_dir/$tracked_path"
  mkdir -p "$(dirname "$dest")"
  cp -Pp "$tracked_path" "$dest"
done
for allow_path in "${snapshot_allowlist[@]}"; do
  [[ -e "$allow_path" ]] || die "snapshot allowlist entry is missing: $allow_path"
  dest="$snapshot_dir/$allow_path"
  mkdir -p "$(dirname "$dest")"
  cp -p "$allow_path" "$dest"
done
# Prove that git-ignored sensitive paths present in the checkout did not
# enter the snapshot.
for sensitive in "${sensitive_paths[@]}"; do
  if git check-ignore -q -- "$sensitive" 2>/dev/null && [[ -e "$repo_root/$sensitive" ]]; then
    if [[ -e "$snapshot_dir/$sensitive" ]]; then
      die "snapshot-leak-$sensitive"
    fi
    log "snapshot-ignored-absent=$sensitive"
  fi
done

log "building image from snapshot"
docker build --tag "$image" "$snapshot_dir"

runtime_user="$(docker image inspect "$image" --format '{{.Config.User}}')"
[[ "$runtime_user" == "10001:10001" ]] || die "runtime user is not 10001:10001"
log "runtime_user=10001:10001"

docker run --rm --entrypoint test "$image" -f /app/staticfiles/web/site.css
docker run --rm --entrypoint test "$image" -f /app/staticfiles/admin/css/base.css
docker run --rm --entrypoint test "$image" -f /app/staticfiles/drf_spectacular_sidecar/swagger-ui-dist/swagger-ui-bundle.js
docker run --rm --entrypoint test "$image" -f /app/data/bootstrap/assets.yaml
docker run --rm --entrypoint test "$image" -f /app/data/bootstrap/assets.schema.json
log "image_assets=ok"

startup_residue_scan

# ---------------------------------------------------------------------------
# Pre-creation collision checks. A resource already holding an expected
# name is foreign (or abandoned residue) and is refused, never adopted.
# Note: this check alone is NOT proof of exclusive ownership (a concurrent
# creator could win after it); ownership is established by the
# post-creation identity verification below.
# ---------------------------------------------------------------------------
expected_db_name="${project}-db-1"
expected_app_name="${project}-app-1"
expected_volume_name="${project}_postgres-data"
if docker inspect "$expected_db_name" >/dev/null 2>&1; then
  die "pre-existing resource holds expected db container name $expected_db_name; refusing to adopt it"
fi
if docker inspect "$expected_app_name" >/dev/null 2>&1; then
  die "pre-existing resource holds expected app container name $expected_app_name; refusing to adopt it"
fi
if docker volume inspect "$expected_volume_name" >/dev/null 2>&1; then
  die "pre-existing resource holds expected volume name $expected_volume_name; refusing to adopt it"
fi
log "pre-creation checks clean (db=$expected_db_name app=$expected_app_name volume=$expected_volume_name)"
db_volume="$expected_volume_name"
resources_started=1
docker volume create --label "slaif.qualification.owner=$run_owner" "$db_volume" >/dev/null \
  || die "owned volume creation failed"
[[ "$(docker volume inspect "$db_volume" --format '{{index .Labels "slaif.qualification.owner"}}')" == "$run_owner" ]] \
  || die "foreign volume won the creation race; refusing to adopt it"
volume_created="$(docker volume inspect "$db_volume" --format '{{.CreatedAt}}')"
cat >> "$override_file" <<EOF
volumes:
  postgres-data:
    external: true
    name: "$db_volume"
EOF

verify_container_identity() {
  # $1 = expected name, $2 = expected service; echoes the verified container
  # ID. Fails (returns 1) unless the resource exists AND carries this
  # project's compose labels - the only basis on which this run may later
  # delete it.
  local name="$1" service="$2" cid proj_label svc_label
  if ! cid="$(docker inspect "$name" --format '{{.Id}}' 2>/dev/null)"; then
    return 1
  fi
  proj_label="$(docker inspect "$cid" --format '{{index .Config.Labels "com.docker.compose.project"}}')"
  svc_label="$(docker inspect "$cid" --format '{{index .Config.Labels "com.docker.compose.service"}}')"
  if [[ "$proj_label" != "$project" || "$svc_label" != "$service" ]] || \
     [[ "$(docker inspect "$cid" --format '{{index .Config.Labels "slaif.qualification.owner"}}')" != "$run_owner" ]]; then
    return 1
  fi
  printf '%s' "$cid"
}

log "starting disposable PostgreSQL"
compose up -d db
compose_started=1

db_cid="$(verify_container_identity "$expected_db_name" "db")" \
  || die "db container identity verification failed (name exists without this project's labels)"
log "db-verified cid=${db_cid:0:12}"

db_volume="$(docker inspect "$db_cid" --format '{{range .Mounts}}{{if eq .Type "volume"}}{{.Name}}{{end}}{{end}}')"
[[ -n "$db_volume" ]] || die "db container has no named volume mount"
[[ "$db_volume" == "${project}_"* ]] || die "db volume $db_volume is not project-scoped"
log "db-volume-verified=$db_volume"

wait_for_db_healthy() {
  local status i
  for i in $(seq 1 90); do
    status="$(docker inspect "$db_cid" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}starting{{end}}')"
    if [[ "$status" == "healthy" ]]; then
      return 0
    fi
    if [[ "$status" == "unhealthy" ]]; then
      return 1
    fi
    sleep 1
  done
  return 1
}
wait_for_db_healthy || die "db did not become healthy"
log "db-healthy"

# One-shot children: explicit minimal synthetic environment, project
# network, this run's own database. The host environment (SLAIF settings,
# PG* client credentials, anything else) is never passed.
run_one_shot() {
  local args=("$@")
  docker run --rm \
    --network "${project}_default" \
    --env-file "$env_file" \
    "$image" python manage.py "${args[@]}"
}

log "applying migrations"
run_one_shot migrate --noinput

log "validating sanitized bootstrap import"
run_one_shot import_bootstrap_assets --input data/bootstrap/assets.yaml

log "running operational_check"
run_one_shot operational_check

log "validating OpenAPI"
run_one_shot spectacular --file /tmp/rehearsal-openapi.yaml --validate --fail-on-warn

port_precheck

log "starting application"
if ! compose up -d app; then
  die "app container create failed; a foreign resource may hold the expected name - foreign resources are left untouched"
fi

app_cid="$(verify_container_identity "$expected_app_name" "app")" \
  || die "app container identity verification failed (name exists without this project's labels)"
log "app-verified cid=${app_cid:0:12}"

wait_for_http() {
  local url="$1"
  local expected="$2"
  local attempts=60
  local status
  for _ in $(seq 1 "$attempts"); do
    status="$(curl --silent --output /dev/null --write-out '%{http_code}' "$url" || true)"
    if [[ "$status" == "$expected" ]]; then
      return 0
    fi
    sleep 1
  done
  die "$url did not return HTTP $expected"
}

wait_for_http "http://127.0.0.1:${port}/health/live" "200"
wait_for_http "http://127.0.0.1:${port}/health/ready" "200"
wait_for_http "http://127.0.0.1:${port}/login/" "200"
log "health_and_login=ok"

manage_status="$(curl --silent --output /dev/null --write-out '%{http_code}' "http://127.0.0.1:${port}/manage/")"
[[ "$manage_status" == "302" || "$manage_status" == "303" ]] || die "anonymous /manage/ did not redirect safely"
log "anonymous_manage_redirect=ok"

api_response="$tmp_dir/api-me.json"
api_status="$(curl --silent --output "$api_response" --write-out '%{http_code}' "http://127.0.0.1:${port}/api/v1/me/")"
[[ "$api_status" == "401" ]] || die "unauthenticated /api/v1/me/ did not return 401"
grep -q '"code"[[:space:]]*:[[:space:]]*"authentication_required"' "$api_response" || die "unauthenticated /api/v1/me/ did not return safe problem details"
log "api_auth_failure=ok"

log "rehearsal=ok"
