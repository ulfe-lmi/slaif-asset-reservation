#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  cat <<'EOF'
Usage: deploy/rehearse_internal_alpha_deployment.sh [--config-only]

Runs a disposable internal-alpha deployment rehearsal using compose.production.example.yaml.

Modes:
  --config-only  Create synthetic ignored production env files, render Compose config,
                 then clean up without building or starting containers.

Environment overrides:
  SLAIF_REHEARSAL_PORT       Host port for the temporary app, default 18080.
  SLAIF_REHEARSAL_PROJECT    Compose project name, default includes the process id.
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
project="${SLAIF_REHEARSAL_PROJECT:-slaif-alpha-rehearsal-$$}"
port="${SLAIF_REHEARSAL_PORT:-18080}"
image="${SLAIF_REHEARSAL_IMAGE:-slaif-asset-reservation:internal-alpha}"
tmp_dir=""
override_file=""
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

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "$1 is required on PATH"
}

require_command docker
require_command curl

[[ -f "$compose_file" ]] || die "compose.production.example.yaml is missing"
[[ -d "$deploy_dir" ]] || die "deploy directory is missing"
[[ "$repo_root" != "/" ]] || die "refusing to run with filesystem root as repository root"
[[ ! -e "$env_file" ]] || die "deploy/env.production already exists; refusing to overwrite a real deployment env file"
[[ ! -e "$password_file" ]] || die "deploy/secrets/postgres_password already exists; refusing to overwrite a real secret file"
[[ "$port" =~ ^[0-9]+$ ]] || die "SLAIF_REHEARSAL_PORT must be a TCP port number"

tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/slaif-alpha-rehearsal.XXXXXX")"
override_file="$tmp_dir/compose.override.yaml"

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
    ports:
      - "127.0.0.1:${port}:8000"
EOF

log "rendering production Compose config with synthetic env"
compose config >/dev/null

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
