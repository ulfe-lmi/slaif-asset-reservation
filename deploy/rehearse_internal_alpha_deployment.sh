#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  cat <<'EOF'
Usage: deploy/rehearse_internal_alpha_deployment.sh [--config-only|--status|--cleanup-owned]

Runs a disposable internal-alpha deployment rehearsal using compose.production.example.yaml.

Modes:
  (no flag)      Full rehearsal: build the image, start disposable PostgreSQL and the
                 app, run smoke checks, then clean up. Refuses to start while
                 rehearsal-owned residue from a previously crashed or abandoned run
                 exists.
  --config-only  Create synthetic ignored production env files, render Compose config,
                 then clean up without building or starting containers.
  --status       Read-only: list rehearsal-owned Compose projects with their containers
                 (name, state, age). Never mutates Docker state.
  --cleanup-owned  Remove only rehearsal-owned Compose projects (scoped
                 down -v --remove-orphans per project), verify absence, and report
                 cleanup=ok. Destructive and explicit; its own mode, never part of a
                 full rehearsal run.

Rehearsal-owned means a Compose container whose com.docker.compose.project label starts
with slaif-alpha-rehearsal- (the default project name, and any SLAIF_REHEARSAL_PROJECT
value the script uses, always starts with that prefix). Foreign projects are never
touched, and the script never kills port occupants automatically.

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
tmp_dir=""
override_file=""
rendered_config_file=""
created_env=0
created_password=0
compose_started=0

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
  if [[ "$compose_started" == "1" ]]; then
    docker compose -f "$compose_file" -f "$override_file" -p "$project" down -v --remove-orphans >/dev/null 2>&1 || true
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
SLAIF_SECURE_SSL_REDIRECT=false
SLAIF_SECURE_HSTS_SECONDS=0
SLAIF_SECURE_HSTS_INCLUDE_SUBDOMAINS=false
SLAIF_SECURE_HSTS_PRELOAD=false
SLAIF_API_TOKEN_PEPPER=synthetic-rehearsal-api-token-pepper-not-for-deployment-32-bytes
SLAIF_API_TOKEN_MAX_LIFETIME_DAYS=90
DATABASE_URL=postgres://slaif:synthetic-rehearsal-postgres-password@db:5432/slaif_reservation
EOF
created_env=1
umask 022

cat > "$override_file" <<EOF
services:
  app:
    image: ${image}
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

log "building image"
docker build --tag "$image" .

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

log "starting disposable PostgreSQL"
compose up -d db
compose_started=1

log "applying migrations"
compose run --rm app python manage.py migrate --noinput

log "validating sanitized bootstrap import"
compose run --rm app python manage.py import_bootstrap_assets --input data/bootstrap/assets.yaml

log "running operational_check"
compose run --rm app python manage.py operational_check

log "validating OpenAPI"
compose run --rm app python manage.py spectacular --file /tmp/rehearsal-openapi.yaml --validate --fail-on-warn

port_precheck

log "starting application"
compose up -d app

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
