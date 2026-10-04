#!/usr/bin/env bash
# Real-HTTPS trust-boundary qualification (OAP 033-b) — the ACTUAL supported
# operator path, end to end:
#
#   real TLS Caddy (host, pinned v2.11.6) -> loopback-published non-root
#   production image (Docker) -> private PostgreSQL 17 (Docker), with the
#   bridge gateway explicitly discovered and configured as the /32 trusted
#   proxy peer (one of the two possible original peers behind the
#   published port, depending on host NAT mode - loopback or bridge
#   gateway; both are trusted).
#
# The Caddy configuration is DERIVED from the shipped deploy/Caddyfile.
# example by explicit narrow substitutions only (harness-only certificate,
# site address, loopback listen, short read_header/idle windows, proxy
# target); every substituted or preserved value is asserted against the
# actual adapted JSON. The shipped read_body_idle pair (30s window /
# 1024-byte/second min-rate) is exercised exactly as shipped.
#
# Ownership contract (SAR-031, 033-a safety recovery + 033-b criterion 2):
# - Every file, process, container and volume belongs to THIS run: a fresh
#   mktemp work directory, an image built from a tracked-file SNAPSHOT
#   (never cp -a of the checkout), a uniquely named Compose project
#   (default: slaif033b-boundary-$$-<hex>; SLAIF033B_BOUNDARY_PROJECT only
#   for tests), and a uniquely tagged image. Existing resources are never
#   adopted, terminated, dropped or migrated: a name collision is a
#   refusal, not an adoption, and ownership of a created resource is
#   re-verified from its compose labels AFTER creation, so a failed create
#   leaves a foreign resource untouched.
# - Nothing is inherited: DATABASE_URL/TEST_DATABASE_URL and the
#   repository .env are never loaded. Every migration/seed/check one-shot
#   runs via `docker run --env-file` with an explicit minimal synthetic
#   environment on the project network - no host environment, no PG*
#   client credentials, only this run's own database.
# - Secret material (database/user passwords, secret keys, peppers) is
#   generated into 0600 work files or carried in 0600 env files, never
#   printed and never placed on a command line.
# - Bounded process sessions: Caddy runs in its own session under a shell
#   leader; cleanup terminates the whole process group even when the
#   leader has already exited first, then audits /proc for orphans carrying
#   the work-directory marker.
# - No public DNS, no ACME, no OS trust-store changes: a 1-day synthetic
#   certificate for slaif-boundary.test, trusted only per-client.
#
# Exit codes:
# - 0: all checks passed (prints https-boundary=ok)
# - 1: a check failed, prerequisites collided, or cleanup was incomplete
# - 42: prerequisites not met (Caddy unavailable or not v2.11.6, or
#   openssl/curl/docker/python3 missing) - callers may skip
#
# Environment overrides:
#   SLAIF033B_BOUNDARY_CADDY     Path to the pinned Caddy binary
#                                (default: caddy on PATH).
#   SLAIF033B_BOUNDARY_PROJECT   Fixed Compose project name (test-only;
#                                keeps cleanup discoverable).
#   SLAIF033B_BOUNDARY_DB_PASSWORD  Sentinel database password (test-only;
#                                written to a 0600 file, never printed).
#   SLAIF033B_BOUNDARY_SLOW_APP_UP_S  Seconds to sleep before `compose up
#                                -d app` (test-only dial for creation-race
#                                injection; never set by an operator).
#   SLAIF033B_BOUNDARY_FAULT    Test-only failure injection:
#                                after-edge-up     fail right after the edge
#                                                  is ready (cleanup audit);
#                                kill-caddy-leader SIGKILL the Caddy session
#                                                  leader, then fail (the
#                                                  orphaned child must still
#                                                  be cleaned by group).
set -Eeuo pipefail

# Re-exec once with an allowlisted environment. Host database/client and
# Docker-context configuration must never reach any qualification child.
if [ "${1:-}" != "--owned-environment" ]; then
  exec python3 - "$0" <<'PY'
import os
import sys
allowed = {"PATH", "TMPDIR", "SLAIF033B_BOUNDARY_CADDY", "SLAIF033B_BOUNDARY_PROJECT",
           "SLAIF033B_BOUNDARY_DB_PASSWORD", "SLAIF033B_BOUNDARY_SLOW_APP_UP_S",
           "SLAIF033B_BOUNDARY_SLOW_VOLUME_CREATE_S", "SLAIF033B_BOUNDARY_FAULT"}
env = {key: value for key, value in os.environ.items() if key in allowed}
env["DOCKER_HOST"] = "unix:///var/run/docker.sock"
os.execve("/bin/bash", ["bash", sys.argv[1], "--owned-environment"], env)
PY
fi

# Never inherit product database or settings configuration.
unset DATABASE_URL TEST_DATABASE_URL DJANGO_SETTINGS_MODULE SLAIF_TRUSTED_PROXY_PEERS 2>/dev/null || true

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

CADDY_VERSION="v2.11.6"
HOSTNAME_SYNTHETIC="slaif-boundary.test"
# Harness-only deadline substitutions (explicit, narrow, each asserted
# against the adapted JSON): the read_header window is shortened 60s -> 5s
# and the keep-alive idle 5m -> 10s so those deadlines are exercised within
# a bounded budget. The shipped read_body_idle pair (30s window, 524288
# min-rate ~ 17.5 KiB/s floor) and the shipped transport/buffer/cap values
# are kept exactly as shipped.
READ_HEADER_TIMEOUT_S=5
IDLE_TIMEOUT_S=10

work=""
project=""
image_tag=""
app_port=""
caddy_port=""
caddy_leader=""
total_leader=""
gateway=""
db_cid=""
app_cid=""
dead_cid=""
db_volume=""
env_file=""
dead_env_file=""
password_file=""
work_marker=""
cleanup_incomplete=0
image_built=0
dead_created=0
run_owner=""
network_id=""
volume_created=""
image_id=""
owned_probe_sessions=()

log() {
  printf 'https-boundary: %s\n' "$1"
}

fail() {
  printf 'https-boundary=FAIL check=%s\n' "$1" >&2
  exit 1
}

skip() {
  printf 'https-boundary=SKIP check=%s\n' "$1" >&2
  exit 42
}

ok() {
  printf 'https-boundary=%s=ok\n' "$1"
}

free_port() {
  python3 - <<'PY'
import socket

s = socket.socket()
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()
PY
}

kill_session() {
  # Bounded terminate/kill/reap of an owned session ($1 = leader pid).
  # The leader may already be dead while children survive (the case this
  # run's kill-caddy-leader fault injection proves): the process GROUP is
  # signalled for as long as any member is alive, so surviving children
  # are never skipped by a dead-leader early return.
  local pid="$1" i
  [ -n "$pid" ] || return 0
  if kill -0 -- "-$pid" 2>/dev/null; then
    kill -TERM -- "-$pid" 2>/dev/null || true
    for i in $(seq 1 24); do
      kill -0 -- "-$pid" 2>/dev/null || break
      sleep 0.5
    done
    if kill -0 -- "-$pid" 2>/dev/null; then
      kill -KILL -- "-$pid" 2>/dev/null || true
      sleep 0.5
    fi
  fi
  wait "$pid" 2>/dev/null || true
}

orphan_scan() {
  # $1 = marker (owned work-directory path). Print the pid of any live
  # process whose cmdline carries the marker, one per line.
  local marker="$1" d pid
  for d in /proc/[0-9]*; do
    pid="${d#/proc/}"
    [ "$pid" = "$$" ] && continue
    if ( tr '\0' ' ' <"$d/cmdline" ) 2>/dev/null | grep -qF -- "$marker"; then
      printf '%s\n' "$pid"
    fi
  done
  return 0
}

await_app_log() {
  # Bounded (~10 s) poll of the owned app container's MERGED log stream
  # (stdout+stderr): the application's safe request log and the Gunicorn
  # access/error logs are all emitted on the container's STDERR, so
  # capturing stdout alone would make every log assertion vacuous.
  # $1 = fixed string that must appear in a log line; the captured
  # snapshot is printed on success.
  local needle="$1" i logs
  for i in $(seq 1 40); do
    logs="$(docker logs "$app_cid" 2>&1)"
    if printf '%s\n' "$logs" | grep -qF -- "$needle"; then
      printf '%s\n' "$logs"
      return 0
    fi
    sleep 0.25
  done
  return 1
}

cleanup() {
  local status=$?
  set +u
  kill_session "$caddy_leader"
  kill_session "$total_leader"
  for identity in "${owned_probe_sessions[@]}"; do
    kill_session "$identity"
  done
  if [ -z "$network_id" ] && [ -n "$run_owner" ]; then
    identity="$(docker network inspect "${project}_default" --format '{{.Id}}' 2>/dev/null || true)"
    if [ -n "$identity" ] && \
       [ "$(docker network inspect "$identity" --format '{{index .Labels "slaif.qualification.owner"}}' 2>/dev/null)" = "$run_owner" ]; then
      network_id="$identity"
    fi
  fi
  # The dead-DB container is attached to the project network but is NOT a
  # compose member: remove it before `compose down` so the project network
  # can be removed cleanly.
  # Never `compose down -v`: even a failed creation can leave a foreign
  # resource under the same project/name. Delete only nonce-labelled IDs.
  for name in "${project}-app-1" "${project}-db-1" "${project}-appdead-1"; do
    identity="$(docker inspect "$name" --format '{{.Id}}' 2>/dev/null || true)"
    if [ -n "$identity" ] && [ -n "$run_owner" ] && \
       [ "$(docker inspect "$identity" --format '{{index .Config.Labels "slaif.qualification.owner"}}' 2>/dev/null)" = "$run_owner" ]; then
      docker rm -f "$identity" >/dev/null 2>&1 || cleanup_incomplete=1
    fi
  done
  if [ -n "$network_id" ] && \
     [ "$(docker network inspect "$network_id" --format '{{index .Labels "slaif.qualification.owner"}}' 2>/dev/null)" = "$run_owner" ]; then
    docker network rm "$network_id" >/dev/null 2>&1 || cleanup_incomplete=1
  fi
  if [ -n "$volume_created" ] && \
     [ "$(docker volume inspect "$db_volume" --format '{{.CreatedAt}}' 2>/dev/null)" = "$volume_created" ] && \
     [ "$(docker volume inspect "$db_volume" --format '{{index .Labels "slaif.qualification.owner"}}' 2>/dev/null)" = "$run_owner" ]; then
    docker volume rm "$db_volume" >/dev/null 2>&1 || cleanup_incomplete=1
  fi
  if [ -n "$image_id" ] && \
     [ "$(docker image inspect "$image_id" --format '{{index .Config.Labels "slaif.qualification.owner"}}' 2>/dev/null)" = "$run_owner" ]; then
    docker rmi "$image_id" >/dev/null 2>&1 || cleanup_incomplete=1
  fi
  if [ -n "$work" ]; then
    rm -rf "$work"
  fi
  # Identity-verified residue audit: only names THIS run owns are checked.
  if [ -n "$project" ]; then
    for identity in "$db_cid" "$app_cid" "$dead_cid"; do
      if [ -n "$identity" ] && docker inspect "$identity" >/dev/null 2>&1; then
        log "cleanup=incomplete container=$identity still present"
        cleanup_incomplete=1
      fi
    done
    if [ -n "$volume_created" ] && docker volume inspect "$db_volume" >/dev/null 2>&1; then
      log "cleanup=incomplete volume=$db_volume still present"
      cleanup_incomplete=1
    fi
    if [ "$image_built" = "1" ] && docker image inspect "$image_tag" >/dev/null 2>&1; then
      log "cleanup=incomplete image=$image_tag still present"
      cleanup_incomplete=1
    fi
    if [ -n "$work_marker" ]; then
      local orphans
      orphans="$(orphan_scan "$work_marker")"
      if [ -n "$orphans" ]; then
        log "cleanup=incomplete orphans=${orphans//$'\n'/,} (work-path marker)"
        cleanup_incomplete=1
      fi
    fi
  fi
  if [ "$cleanup_incomplete" = "1" ]; then
    status=1
  fi
  exit "$status"
}
trap cleanup EXIT

# ---------------------------------------------------------------------------
# Prerequisites (exit 42 => caller may skip)
# ---------------------------------------------------------------------------
caddy_bin="${SLAIF033B_BOUNDARY_CADDY:-$(command -v caddy || true)}"
if [ -z "$caddy_bin" ]; then
  skip "caddy-missing"
fi
caddy_version_out="$("$caddy_bin" version | head -n 1)"
case "$caddy_version_out" in
  "$CADDY_VERSION"*) ;;
  *) skip "caddy-version-mismatch" ;;
esac
command -v openssl >/dev/null 2>&1 || skip "openssl-missing"
command -v curl >/dev/null 2>&1 || skip "curl-missing"
command -v docker >/dev/null 2>&1 || skip "docker-missing"
# A docker CLI without a reachable daemon (for example CI runners) is the
# same as a missing tool: honest 42, never a fake pass or a build failure.
docker info >/dev/null 2>&1 || skip "docker-daemon-unavailable"
command -v python3 >/dev/null 2>&1 || skip "python3-missing"
[[ -f "$repo_root/deploy/Caddyfile.example" ]] || fail "shipped-caddyfile-missing"
[[ -f "$repo_root/compose.production.example.yaml" ]] || fail "compose-example-missing"

rand_hex="$(openssl rand -hex 4)"
run_owner="$(openssl rand -hex 16)"
project="${SLAIF033B_BOUNDARY_PROJECT:-slaif033b-boundary-$$-${rand_hex}}"
image_tag="slaif033b-boundary-${project}-app"
work="$(mktemp -d "${TMPDIR:-/tmp}/slaif033b-boundary.XXXXXX")" || fail "workdir"
work_marker="$work"
chmod 700 "$work"
umask 077
log "work=$work"
log "project=$project"
log "image=$image_tag"

# ---------------------------------------------------------------------------
# Synthetic short-lived certificate (owned, private to this run)
# ---------------------------------------------------------------------------
openssl req -x509 -newkey rsa:2048 -sha256 -nodes -days 1 \
  -keyout "$work/key.pem" -out "$work/cert.pem" \
  -subj "/CN=${HOSTNAME_SYNTHETIC}" \
  -addext "subjectAltName=DNS:${HOSTNAME_SYNTHETIC}" >/dev/null 2>&1 \
  || fail "cert-gen"

# ---------------------------------------------------------------------------
# Synthetic secrets (0600 work files; never printed, never on argv)
# ---------------------------------------------------------------------------
password_file="$work/pg_password"
if [ -n "${SLAIF033B_BOUNDARY_DB_PASSWORD:-}" ]; then
  printf '%s' "$SLAIF033B_BOUNDARY_DB_PASSWORD" >"$password_file"
else
  openssl rand -base64 48 | tr -d '=+/\n' | head -c 32 >"$password_file"
fi
chmod 600 "$password_file"

# ---------------------------------------------------------------------------
# Pre-creation collision checks. A resource already holding an expected
# name is foreign (or abandoned residue) and is refused, never adopted.
# Note: this check alone is NOT proof of exclusive ownership (a concurrent
# creator could win after it); ownership of what we create is established
# by the post-creation label verification below.
# ---------------------------------------------------------------------------
for expected in "${project}-app-1" "${project}-db-1" "${project}-appdead-1"; do
  if docker inspect "$expected" >/dev/null 2>&1; then
    fail "refusing-to-adopt-container-$expected"
  fi
done
if docker volume inspect "${project}_postgres-data" >/dev/null 2>&1; then
  fail "refusing-to-adopt-volume-${project}_postgres-data"
fi
docker image inspect "$image_tag" >/dev/null 2>&1 && fail "refusing-to-adopt-image"
docker network inspect "${project}_default" >/dev/null 2>&1 && fail "refusing-to-adopt-network"
log "pre-creation checks clean"

# ---------------------------------------------------------------------------
# Build snapshot: tracked files + explicit (empty) untracked allowlist.
# Never cp -a the live checkout: ignored valuable files (.env, deploy
# secrets, private exports, role data) must not enter the build context
# even if a .dockerignore entry is later removed.
# ---------------------------------------------------------------------------
log "creating tracked-file build snapshot"
snapshot_dir="$work/snapshot"
mkdir -p "$snapshot_dir"
git -C "$repo_root" ls-files -z | while IFS= read -r -d '' tracked_path; do
  dest="$snapshot_dir/$tracked_path"
  mkdir -p "$(dirname "$dest")"
  cp -Pp "$repo_root/$tracked_path" "$dest"
done
# Prove that git-ignored sensitive paths present in the checkout did not
# enter the snapshot.
for sensitive in .env deploy/env.production deploy/secrets private_exports \
  legacy_exports smartscheduling_exports migration_artifacts/private \
  oap/leases oap/tmp backups db.sqlite3 staticfiles instance local_settings.py \
  .venv; do
  if git -C "$repo_root" check-ignore -q -- "$sensitive" 2>/dev/null \
    && [[ -e "$repo_root/$sensitive" ]]; then
    if [[ -e "$snapshot_dir/$sensitive" ]]; then
      fail "snapshot-leak-$sensitive"
    fi
    log "snapshot-ignored-absent=$sensitive"
  fi
done

log "building image from snapshot"
docker build --label "slaif.qualification.owner=$run_owner" --tag "$image_tag" "$snapshot_dir" >/dev/null 2>&1 \
  || fail "image-build"
image_built=1
image_id="$(docker image inspect "$image_tag" --format '{{.Id}}')"
runtime_user="$(docker image inspect "$image_tag" --format '{{.Config.User}}')"
[[ "$runtime_user" == "10001:10001" ]] || fail "runtime-user"
for asset in /app/staticfiles/web/site.css /app/staticfiles/admin/css/base.css \
  /app/staticfiles/drf_spectacular_sidecar/swagger-ui-dist/swagger-ui-bundle.js \
  /app/data/bootstrap/assets.yaml /app/data/bootstrap/assets.schema.json; do
  docker run --rm --entrypoint test "$image_tag" -f "$asset" >/dev/null 2>&1 \
    || fail "image-asset-missing"
done
log "image=ok user=10001:10001"

# ---------------------------------------------------------------------------
# Owned copy of the production Compose file (only the app image tag is
# substituted; everything else - db pin, healthchecks, command, read_only,
# user, tmpfs, loopback publish - is the shipped contract).
# ---------------------------------------------------------------------------
compose_dir="$work/compose-dir"
mkdir -p "$compose_dir/deploy/secrets"
python3 - "$repo_root/compose.production.example.yaml" "$compose_dir/compose.yaml" "$image_tag" <<'PY'
import sys

src, dst, tag = sys.argv[1:4]
text = open(src, encoding="utf-8").read()
needle = "    image: slaif-asset-reservation:internal-alpha"
assert text.count(needle) == 1, "app image line not found exactly once"
open(dst, "w", encoding="utf-8").write(text.replace(needle, f"    image: {tag}"))
PY
compose_yaml="$compose_dir/compose.yaml"
db_volume="${project}_postgres-data"
if [ -n "${SLAIF033B_BOUNDARY_SLOW_VOLUME_CREATE_S:-}" ]; then
  log "volume-create-window"
  sleep "$SLAIF033B_BOUNDARY_SLOW_VOLUME_CREATE_S"
fi
docker volume create --label "slaif.qualification.owner=$run_owner" "$db_volume" >/dev/null \
  || fail "volume-create"
[ "$(docker volume inspect "$db_volume" --format '{{index .Labels "slaif.qualification.owner"}}')" = "$run_owner" ] \
  || fail "refusing-to-adopt-raced-volume"
volume_created="$(docker volume inspect "$db_volume" --format '{{.CreatedAt}}')"
cat >"$compose_dir/owned.yaml" <<YAML
services:
  db:
    labels:
      slaif.qualification.owner: "$run_owner"
  app:
    labels:
      slaif.qualification.owner: "$run_owner"
volumes:
  postgres-data:
    external: true
    name: "$db_volume"
networks:
  default:
    labels:
      slaif.qualification.owner: "$run_owner"
YAML

# The db secret bind in the shipped compose file is relative to the compose
# file directory: provide the owned synthetic password at that path.
cp "$password_file" "$compose_dir/deploy/secrets/postgres_password"
chmod 600 "$compose_dir/deploy/secrets/postgres_password"

# ---------------------------------------------------------------------------
# Start owned PostgreSQL; discover the actual bridge gateway /32 peer.
# ---------------------------------------------------------------------------
compose() {
  docker compose -f "$compose_yaml" -f "$compose_dir/owned.yaml" -p "$project" "$@"
}

compose up -d db >/dev/null 2>&1 || fail "db-create"
network_id="$(docker network inspect "${project}_default" --format '{{.Id}}')"

verify_container_identity() {
  # $1 = expected name, $2 = expected service; echoes the verified
  # container ID. Fails unless the resource exists AND carries this
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

db_cid="$(verify_container_identity "${project}-db-1" "db")" \
  || fail "db-identity"
log "db-verified cid=${db_cid:0:12}"
db_volume="$(docker inspect "$db_cid" --format '{{range .Mounts}}{{if eq .Type "volume"}}{{.Name}}{{end}}{{end}}')"
[[ -n "$db_volume" ]] || fail "db-volume-missing"
[[ "$db_volume" == "${project}_"* ]] || fail "db-volume-not-project-scoped"
log "db-volume-verified=$db_volume"

gateway="$(docker network inspect "${project}_default" \
  --format '{{range .IPAM.Config}}{{.Gateway}}{{end}}')"
[[ -n "$gateway" ]] || fail "gateway-discovery"
case "$gateway" in
  *:*) gateway_cidr="${gateway}/128" ;;
  *) gateway_cidr="${gateway}/32" ;;
esac
log "gateway=$gateway_cidr"

db_ready=0
for _ in $(seq 1 90); do
  if docker exec "$db_cid" pg_isready -U slaif -d slaif_reservation >/dev/null 2>&1; then
    db_ready=1
    break
  fi
  sleep 1
done
[ "$db_ready" = "1" ] || fail "db-ready"
log "db-healthy"

# ---------------------------------------------------------------------------
# Explicit minimal synthetic environment for the app and every one-shot
# (0600 file; the only environment any child process sees). The CSRF
# origin is the legitimate origin INCLUDING the fixture Caddy port - the
# origin a real browser would present.
# ---------------------------------------------------------------------------
app_port="$(free_port)" || fail "app-port"
caddy_port="$(free_port)" || fail "caddy-port"
export SLAIF_APP_HOST_PORT="$app_port"
openssl rand -base64 48 | tr -d '=+/\n' | head -c 48 >"$work/django_secret_key"
openssl rand -base64 48 | tr -d '=+/\n' | head -c 48 >"$work/token_pepper"
openssl rand -base64 24 | tr -d '=+/\n' | head -c 24 >"$work/user_password"
chmod 600 "$work/django_secret_key" "$work/token_pepper" "$work/user_password"
# The owned compose file resolves ./deploy/env.production relative to the
# compose directory; write the synthetic env there (the one-shots use the
# same file).
env_file="$compose_dir/deploy/env.production"
work="$work" python3 - "$work" "$env_file" <<PY
import os
import sys

work, env_path = sys.argv[1:3]
db_password = open(os.path.join(work, "pg_password")).read()
values = {
    "DJANGO_SETTINGS_MODULE": "slaif_reservation.config.settings.production",
    "SLAIF_DJANGO_SECRET_KEY": open(os.path.join(work, "django_secret_key")).read(),
    "SLAIF_ALLOWED_HOSTS": "${HOSTNAME_SYNTHETIC},127.0.0.1",
    "SLAIF_CSRF_TRUSTED_ORIGINS": "https://${HOSTNAME_SYNTHETIC}:${caddy_port}",
    "SLAIF_ENABLE_API_DOCS": "false",
    "SLAIF_PUBLIC_API_DOCS": "false",
    "SLAIF_SECURE_SSL_REDIRECT": "true",
    "SLAIF_SECURE_HSTS_SECONDS": "0",
    "SLAIF_API_TOKEN_PEPPER": open(os.path.join(work, "token_pepper")).read(),
    "SLAIF_API_TOKEN_MAX_LIFETIME_DAYS": "90",
    "SLAIF_TRUSTED_PROXY_PEERS": "127.0.0.1,${gateway_cidr}",
    "DATABASE_URL": "postgres://slaif:" + db_password + "@db:5432/slaif_reservation",
    "BOUNDARY_USER_EMAIL": "boundary033b@example.test",
    "BOUNDARY_USER_PASSWORD": open(os.path.join(work, "user_password")).read(),
}
with open(env_path, "w", encoding="utf-8") as fh:
    for key, value in values.items():
        fh.write(f"{key}={value}\n")
os.chmod(env_path, 0o600)
PY
chmod 600 "$env_file"
log "synthetic-env=ok app-port=$app_port caddy-port=$caddy_port"

# The dead-DB variant of the same explicit environment: identical except
# the database points at a closed loopback port inside the container.
dead_env_file="$work/env.dead"
python3 - "$env_file" "$dead_env_file" <<'PY'
import sys

src, dst = sys.argv[1:3]
lines = open(src, encoding="utf-8").read().splitlines()
out = []
for line in lines:
    if line.startswith("DATABASE_URL="):
        line = "DATABASE_URL=postgres://slaif:dead@127.0.0.1:1/slaif_reservation"
    out.append(line)
open(dst, "w", encoding="utf-8").write("\n".join(out) + "\n")
PY
chmod 600 "$dead_env_file"

# ---------------------------------------------------------------------------
# One-shot children: explicit minimal synthetic environment (the 0600 env
# file), project network, this run's own database. The host environment is
# never passed: no `compose run`, no inherited SLAIF settings, no PG*
# client credentials.
# ---------------------------------------------------------------------------
run_one_shot() {
  docker run --rm \
    --network "${project}_default" \
    --env-file "$env_file" \
    "$image_tag" python manage.py "$@" >/dev/null
}

run_one_shot migrate --noinput || fail "db-migrate"
log "migrations=ok"
run_one_shot import_bootstrap_assets --input data/bootstrap/assets.yaml \
  || fail "bootstrap-import"
log "bootstrap-import=ok"
run_one_shot operational_check || fail "operational-check"
log "operational-check=ok"
run_one_shot spectacular --file /tmp/rehearsal-openapi.yaml --validate --fail-on-warn \
  || fail "openapi-validate"
log "openapi=ok"
run_one_shot shell -c '
import os

from django.contrib.auth import get_user_model

User = get_user_model()
User.objects.create_user(
    email=os.environ["BOUNDARY_USER_EMAIL"],
    password=os.environ["BOUNDARY_USER_PASSWORD"],
)
' || fail "user-create"
log "user-created"

# ---------------------------------------------------------------------------
# Start the production app container (shipped command/healthcheck intact).
# ---------------------------------------------------------------------------
# Test-only dial (never set by an operator): widens the creation window so
# a race-injection test can claim the app name between our pre-creation
# check and our create attempt.
if [ -n "${SLAIF033B_BOUNDARY_SLOW_APP_UP_S:-}" ]; then
  sleep "${SLAIF033B_BOUNDARY_SLOW_APP_UP_S}"
fi
if ! compose up -d app >/dev/null 2>&1; then
  # A foreign resource may hold the expected name; it is left untouched.
  fail "app-create-refused"
fi
app_cid="$(verify_container_identity "${project}-app-1" "app")" \
  || fail "app-identity"
log "app-verified cid=${app_cid:0:12}"

app_healthy=0
for _ in $(seq 1 240); do
  status="$(docker inspect "$app_cid" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}starting{{end}}')"
  case "$status" in
    healthy) app_healthy=1; break ;;
    unhealthy) break ;;
  esac
  sleep 1
done
[ "$app_healthy" = "1" ] || fail "app-ready"
log "app-healthy"

# ---------------------------------------------------------------------------
# Caddy edge: derive the configuration from the SHIPPED example with
# explicit narrow substitutions, adapt, assert the adapted JSON carries
# exactly the shipped (or declared harness-substituted) values, then run.
# ---------------------------------------------------------------------------
derive_caddyfile() {
  # $1 = input shipped Caddyfile, $2 = output, $3 = caddy port,
  # $4 = app port, $5 = cert, $6 = key.
  # Each substitution below is the ONLY delta from the shipped file:
  #   1. drop `email` (no ACME: auto_https off, explicit certificate)
  #   2. add global `admin off` / `auto_https off`
  #   3. site address -> synthetic host on the harness Caddy port + tls
  #   4. read_header window 60s -> 5s (harness: exercise the deadline)
  #   5. idle keep-alive 5m -> 10s (harness: exercise the deadline)
  #   6. reverse_proxy upstream -> the run's loopback-published app port
  # Everything else - the server timeouts pair (30s/1024), write_idle,
  # transport timeouts, keepalive 3s, request_buffers 1MB, request_body
  # max_size 10MB, the header block (deferred Referrer-Policy default,
  # -Server, -Via, nosniff), encode - is the shipped contract, verbatim.
  python3 - "$1" "$2" "$3" "$4" "$5" "$6" "$READ_HEADER_TIMEOUT_S" \
    "$IDLE_TIMEOUT_S" <<'PY'
import sys

src, dst, caddy_port, app_port, cert, key = sys.argv[1:7]
read_header_s, idle_s = sys.argv[7:9]
text = open(src, encoding="utf-8").read()
anchor = "{\n\temail admin@example.org\n"
assert text.count(anchor) == 1, "global Caddy block must be unique"
text = text.replace(anchor, "{\n\tadmin off\n\tauto_https off\n\temail admin@example.org\n")
subs = [
    ("\temail admin@example.org\n", ""),
    (
        "reservation.example.org {",
        f"slaif-boundary.test:{caddy_port} {{\n\ttls {cert} {key}",
    ),
    ("\t\t\tread_header 60s\n", f"\t\t\tread_header {read_header_s}s\n"),
    ("\t\t\tidle 5m\n", f"\t\t\tidle {idle_s}s\n"),
    ("reverse_proxy 127.0.0.1:8000 {", f"reverse_proxy 127.0.0.1:{app_port} {{"),
]
for old, new in subs:
    assert text.count(old) == 1, f"substitution anchor not unique: {old!r}"
    text = text.replace(old, new)
open(dst, "w", encoding="utf-8").write(text)
PY
}
derive_caddyfile "$repo_root/deploy/Caddyfile.example" "$work/Caddyfile" \
  "$caddy_port" "$app_port" "$work/cert.pem" "$work/key.pem" \
  || fail "caddyfile-derive"

"$caddy_bin" adapt --config "$work/Caddyfile" >"$work/adapted.json" \
  2>"$work/adapt-warnings.log" || fail "caddy-adapt"

if ! python3 - "$work/adapted.json" "$work/caddy.json" "$caddy_port" "$app_port" \
  "$READ_HEADER_TIMEOUT_S" "$IDLE_TIMEOUT_S" <<'PY'
import json
import sys

raw_path, out_path, caddy_port, app_port, rht_s, idle_s = sys.argv[1:7]
raw = open(raw_path, encoding="utf-8").read()
decoder = json.JSONDecoder()
docs = []
i = 0
while i < len(raw):
    while i < len(raw) and raw[i] in " \t\r\n":
        i += 1
    if i >= len(raw):
        break
    obj, j = decoder.raw_decode(raw, i)
    docs.append(obj)
    i = j
http_docs = [d for d in docs if "http" in d.get("apps", {})]
assert http_docs, "no http app in adapted Caddy config"
doc = http_docs[0]
servers = doc["apps"]["http"]["servers"]
assert len(servers) == 1, "expected exactly one server"
server = next(iter(servers.values()))
# Harness-substituted values (declared in derive_caddyfile):
assert server["listen"] == [f":{caddy_port}"], "harness listen substitution"
server["listen"] = [f"127.0.0.1:{caddy_port}"]
assert server["read_header_timeout"] == int(rht_s) * 10**9, "read_header window"
assert server["idle_timeout"] == int(idle_s) * 10**9, "idle window"
assert server["automatic_https"] == {"disable": True}, "auto_https must be off"
# Shipped values, verbatim:
assert server["read_idle_timeout"] == 30 * 10**9, "shipped read_body_idle window"
assert server["read_min_rate"] == 1024, "shipped read_body_idle min-rate"
assert server["read_timeout"] == 60 * 10**9, "shipped total body-read deadline"
assert server["write_idle_timeout"] == 30 * 10**9, "shipped write_idle"
# No ACME and no admin listener; the all_handlers() walk below proves no
# access log directive exists anywhere in the adapted config.
assert "admin" not in doc.get("apps", {}), "admin app must be off"
assert "acme" not in doc.get("apps", {}), "acme app must be absent"
routes = server["routes"]
assert len(routes) == 1
match = routes[0]["match"]
assert {"host": ["slaif-boundary.test"]} in match, "site host match"
sub = routes[0]["handle"][0]
assert sub["handler"] == "subroute"
handlers = {h.get("handler"): h for h in sub["routes"][0]["handle"]}
headers = [h for h in sub["routes"][0]["handle"] if h.get("handler") == "headers"]
assert len(headers) == 2, "expected exactly two headers handlers"
static_headers, deferred_headers = None, None
for h in headers:
    resp = h.get("response", {})
    if "require" in resp:
        deferred_headers = resp
    else:
        static_headers = resp
assert static_headers, "static headers handler missing"
assert sorted(static_headers.get("delete", [])) == ["Server", "Via"], "server/via removal"
assert static_headers.get("set", {}).get("X-Content-Type-Options") == ["nosniff"], "nosniff"
assert deferred_headers.get("require", {}).get("headers", {}).get("Referrer-Policy") is None, (
    "deferred referrer-policy default must only apply when absent"
)
assert deferred_headers.get("set", {}).get("Referrer-Policy") == [
    "strict-origin-when-cross-origin"
], "shipped deferred referrer-policy default"
body = handlers.get("request_body")
assert body and body.get("max_size") == 10000000, "shipped request_body cap (10MB)"
encode = handlers.get("encode")
assert encode and set(encode.get("encodings", {})) == {"gzip", "zstd"}, "shipped encodings"
proxy = handlers.get("reverse_proxy")
assert proxy, "reverse_proxy handler missing"
assert proxy.get("request_buffers") == 1000000, "shipped request buffer bound (1MB)"
up = proxy.get("headers", {}).get("request", {}).get("set", {})
assert up.get("X-Forwarded-For") == ["{http.request.remote.host}"], "one-hop XFF overwrite"
assert up.get("X-Forwarded-Proto") == ["{http.request.scheme}"], "one-hop XFP overwrite"
transport = proxy.get("transport", {})
assert transport.get("dial_timeout") == 10 * 10**9, "shipped dial_timeout"
assert transport.get("response_header_timeout") == 30 * 10**9, "shipped response_header_timeout"
assert transport.get("read_timeout") == 60 * 10**9, "shipped read_timeout"
assert transport.get("write_timeout") == 60 * 10**9, "shipped write_timeout"
assert transport.get("keep_alive", {}).get("idle_timeout") == 3 * 10**9, (
    "shipped upstream keepalive (below Gunicorn --keep-alive 5)"
)
upstreams = proxy.get("upstreams", [])
assert [u.get("dial") for u in upstreams] == [f"127.0.0.1:{app_port}"], "proxy target"


def all_handlers(node):
    if isinstance(node, dict):
        if node.get("handler") == "log":
            raise SystemExit("an access log directive exists in the adapted config")
        for value in node.values():
            all_handlers(value)
    elif isinstance(node, list):
        for value in node:
            all_handlers(value)


all_handlers(doc)
json.dump(doc, open(out_path, "w", encoding="utf-8"))
PY
then
  fail "caddy-config-assert"
fi

"$caddy_bin" validate --config "$work/caddy.json" >/dev/null 2>&1 \
  || fail "caddy-validate"

XDG_DATA_HOME="$work/caddy-data" XDG_CONFIG_HOME="$work/caddy-config" \
setsid bash -c 'trap "exit 0" TERM; "$1" run --config "$2" & wait' \
  owned-caddy "$caddy_bin" "$work/caddy.json" \
  >"$work/caddy.out" 2>&1 &
caddy_leader=$!

base="https://${HOSTNAME_SYNTHETIC}:${caddy_port}"
resolve="${HOSTNAME_SYNTHETIC}:${caddy_port}:127.0.0.1"
https_get() {
  curl -sS --cacert "$work/cert.pem" --resolve "$resolve" --max-time 30 "$@"
}

edge_ready=0
for _ in $(seq 1 60); do
  if [ "$(https_get -o /dev/null -w '%{http_code}' "$base/health/live" 2>/dev/null)" = "200" ]; then
    edge_ready=1
    break
  fi
  sleep 1
done
[ "$edge_ready" = "1" ] || fail "edge-readiness"
ok "edge-up"

# ---------------------------------------------------------------------------
# Test-only fault injection hooks (never set by an operator).
# ---------------------------------------------------------------------------
if [ "${SLAIF033B_BOUNDARY_FAULT:-}" = "after-edge-up" ]; then
  fail "fault-after-edge-up"
fi
if [ "${SLAIF033B_BOUNDARY_FAULT:-}" = "kill-caddy-leader" ]; then
  kill -KILL "$caddy_leader" 2>/dev/null || fail "fault-inject"
  sleep 1
  # The fault is only meaningful if the leader is dead while the session
  # (the orphaned Caddy child) is still alive.
  if ! kill -0 "$caddy_leader" 2>/dev/null && kill -0 -- "-$caddy_leader" 2>/dev/null; then
    fail "fault-kill-caddy-leader"
  fi
  fail "fault-caddy-session-alive"
fi

# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

# --- TLS transport ---------------------------------------------------------
live_body="$(https_get "$base/health/live")"
[ "$(https_get -o /dev/null -w '%{http_code}' "$base/health/live")" = "200" ] \
  || fail "tls-health-status"
echo "$live_body" | grep -Eq '"status": *"ok"' || fail "tls-health-body"
ok "tls-health"

if curl -sS --resolve "$resolve" --max-time 10 -o /dev/null "$base/health/live" 2>/dev/null; then
  fail "tls-accepted-without-ca"
fi
ok "tls-requires-owned-ca"

plain_status="$(curl -sS --resolve "$resolve" --max-time 10 -o /dev/null \
  -w '%{http_code}' "http://${HOSTNAME_SYNTHETIC}:${caddy_port}/health/live" 2>/dev/null || true)"
[ "$plain_status" = "400" ] || fail "plain-http-on-tls-port"
ok "tls-port-rejects-plain-http"

# --- Response headers through the real edge --------------------------------
headers="$(https_get -D - -o /dev/null "$base/health/live")"
echo "$headers" | grep -qi '^x-content-type-options: nosniff' || fail "header-nosniff"
echo "$headers" | grep -qi '^x-frame-options: deny' || fail "header-xfo"
# The Django response already carries the site policy; the edge must NOT
# weaken or replace it (deferred semantics), and no server identity may
# leak.
echo "$headers" | grep -qi '^referrer-policy: strict-origin-when-cross-origin' \
  || fail "header-referrer-policy-preserved"
echo "$headers" | grep -qi '^server:' && fail "header-server-exposed"
echo "$headers" | grep -qi '^via:' && fail "header-via-exposed"
ok "response-headers"

# --- Forwarding overwrite at the trusted edge -------------------------------
# A client-sent X-Forwarded-Proto must be overwritten by the edge (https),
# never honored: the app sees https and does not redirect.
spoof_status="$(https_get -H 'X-Forwarded-Proto: http' -o /dev/null -w '%{http_code}' \
  "$base/health/live")"
[ "$spoof_status" = "200" ] || fail "edge-xfp-overwrite"
# An ambiguous client XFF chain must be replaced by the edge's single
# real-client value; the app must not see the chain (no ambiguity warning).
chain_rid="$(python3 -c 'import uuid; print(uuid.uuid4())')"
chain_status="$(https_get -H 'X-Forwarded-For: 203.0.113.9, 203.0.113.10' \
  -H "X-Request-ID: $chain_rid" -o /dev/null -w '%{http_code}' "$base/health/live")"
[ "$chain_status" = "200" ] || fail "edge-xff-overwrite"
# Multiple forwarding variants at once (RFC 7239 + X-Forwarded-* +
# X-Real-IP): the edge overwrites the canonical pair; the app strips
# everything else in both branches.
multi_rid="$(python3 -c 'import uuid; print(uuid.uuid4())')"
multi_status="$(https_get -H 'Forwarded: for=203.0.113.99;proto=http' \
  -H 'X-Forwarded-For: 203.0.113.99' -H 'X-Forwarded-Host: evil.example' \
  -H 'X-Forwarded-Port: 8443' -H 'X-Real-IP: 203.0.113.99' \
  -H "X-Request-ID: $multi_rid" -o /dev/null -w '%{http_code}' "$base/health/live")"
[ "$multi_status" = "200" ] || fail "edge-multi-variant"
# Underscore wire variant: passed to Gunicorn, dropped at its parser
# boundary (--header-map drop), never seen by the application.
underscore_status="$(https_get -H 'X_Forwarded_Proto: http' -o /dev/null -w '%{http_code}' \
  "$base/health/live")"
[ "$underscore_status" = "200" ] || fail "edge-underscore-header"
# Bounded wait for the safe request log lines (merged stream; the app
# log is on the container's stderr) - fail if they never appear.
app_logs="$(await_app_log "\"request_id\":\"${chain_rid}\"")" \
  || fail "client-identity-chain"
if ! printf '%s\n' "$app_logs" | grep -qF "\"request_id\":\"${multi_rid}\""; then
  app_logs="$(await_app_log "\"request_id\":\"${multi_rid}\"")" \
    || fail "client-identity-multi"
fi
echo "$app_logs" | grep -q 'proxy-ambiguity' && fail "edge-xff-ambiguity-leaked"
# The normalized client for the chain request is the REAL loopback client
# (the host), never a spoofed chain entry.
echo "$app_logs" | grep "\"request_id\":\"${chain_rid}\"" \
  | grep -Eq '"client":"(127\.0\.0\.1|[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)"' \
  || fail "client-identity-chain"
echo "$app_logs" | grep "\"request_id\":\"${chain_rid}\"" | grep -q '203\.0\.113\.9' \
  && fail "client-identity-spoofed-chain"
echo "$app_logs" | grep "\"request_id\":\"${multi_rid}\"" | grep -q '203\.0\.113\.99' \
  && fail "client-identity-spoofed-multi"
ok "forwarding-overwrite"

# --- Real TLS login, Secure cookies, CSRF with the fixture-port Origin -----
login_status="$(https_get -c "$work/cookies" -o "$work/login-page.html" -w '%{http_code}' \
  "$base/login/")"
[ "$login_status" = "200" ] || fail "login-page"
csrf_token="$(sed -n 's/.*name="csrfmiddlewaretoken" value="\([^"]*\)".*/\1/p' \
  "$work/login-page.html" | head -n 1)"
[ -n "$csrf_token" ] || fail "login-csrf-token"
awk -F'\t' '$6 == "csrftoken" { print $4 }' "$work/cookies" | grep -qx 'TRUE' \
  || fail "csrf-cookie-secure"
user_email="boundary033b@example.test"
# The legitimate browser Origin for this deployment INCLUDES the fixture
# port (CSRF_TRUSTED_ORIGINS carries it); a manual portless Origin would
# mask the real browser behavior and is deliberately not used.
user_password_file="$work/user_password"
{
  printf 'csrfmiddlewaretoken=%s\n' "$csrf_token"
  printf 'username=%s\n' "$user_email"
  printf 'password=%s\n' "$(cat "$user_password_file")"
} | python3 -c 'import sys, urllib.parse
lines = dict(l.strip().split("=", 1) for l in sys.stdin if l.strip())
print(urllib.parse.urlencode(lines))' >"$work/login-post.data"
chmod 600 "$work/login-post.data"
login_resp="$(https_get -H "Origin: https://${HOSTNAME_SYNTHETIC}:${caddy_port}" \
  -b "$work/cookies" -c "$work/cookies" -D "$work/login-post-headers" \
  -o /dev/null -w '%{http_code}' \
  --data @"$work/login-post.data" "$base/login/")" || fail "login-post"
[ "$login_resp" = "302" ] || fail "login-success"
grep -i '^set-cookie: sessionid=' "$work/login-post-headers" | grep -q 'Secure' \
  || fail "session-cookie-secure"
ok "login-secure"

# --- One-time token E2E: header precedence through the real edge ----------
# Fresh CSRF round-trip on the token page; the POST success response must
# arrive through Caddy with the STRICTER per-view policy intact (the edge
# default is deferred, not replacing): no-referrer + no-store/private.
csrf_fetch() {
  https_get -b "$work/cookies" -c "$work/cookies" -c "$1" -o "$2" "$3" >/dev/null 2>&1
}
jar_tok="$work/jar-token"
csrf_fetch "$jar_tok" "$work/token-page.html" "$base/tokens/new/" || fail "token-page"
tok_csrf="$(sed -n 's/.*name="csrfmiddlewaretoken" value="\([^"]*\)".*/\1/p' \
  "$work/token-page.html" | head -n 1)"
[ -n "$tok_csrf" ] || fail "token-csrf-token"
{
  printf 'csrfmiddlewaretoken=%s\n' "$tok_csrf"
  printf 'name=boundary-033b-qualification\n'
  printf 'scopes=reservations:read\n'
  printf 'lifetime_days=1\n'
} | python3 -c 'import sys, urllib.parse
# urlencode requires two-element TUPLES (a list of lists is rejected).
lines = [tuple(l.strip().split("=", 1)) for l in sys.stdin if l.strip()]
print(urllib.parse.urlencode(lines))' >"$work/token-post.data"
chmod 600 "$work/token-post.data"
token_status="$(https_get -H "Origin: https://${HOSTNAME_SYNTHETIC}:${caddy_port}" \
  -b "$jar_tok" -c "$jar_tok" -D "$work/token-post-headers" \
  -o "$work/token-created.html" -w '%{http_code}' \
  --data @"$work/token-post.data" "$base/tokens/new/")" || fail "token-create"
[ "$token_status" = "200" ] || fail "token-create-status"
grep -q 'Copy this token now' "$work/token-created.html" || fail "token-page-marker"
# Header precedence: the STRICTER app headers survived the edge (CRLF is
# normalized for the anchored checks).
token_headers_norm="$(tr -d '\r' <"$work/token-post-headers")"
echo "$token_headers_norm" | grep -qi '^referrer-policy: no-referrer$' \
  || fail "token-referrer-policy-precedence"
echo "$token_headers_norm" | grep -qi '^cache-control: no-store, private' \
  || fail "token-cache-control-precedence"
echo "$token_headers_norm" | grep -qi '^pragma: no-cache' || fail "token-pragma"
echo "$token_headers_norm" | grep -qi '^server:' && fail "token-server-exposed"
echo "$token_headers_norm" | grep -qi '^via:' && fail "token-via-exposed"
# Secret handling: extracted in memory only (never echoed by this script),
# validated against the issued format, then asserted ABSENT from every log
# this run captures.
python3 - "$work/token-created.html" <<'PY' || fail "token-secret-extract"
import re
import sys

html = open(sys.argv[1], encoding="utf-8").read()
match = re.search(
    r'<code id="one-time-bearer-token">([^<]+)</code>', html
)
assert match, "one-time bearer token element missing"
secret = match.group(1).strip()
assert re.fullmatch(r"sar_[0-9a-f]{32}_[A-Za-z0-9_-]{32,128}", secret), (
    "unexpected token format"
)
open("/dev/null", "w")  # secret stays in memory only
PY
sleep 1
# The issued secret must be absent from every artifact this run captures:
# the application logs, the Caddy log and the captured response headers.
# The comparison happens in memory; the secret is never printed or placed
# on a command line.
python3 - "$work/token-created.html" "$app_cid" "$work/caddy.out" \
  "$work/token-post-headers" <<'PY' || fail "token-secret-log-leak"
import re
import subprocess
import sys

html_path, app_cid, caddy_out, headers_path = sys.argv[1:5]
html = open(html_path, encoding="utf-8").read()
secret = re.search(
    r'<code id="one-time-bearer-token">([^<]+)</code>', html
).group(1).strip()
log_proc = subprocess.run(
    ["docker", "logs", app_cid], capture_output=True, text=True, check=False
)
# The application logs are emitted on the container's stderr: both
# streams must be covered or the leak check would be vacuous.
artifacts = {
    "app-logs": log_proc.stdout + log_proc.stderr,
    "caddy-log": open(caddy_out, encoding="utf-8", errors="replace").read(),
    "token-headers": open(headers_path, encoding="utf-8").read(),
}
for name, text in artifacts.items():
    assert secret not in text, f"secret leaked into {name}"
PY
ok "token-e2e-headers"

# --- Normalized CLIENT IP itself (safe instrumentation, no endpoint) ------
# The TLS client is bound to 127.0.0.2 (whole 127/8 is local on Linux: no
# host change) and spoofs Forwarded/XFF. The edge overwrites XFF with the
# REAL client; the app (behind the published port, peer = bridge gateway,
# a configured trusted peer) must normalize to 127.0.0.2 and log it in the
# safe `client` field - the later-compatible instrumentation for the next
# limiter objective. No diagnostic endpoint exists; the proof reads the
# already-emitted safe request log.
client_rid="$(python3 -c 'import uuid; print(uuid.uuid4())')"
python3 - "$caddy_port" "$work/cert.pem" "$client_rid" <<'PY' || fail "client-ip-proof"
import socket
import ssl
import sys
import time

caddy_port, cert, rid = int(sys.argv[1]), sys.argv[2], sys.argv[3]
host = "slaif-boundary.test"
raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
raw.bind(("127.0.0.2", 0))
raw.settimeout(10)
raw.connect(("127.0.0.1", caddy_port))
ctx = ssl.create_default_context(cafile=cert)
sock = ctx.wrap_socket(raw, server_hostname=host)
request = (
    f"GET /health/live HTTP/1.1\r\n"
    f"Host: {host}:{caddy_port}\r\n"
    f"X-Request-ID: {rid}\r\n"
    "Forwarded: for=203.0.113.88;proto=http\r\n"
    "X-Forwarded-For: 203.0.113.88\r\n"
    "Connection: close\r\n"
    "\r\n"
)
sock.sendall(request.encode())
buf = b""
deadline = time.monotonic() + 15
while b"\r\n\r\n" not in buf and time.monotonic() < deadline:
    try:
        chunk = sock.recv(8192)
    except socket.timeout:
        break
    if not chunk:
        break
    buf += chunk
sock.close()
assert buf.startswith(b"HTTP/1.1 200"), f"client-ip probe not 200: {buf[:40]!r}"
PY
client_logs="$(await_app_log "\"request_id\":\"${client_rid}\"")" \
  || fail "client-ip-normalized"
echo "$client_logs" | grep "\"request_id\":\"${client_rid}\"" | grep -q '"client":"127.0.0.2"' \
  || fail "client-ip-normalized"
echo "$client_logs" | grep "\"request_id\":\"${client_rid}\"" | grep -q '203\.0\.113\.88' \
  && fail "client-ip-spoof-leaked"
# Gunicorn's access line records REMOTE_ADDR as it exists AFTER the
# middleware (its 'h' atom): for trusted traffic that is the normalized
# one-hop client, not the original socket peer - which is retained only
# on request.remote_peer and never written to any log. The probe's access
# line must therefore carry the normalized client with a 200, never a
# spoof. 127.0.0.2 is unique to this probe, so the bounded poll below
# identifies exactly its access line.
client_access_logs="$(await_app_log '"peer":"127.0.0.2"')" \
  || fail "gunicorn-access-normalized-client"
access_client_ok="$(echo "$client_access_logs" | grep '"category":"access"' \
  | grep '"peer":"127.0.0.2"' | grep -q '"status":200' && echo yes || echo no)"
[ "$access_client_ok" = "yes" ] || fail "gunicorn-access-normalized-client"
ok "client-ip-proof"

# --- Untrusted direct peer (no Caddy): spoofing must not be honored -------
# A probe container on the project network talks to app:8000 directly. Its
# source is its own bridge IP - NOT the configured gateway peer - so the
# app must treat it as a direct, untrusted client: every forwarding header
# stripped, scheme pinned to the plain transport, 301 redirect, and the
# safe request log carries the probe's own IP, never a spoofed value.
probe_rid="$(python3 -c 'import uuid; print(uuid.uuid4())')"
cat >"$work/probe_untrusted.py" <<'PY'
import os
import socket

rid = os.environ["PROBE_RID"]
sock = socket.create_connection(("app", 8000), timeout=15)
# This container's own source address (UDP connect sends no packet).
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.connect(("172.16.0.1", 53))
own_ip = udp.getsockname()[0]
udp.close()
request = (
    "GET /health/live HTTP/1.1\r\n"
    "Host: slaif-boundary.test\r\n"
    f"X-Request-ID: {rid}\r\n"
    "X-Forwarded-Proto: https\r\n"
    "X-Forwarded-For: 203.0.113.77, 203.0.113.78\r\n"
    "Forwarded: for=203.0.113.77;proto=https\r\n"
    "X-Forwarded-Host: evil.example\r\n"
    "X-Real-IP: 203.0.113.77\r\n"
    "Connection: close\r\n"
    "\r\n"
)
sock.sendall(request.encode())
buf = b""
while b"\r\n\r\n" not in buf:
    chunk = sock.recv(8192)
    if not chunk:
        break
    buf += chunk
sock.close()
first_line = buf.split(b"\r\n", 1)[0].decode("latin-1", "replace")
status = first_line.split(" ")[1] if len(first_line.split(" ")) >= 2 else ""
location = next(
    (line.split(b":", 1)[1].strip().decode() for line in buf.split(b"\r\n")
     if line.lower().startswith(b"location:")),
    "",
)
print(f"status={status}")
print(f"own_ip={own_ip}")
print(f"location={location}")
PY
chmod 600 "$work/probe_untrusted.py"
probe_result="$(PROBE_RID="$probe_rid" docker run --rm -i \
  --network "${project}_default" \
  --env "PROBE_RID=$probe_rid" \
  --entrypoint python "$image_tag" - <"$work/probe_untrusted.py" 2>/dev/null)" \
  || fail "probe-untrusted-run"
echo "$probe_result" | grep -q '^status=301' || fail "untrusted-redirect"
echo "$probe_result" | grep -q '^location=https://slaif-boundary.test/health/live$' \
  || fail "untrusted-redirect-target"
probe_ip="$(echo "$probe_result" | sed -n 's/^own_ip=//p')"
[[ "$probe_ip" =~ ^[0-9.]+$ ]] || fail "untrusted-probe-ip"
# The 301 is issued before the safe request log middleware completes
# (the SSL redirect short-circuits the middleware chain), so this
# request's identity proof reads the Gunicorn access line instead: its
# peer is the ORIGINAL socket peer of the rejected request - the probe's
# own bridge IP, never a spoofed chain value.
probe_logs="$(await_app_log "\"peer\":\"${probe_ip}\"")" \
  || fail "untrusted-client-identity"
probe_peer_301="$(echo "$probe_logs" | grep '"category":"access"' \
  | grep "\"peer\":\"${probe_ip}\"" | grep -q '"status":301' && echo yes || echo no)"
[ "$probe_peer_301" = "yes" ] || fail "untrusted-client-identity"
echo "$probe_logs" | grep -q '203\.0\.113\.77' && fail "untrusted-spoof-leaked"
ok "untrusted-spoof-refused"

# --- Private docs stay private through the edge ----------------------------
schema_status="$(https_get -o /dev/null -w '%{http_code}' "$base/api/schema/")"
[ "$schema_status" = "404" ] || fail "private-schema"
docs_status="$(https_get -o /dev/null -w '%{http_code}' "$base/api/docs/")"
[ "$docs_status" = "404" ] || fail "private-docs"
ok "private-docs"

# --- Dead-DB instance: liveness stays up, readiness is a safe 503 ---------
dead_name="${project}-appdead-1"
dead_port="$(free_port)"
if ! dead_cid="$(docker run -d --name "$dead_name" \
  --label "slaif.qualification.owner=$run_owner" \
  --read-only --tmpfs /tmp --user 10001:10001 \
  -p "127.0.0.1:${dead_port}:8000" \
  --network "${project}_default" \
  --network-alias appdead \
  --env-file "$dead_env_file" \
  "$image_tag")"; then
  fail "dead-create"
fi
dead_created=1
# Liveness/readiness through the trusted in-container path (127.0.0.1 peer
# + X-Forwarded-Proto header: the same one the compose healthcheck uses).
# An untrusted bridge peer over plain transport would be redirected (301)
# before the views run, which would not exercise the dead-DB boundary.
cat >"$work/probe_dead.py" <<'PY'
import urllib.error
import urllib.request


def get(path):
    req = urllib.request.Request(
        f"http://127.0.0.1:8000{path}",
        headers={"X-Forwarded-Proto": "https"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


live_status, _ = get("/health/live")
ready_status, ready_body = get("/health/ready")
print(f"live={live_status}")
print(f"ready={ready_status}")
print(f"ready_body={ready_body}")
PY
chmod 600 "$work/probe_dead.py"
dead_ready=0
for _ in $(seq 1 120); do
  if docker exec -i "$dead_cid" python - <"$work/probe_dead.py" >/dev/null 2>&1; then
    dead_ready=1
    break
  fi
  sleep 1
done
[ "$dead_ready" = "1" ] || fail "dead-app-up"
dead_result="$(docker exec -i "$dead_cid" python - <"$work/probe_dead.py" 2>/dev/null)" \
  || fail "dead-probe"
echo "$dead_result" | grep -q '^live=200' || fail "dead-db-liveness"
echo "$dead_result" | grep -q '^ready=503' || fail "dead-db-ready-status"
ready_body="$(echo "$dead_result" | sed -n 's/^ready_body=//p')"
echo "$ready_body" | grep -Eq '"status": *"unavailable"' || fail "dead-db-ready-body"
echo "$ready_body" | grep -qiE 'psycopg|operationalerror|connection refused|database' \
  && fail "dead-db-ready-details"
ok "dead-db-boundary"

# Production fail-closed 503 response and logging through TLS, using the identical
# proxy contract and a non-root/read-only app pointed at its own closed
# database port. No production crash endpoint is introduced.
error_port="$(free_port)"
python3 - "$work/caddy.json" "$work/error.json" "$error_port" "$dead_port" <<'PYERRORCONFIG'
import json
import sys
cfg = json.load(open(sys.argv[1]))
server = next(iter(cfg["apps"]["http"]["servers"].values()))
server["listen"] = ["127.0.0.1:" + sys.argv[3]]
def retarget(node):
    if isinstance(node, dict):
        if node.get("handler") == "reverse_proxy":
            node["upstreams"] = [{"dial": "127.0.0.1:" + sys.argv[4]}]
        for value in node.values(): retarget(value)
    elif isinstance(node, list):
        for value in node: retarget(value)
retarget(cfg)
json.dump(cfg, open(sys.argv[2], "w"))
PYERRORCONFIG
XDG_DATA_HOME="$work/error-data" XDG_CONFIG_HOME="$work/error-config" setsid bash -c 'trap "exit 0" TERM; "$1" run --config "$2" & wait'   owned-error "$caddy_bin" "$work/error.json" >"$work/error.out" 2>&1 &
owned_probe_sessions+=("$!")
python3 - "$work/error-curl.conf" <<'PYAUTH'
import secrets
import sys
import uuid
value = "sar_" + uuid.uuid4().hex + "_" + secrets.token_hex(32)
open(sys.argv[1], "w").write('header = "Authorization: Bearer ' + value + '"\n')
PYAUTH
chmod 600 "$work/error-curl.conf"
for _ in $(seq 1 60); do
  error_status="$(curl -sS --cacert "$work/cert.pem"     --resolve "${HOSTNAME_SYNTHETIC}:${error_port}:127.0.0.1"     --config "$work/error-curl.conf" -H 'Accept: application/json'     --max-time 3 -o "$work/error-body" -w '%{http_code}'     "https://${HOSTNAME_SYNTHETIC}:${error_port}/api/v1/me/" 2>/dev/null || true)"
  [ "$error_status" = "503" ] && break
  sleep 0.1
done
[ "$error_status" = "503" ] || fail "production-error-status"
python3 - "$work/error-curl.conf" "$work/error-body" "$dead_cid" "$work/error.out" <<'PYERRORSAFE' || fail "production-error-privacy"
import re
import subprocess
import sys
credential = open(sys.argv[1]).read().split("Bearer ", 1)[1].split('"', 1)[0]
body = open(sys.argv[2]).read()
logs = subprocess.run(["docker", "logs", sys.argv[3]], capture_output=True, text=True)
outputs = [body, logs.stdout, logs.stderr, open(sys.argv[4]).read()]
assert all(credential not in value for value in outputs), "credential leaked at production error boundary"
assert not re.search(r"Traceback|OperationalError|DATABASE_URL|django\.db|connection refused", body), "production error exposed details"
PYERRORSAFE
ok "production-error-safe-through-tls"

# --- Body size / rate contract (docs/deployment.md section 8) --------------
# Layered, honest contract:
#  (a) form content types: the application's own DATA_UPLOAD_MAX_MEMORY_SIZE
#      cap rejects with 400 before view logic (early, bounded);
#  (b) multipart bodies the app reads: the edge's shipped 10MB cap rejects
#      with 413, exercised on a Content-Length multipart upload here;
#  (c) bodies the app never reads (unknown-length form bodies and
#      octet-stream bodies): NOT rejected as a whole body - the app
#      answers as for an empty form (200, nothing from the body is
#      accepted), edge memory stays bounded by the shipped 1MB buffer,
#      and the pool stays responsive (bounded-unread, not a rejection);
#  (d) the shipped read_body_idle pair (30s / 1024) cuts stalled and
#      below-floor trickling bodies while a healthy pool keeps serving.
head -c 11534336 /dev/zero | tr '\0' 'x' >"$work/bigbody"
chmod 600 "$work/bigbody"
head -c 3145728 /dev/zero | tr '\0' 'z' >"$work/formcap"
chmod 600 "$work/formcap"
head -c 655360 /dev/zero | tr '\0' 'y' >"$work/midbody"
chmod 600 "$work/midbody"

# The body-matrix upload tests POST the LOGIN form, which an
# AUTHENTICATED session cannot fetch (Django's LoginView answers 403 to
# logged-in users), so each body case fetches the login page with a FRESH
# ANONYMOUS jar only - the anonymous page is what sets the csrftoken
# cookie and token the subsequent POST carries.
csrf_fetch() {
  https_get -c "$1" -o "$2" "$base/login/" >/dev/null 2>&1
}
csrf_token_to() {
  sed -n 's/.*name="csrfmiddlewaretoken" value="\([^"]*\)".*/\1/p' "$1" | head -n 1 >"$2"
  chmod 600 "$2"
}
build_form_body() {
  # $1 = token file, $2 = payload file, $3 = out
  python3 - "$1" "$2" "$3" <<'PY'
import sys

token = open(sys.argv[1], encoding="utf-8").read().strip()
payload = open(sys.argv[2], "rb").read()
with open(sys.argv[3], "wb") as fh:
    fh.write(b"csrfmiddlewaretoken=" + token.encode())
    fh.write(b"&payload=" + payload)
PY
  chmod 600 "$3"
}
build_multipart_body() {
  # $1 = token file, $2 = payload file, $3 = out
  python3 - "$1" "$2" "$3" <<'PY'
import sys

token = open(sys.argv[1], encoding="utf-8").read().strip()
data = open(sys.argv[2], "rb").read()
boundary = "----slaif033b-bodycap-boundary"
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="csrfmiddlewaretoken"\r\n\r\n'
    f"{token}\r\n"
    f"--{boundary}\r\n"
    'Content-Disposition: form-data; name="file"; filename="big.bin"\r\n'
    "Content-Type: application/octet-stream\r\n\r\n"
).encode() + data + f"\r\n--{boundary}--\r\n".encode()
with open(sys.argv[3], "wb") as fh:
    fh.write(body)
PY
  chmod 600 "$3"
}

# (a) 3MiB form: ABOVE the application's 2.5MiB
# DATA_UPLOAD_MAX_MEMORY_SIZE cap, BELOW the edge's 10MB cap: the
# application rejects with 400 early, before view logic. Django's
# Content-Length pre-check means an oversized FORM body is never read
# at all - so the edge's read-time cap cannot fire on form bodies
# (any form body above 2.5MiB gets this same early 400).
jar_a="$work/jar-a"
csrf_fetch "$jar_a" "$work/page-a" || fail "body-a-csrf"
csrf_token_to "$work/page-a" "$work/token-a"
[ -s "$work/token-a" ] || fail "body-a-token"
build_form_body "$work/token-a" "$work/formcap" "$work/body-a"
start_s="$(date +%s)"
app_cap_status="$(https_get -b "$jar_a" -c "$jar_a" \
  -H "Origin: https://${HOSTNAME_SYNTHETIC}:${caddy_port}" \
  -o /dev/null -w '%{http_code}' -X POST --max-time 15 \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-binary @"$work/body-a" "$base/login/" 2>/dev/null || true)"
end_s="$(date +%s)"
[ "$app_cap_status" = "400" ] || fail "body-cap-app observed=${app_cap_status:-none}"
[ $((end_s - start_s)) -lt 5 ] || fail "body-cap-app-not-early"
ok "body-cap-app-400-early"

# (b1) 11MiB multipart (Content-Length known): edge cap 413.
jar_b="$work/jar-b"
csrf_fetch "$jar_b" "$work/page-b" || fail "body-b-csrf"
csrf_token_to "$work/page-b" "$work/token-b"
[ -s "$work/token-b" ] || fail "body-b-token"
build_multipart_body "$work/token-b" "$work/bigbody" "$work/body-b"
edge_cap_status="$(https_get -b "$jar_b" -c "$jar_b" \
  -H "Origin: https://${HOSTNAME_SYNTHETIC}:${caddy_port}" \
  -o /dev/null -w '%{http_code}' -X POST --max-time 30 \
  -H 'Content-Type: multipart/form-data; boundary=----slaif033b-bodycap-boundary' \
  --data-binary @"$work/body-b" "$base/login/" 2>/dev/null || true)"
[ "$edge_cap_status" = "413" ] || fail "body-cap-edge observed=${edge_cap_status:-none}"
ok "body-cap-edge-413"

# (b2) 11MiB multipart, CHUNKED (no Content-Length: unknown length).
# HONEST CONTRACT (docs/deployment.md section 8; 033-b evidence):
# the shipped edge cap (request_body max_size 10MB) is a read-time
# bound. This application does NOT read a body that arrives without
# Content-Length: Gunicorn sets no CONTENT_LENGTH for chunked bodies
# (wsgi.input_terminated only) and Django's multipart parser treats
# the form data as empty when the content length is absent, so the
# login view answers the form re-render for an EMPTY form (200)
# without streaming the body. The 200 is therefore HONESTLY LABELED:
# it is the app's empty-form response, NOT a whole-body rejection,
# and nothing from the body is accepted or read. The edge still
# bounds such requests finitely: 1MB memory (request_buffers),
# 30s/1024 stall+trickle cuts (read_body_idle), and no connection
# reuse with a residual body (the edge closes the connection after
# the response; proven by the 033-b keep-alive probe). The 10MB cap
# itself holds for ANY body the application reads, chunked or not
# (033-b probe: body-reading backend, chunked 11MiB -> 413).
jar_c="$work/jar-c"
csrf_fetch "$jar_c" "$work/page-c" || fail "body-c-csrf"
csrf_token_to "$work/page-c" "$work/token-c"
[ -s "$work/token-c" ] || fail "body-c-token"
build_multipart_body "$work/token-c" "$work/bigbody" "$work/body-c"
b2_rid="$(python3 -c 'import uuid; print(uuid.uuid4())')"
printf '%s\n' "$b2_rid" >"$work/rid-b2"
chmod 600 "$work/rid-b2"
# curl handles an early response while uploading; a hand-written send-all
# loop mistakes the server closing an unread body for a rehearsal failure.
python3 - "$work/token-c" "$work/chunked-csrf.conf" <<'PYCONF'
from pathlib import Path
import sys
token = Path(sys.argv[1]).read_text().strip()
Path(sys.argv[2]).write_text('header = "X-CSRFToken: ' + token + '"\n')
PYCONF
chmod 600 "$work/chunked-csrf.conf"
chunked_status="$(https_get --config "$work/chunked-csrf.conf" \
  -b "$jar_c" -H "Origin: https://${HOSTNAME_SYNTHETIC}:${caddy_port}" \
  -H "Transfer-Encoding: chunked" -H "X-Request-ID: $b2_rid" \
  -H 'Content-Type: multipart/form-data; boundary=----slaif033b-bodycap-boundary' \
  --data-binary @"$work/body-c" -o "$work/page-c2" -w '%{http_code}' \
  --max-time 20 "$base/login/" 2>/dev/null)" || fail "body-chunked-run"
[ "$chunked_status" = "200" ] || fail "body-cap-chunked observed=${chunked_status:-none}"
# The response must be the login form re-rendered for the EMPTY form:
# the app treated the unknown-length body as carrying no form data.
grep -q 'csrfmiddlewaretoken' "$work/page-c2" || fail "body-cap-chunked-not-form"
# The request must complete WITHOUT the app streaming 11MiB: the safe
# request log line for the unique request ID shows a short duration.
b2_logs="$(await_app_log "\"request_id\":\"${b2_rid}\"")" || fail "body-cap-chunked-log"
b2_duration="$(printf '%s\n' "$b2_logs" \
  | grep -F "\"request_id\":\"${b2_rid}\"" | sed -n 's/.*"duration_ms": *\([0-9.]*\).*/\1/p' | head -n 1)"
[ -n "$b2_duration" ] || fail "body-cap-chunked-duration"
python3 - "$b2_duration" <<'PY' || fail "body-cap-chunked-slow"
import sys
sys.exit(0 if float(sys.argv[1]) < 1000.0 else 1)
PY
ok "body-cap-chunked-ignored-not-rejection"

# (c) 11MiB octet-stream: the app never reads this body. The response is
# 200 - HONESTLY LABELED: bounded by the edge buffer, NOT a whole-body
# rejection (the lazy-proxy limit; see docs/deployment.md section 8).
jar_d="$work/jar-d"
csrf_fetch "$jar_d" "$work/page-d" || fail "body-d-csrf"
csrf_token_to "$work/page-d" "$work/token-d"
[ -s "$work/token-d" ] || fail "body-d-token"
# The CSRF token travels in a 0600 curl config file - never in argv.
python3 - "$work/token-d" "$work/curl-csrf.conf" <<'PY'
import os
import sys

token = open(sys.argv[1], encoding="utf-8").read().strip()
with open(sys.argv[2], "w", encoding="utf-8") as fh:
    fh.write(f'header = "X-CSRFToken: {token}"\n')
os.chmod(sys.argv[2], 0o600)
PY
unread_status="$(https_get -b "$jar_d" -c "$jar_d" \
  -H "Origin: https://${HOSTNAME_SYNTHETIC}:${caddy_port}" \
  --config "$work/curl-csrf.conf" \
  -o /dev/null -w '%{http_code}' -X POST --max-time 30 \
  -H 'Content-Type: application/octet-stream' \
  --data-binary @"$work/bigbody" "$base/login/" 2>/dev/null || true)"
[ "$unread_status" = "200" ] || fail "body-unread observed=${unread_status:-none}"
pool_status="$(https_get -o /dev/null -w '%{http_code}' --max-time 10 "$base/health/live")"
[ "$pool_status" = "200" ] || fail "body-unread-pool"
ok "body-cap-unread-bounded-not-rejection"

build_multipart_nofield_body() {
  # $1 = payload file, $2 = out: multipart WITHOUT a csrfmiddlewaretoken
  # field (the early-CSRF negative control; the application still reads
  # the body while hunting for the token, then rejects 403 before view
  # logic - well under the edge cap).
  python3 - "$1" "$2" <<'PY'
import sys

payload = open(sys.argv[1], "rb").read()
boundary = "----slaif033b-bodycap-boundary"
body = (
    f"--{boundary}\r\n"
    'Content-Disposition: form-data; name="file"; filename="big.bin"\r\n'
    "Content-Type: application/octet-stream\r\n\r\n"
).encode() + payload + f"\r\n--{boundary}--\r\n".encode()
with open(sys.argv[2], "wb") as fh:
    fh.write(body)
PY
  chmod 600 "$2"
}
build_multipart_nofield_body "$work/midbody" "$work/body-d1"

# (d1) Early CSRF: a 640 KiB multipart WITHOUT a CSRF token is rejected
# 403 before view logic (and well under the edge cap).
early_start_s="$(date +%s)"
early_status="$(https_get -o /dev/null -w '%{http_code}' -X POST --max-time 15 \
  -H 'Content-Type: multipart/form-data; boundary=----slaif033b-bodycap-boundary' \
  --data-binary @"$work/body-d1" "$base/login/" 2>/dev/null || true)"
early_end_s="$(date +%s)"
[ "$early_status" = "403" ] || fail "body-early-csrf observed=${early_status:-none}"
[ $((early_end_s - early_start_s)) -lt 5 ] || fail "body-early-csrf-not-early"
ok "body-early-csrf-403-early"

# (e) Above the shipped min-rate: a 640KiB multipart (with CSRF, app reads
# the body) completes normally - the floor does not cut healthy traffic.
build_multipart_body "$work/token-d" "$work/midbody" "$work/body-e"
above_start_s="$(date +%s)"
above_status="$(https_get -b "$jar_d" -c "$jar_d" \
  -H "Origin: https://${HOSTNAME_SYNTHETIC}:${caddy_port}" \
  -o /dev/null -w '%{http_code}' -X POST --max-time 20 \
  -H 'Content-Type: multipart/form-data; boundary=----slaif033b-bodycap-boundary' \
  --data-binary @"$work/body-e" "$base/login/" 2>/dev/null || true)"
above_end_s="$(date +%s)"
[ "$above_status" = "200" ] || fail "body-above-floor observed=${above_status:-none}"
[ $((above_end_s - above_start_s)) -le 15 ] || fail "body-above-floor-slow"
ok "body-above-floor-completes"

# (f) Stalled and below-floor trickling bodies are cut by the shipped
# read_body_idle pair (30s window, 1024-byte/second min-rate); a healthy pool keeps
# serving during the cut. Both probes run in parallel.
#
# Each probe is a multipart POST to /login/ carrying a VALID csrfmiddlewaretoken
# in the FIRST chunk plus a 5MiB declared file field: the application's
# multipart parser (reached via the CSRF check's request.POST lookup) then
# reads the body and stalls inside it, so the EDGE's read_body_idle governs
# the cut. (An unread body would never be measured; a tokenless body would
# be answered before the read completes.) When the edge cuts, v2.11.6
# responds to the client with a 499 - asserted, not papered over.
jar_f="$work/jar-f"
csrf_fetch "$jar_f" "$work/page-f" || fail "body-f-csrf"
csrf_token_to "$work/page-f" "$work/token-f"
[ -s "$work/token-f" ] || fail "body-f-token"
cat >"$work/probe_bodycut.py" <<'PY'
import socket
import ssl
import sys
import threading
import time

caddy_port, cert = int(sys.argv[1]), sys.argv[2]
mode = sys.argv[3]  # "stall" | "trickle"
jar_path, token_path = sys.argv[4], sys.argv[5]
host = "slaif-boundary.test"


def cookie_header() -> str:
    pairs = []
    for line in open(jar_path, encoding="utf-8"):
        if not line.strip() or line.startswith("#") and not line.startswith(
            "#HttpOnly_"
        ):
            continue
        fields = line.rstrip("\n").lstrip("#HttpOnly_").split("\t")
        if len(fields) >= 7:
            pairs.append(f"{fields[5]}={fields[6]}")
    return ", ".join(pairs)


def tls_conn():
    raw = socket.create_connection(("127.0.0.1", caddy_port), timeout=5)
    ctx = ssl.create_default_context(cafile=cert)
    return ctx.wrap_socket(raw, server_hostname=host)


def health_prompt() -> None:
    sock = tls_conn()
    try:
        sock.settimeout(5.0)
        sock.sendall(
            f"GET /health/live HTTP/1.1\r\nHost: {host}:{caddy_port}\r\n"
            "Connection: close\r\n\r\n".encode()
        )
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
        assert buf.startswith(b"HTTP/1.1 200"), "health not prompt during body cut"
    finally:
        sock.close()


def probe_body() -> None:
    sock = tls_conn()
    try:
        token = open(token_path, encoding="utf-8").read().strip()
        boundary = "----slaif033b-bodycut"
        first = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="csrfmiddlewaretoken"\r\n'
            "\r\n"
            f"{token}\r\n"
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="slow.bin"\r\n'
            "Content-Type: application/octet-stream\r\n"
            "\r\n"
        ).encode() + b"x" * 1024
        total = 5242880
        head = (
            f"POST /login/ HTTP/1.1\r\n"
            f"Host: {host}:{caddy_port}\r\n"
            f"Origin: https://{host}:{caddy_port}\r\n"
            f"Cookie: {cookie_header()}\r\n"
            f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
            f"Content-Length: {total}\r\n"
            "Connection: close\r\n"
            "\r\n"
        )
        sock.settimeout(5.0)
        sock.sendall(head.encode() + first)
        started = time.monotonic()
        outcome = "hung"
        first_line = ""
        while time.monotonic() - started < 50:
            if mode == "trickle" and time.monotonic() - started > 5:
                sock.sendall(b"t" * 100)
                time.sleep(5)
            try:
                chunk = sock.recv(4096)
            except socket.timeout:
                continue
            except OSError:
                outcome = "closed"
                break
            if not chunk:
                outcome = "eof"
                break
            if b"\r\n\r\n" in chunk:
                outcome = "status"
                first_line = chunk.split(b"\r\n", 1)[0].decode("latin-1")
                break
        result["elapsed"] = time.monotonic() - started
        result["outcome"] = outcome
        result["first_line"] = first_line
    finally:
        sock.close()


result = {}
health_prompt()
started = time.monotonic()
threading.Thread(target=probe_body, daemon=True).start()
# Poll health DURING the cut window: the pool must keep serving.
healths = []
deadline = time.monotonic() + 65
t = 0
while "outcome" not in result:
    if time.monotonic() > deadline:
        raise SystemExit("body cut never happened")
    t += 1
    if t % 5 == 0 and 10 < time.monotonic() - started < 48:
        try:
            health_prompt()
            healths.append("ok")
        except AssertionError:
            healths.append("slow")
    time.sleep(1)
health_prompt()
print(f"outcome={result['outcome']}")
print(f"first_line={result['first_line']}")
print(f"elapsed={result['elapsed']:.1f}")
print(f"healths={len(healths)}")
PY
chmod 600 "$work/probe_bodycut.py"
setsid python3 "$work/probe_bodycut.py" "$caddy_port" "$work/cert.pem" stall \
  "$jar_f" "$work/token-f" >"$work/bodycut-stall.out" 2>&1 &
stall_pid=$!
owned_probe_sessions+=("$stall_pid")
setsid python3 "$work/probe_bodycut.py" "$caddy_port" "$work/cert.pem" trickle \
  "$jar_f" "$work/token-f" >"$work/bodycut-trickle.out" 2>&1 &
trickle_pid=$!
owned_probe_sessions+=("$trickle_pid")
wait "$stall_pid" || fail "body-cut-stall-probe"
wait "$trickle_pid" || fail "body-cut-trickle-probe"
for mode in stall trickle; do
  outcome="$(sed -n 's/^outcome=//p' "$work/bodycut-$mode.out")"
  first_line="$(sed -n 's/^first_line=//p' "$work/bodycut-$mode.out")"
  elapsed="$(sed -n 's/^elapsed=//p' "$work/bodycut-$mode.out")"
  healths="$(sed -n 's/^healths=//p' "$work/bodycut-$mode.out")"
  python3 - "$mode" "$outcome" "$first_line" "$elapsed" "$healths" <<'PY' || fail "body-cut-bounds"
import sys

mode, outcome, first_line, elapsed, healths = (
    sys.argv[1],
    sys.argv[2],
    sys.argv[3],
    float(sys.argv[4]),
    int(sys.argv[5]),
)
# The edge cut surfaces to the client as Caddy's 499 (verified against
# v2.11.6 with the shipped read_body_idle pair); a clean EOF also counts as
# a cut, but a full error page (403/400/...) would mean the application
# answered before the body read was cut.
assert outcome == "status" and len(first_line.split()) >= 2 and first_line.split()[1] == "499", (
    f"{mode}: not cut by the edge: {outcome} {first_line!r}"
)
# The shipped 30s window: the cut must not come sooner than a full healthy
# window's worth of below-floor tolerance, nor much later than the window.
assert 10.0 < elapsed <= 45.0, f"{mode}: cut at {elapsed}s"
# Health was polled during the cut window; every poll answered 200.
assert healths >= 1, f"{mode}: no in-window health probe completed"
PY
done
ok "body-stall-and-trickle-bounded"

# Exercise a total deadline against a sender ABOVE the minimum rate. The
# identical adapted shipped configuration is used, with only the owned
# listener and the declared 60s -> 3s test deadline changed.
total_port="$(free_port)"
python3 - "$work/caddy.json" "$work/total.json" "$total_port" <<'PYCONFIG'
import json
import sys
cfg = json.load(open(sys.argv[1]))
server = next(iter(cfg["apps"]["http"]["servers"].values()))
assert server["read_timeout"] == 60 * 10**9
assert server["read_min_rate"] == 1024
server["read_timeout"] = 3 * 10**9
server["listen"] = ["127.0.0.1:" + sys.argv[3]]
json.dump(cfg, open(sys.argv[2], "w"))
PYCONFIG
XDG_DATA_HOME="$work/total-data" XDG_CONFIG_HOME="$work/total-config" setsid bash -c 'trap "exit 0" TERM; "$1" run --config "$2" & wait'   owned-total "$caddy_bin" "$work/total.json" >"$work/total.out" 2>&1 &
total_leader=$!
python3 - "$total_port" "$work/cert.pem" <<'PYPROBE' || fail "total-body-deadline"
import socket
import ssl
import sys
import time

port, cert = int(sys.argv[1]), sys.argv[2]
ctx = ssl.create_default_context(cafile=cert)

def connect():
    raw = socket.create_connection(("127.0.0.1", port), timeout=2)
    return ctx.wrap_socket(raw, server_hostname="slaif-boundary.test")

for _ in range(40):
    try:
        test = connect()
        test.sendall(b"GET /health/live HTTP/1.1\r\nHost: slaif-boundary.test\r\nConnection: close\r\n\r\n")
        good = test.recv(1024).startswith(b"HTTP/1.1 200")
        test.close()
        if good:
            break
    except OSError:
        pass
    time.sleep(0.1)
else:
    raise SystemExit("total-deadline edge unavailable")

sock = connect()
sock.settimeout(0.05)
started = time.monotonic()
cut = False
sent = 0
try:
    sock.sendall(b"POST /login/ HTTP/1.1\r\nHost: slaif-boundary.test\r\nContent-Type: application/octet-stream\r\nContent-Length: 2000000\r\nConnection: close\r\n\r\n")
    while time.monotonic() - started < 6:
        try:
            sock.sendall(b"x" * 4096)
            sent += 4096
            try:
                data = sock.recv(4096)
                if not data or data.startswith(b"HTTP/1.1"):
                    cut = True
                    break
            except socket.timeout:
                pass
        except OSError:
            cut = True
            break
        time.sleep(0.15)
finally:
    sock.close()
elapsed = time.monotonic() - started
assert cut and 2.5 <= elapsed <= 5.5, "total body deadline did not cut the upload"
assert sent / elapsed > 1024, "probe was not above the minimum rate"
# The same application pool remains available after the cut.
test = connect()
test.sendall(b"GET /health/live HTTP/1.1\r\nHost: slaif-boundary.test\r\nConnection: close\r\n\r\n")
assert test.recv(1024).startswith(b"HTTP/1.1 200"), "pool unavailable after body deadline"
test.close()
PYPROBE
ok "total-body-deadline-above-min-rate"

# (g) Slow header read: cut by the (harness-shortened) read_header window.
python3 - "$caddy_port" "$work/cert.pem" "$READ_HEADER_TIMEOUT_S" <<'PY' || fail "slow-header-bounded"
import socket
import ssl
import sys
import threading
import time

caddy_port, cert, rht_s = int(sys.argv[1]), sys.argv[2], int(sys.argv[3])
host = "slaif-boundary.test"


def tls_conn():
    raw = socket.create_connection(("127.0.0.1", caddy_port), timeout=5)
    ctx = ssl.create_default_context(cafile=cert)
    return ctx.wrap_socket(raw, server_hostname=host)


def health_prompt() -> None:
    sock = tls_conn()
    try:
        sock.settimeout(5.0)
        sock.sendall(
            f"GET /health/live HTTP/1.1\r\nHost: {host}:{caddy_port}\r\n"
            "Connection: close\r\n\r\n".encode()
        )
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
        assert buf.startswith(b"HTTP/1.1 200"), "health not prompt during slow headers"
    finally:
        sock.close()


def slow_header() -> None:
    sock = tls_conn()
    try:
        sock.settimeout(0.5)
        sock.sendall(f"GET /health/live HTTP/1.1\r\nHost: {host}\r\n".encode())
        started = time.monotonic()
        while time.monotonic() - started < rht_s + 10:
            try:
                chunk = sock.recv(4096)
            except socket.timeout:
                continue
            except OSError:
                result["outcome"] = "closed"
                result["elapsed"] = time.monotonic() - started
                return
            if not chunk:
                result["outcome"] = "eof"
                result["elapsed"] = time.monotonic() - started
                return
    finally:
        sock.close()
    result["outcome"] = "hung"
    result["elapsed"] = rht_s + 10


result = {}
health_prompt()
threading.Thread(target=slow_header, daemon=True).start()
for _ in range(60):
    if "outcome" in result:
        break
    time.sleep(0.5)
assert "outcome" in result, "slow-header probe incomplete"
assert result["outcome"] in ("eof", "closed"), f"slow headers not cut: {result['outcome']}"
assert result["elapsed"] <= rht_s + 4.0, f"slow-header cutoff too slow: {result['elapsed']:.1f}s"
PY
ok "slow-header-bounded"

# (h) Oversized header SIZE: Go net/http's 1MB cap -> 431 (separate from
# the body cap; the shipped Caddyfile documents this boundary).
python3 - "$caddy_port" "$work/cert.pem" <<'PY' || fail "header-size-431"
import socket
import ssl
import sys

caddy_port, cert = int(sys.argv[1]), sys.argv[2]
host = "slaif-boundary.test"
raw = socket.create_connection(("127.0.0.1", caddy_port), timeout=10)
ctx = ssl.create_default_context(cafile=cert)
sock = ctx.wrap_socket(raw, server_hostname=host)
big = "a" * (1300 * 1024)
request = (
    f"GET /health/live HTTP/1.1\r\n"
    f"Host: {host}:{caddy_port}\r\n"
    f"X-Big: {big}\r\n"
    "Connection: close\r\n"
    "\r\n"
)
sock.sendall(request.encode())
buf = b""
while b"\r\n\r\n" not in buf:
    chunk = sock.recv(8192)
    if not chunk:
        break
    buf += chunk
sock.close()
first = buf.split(b"\r\n", 1)[0].decode("latin-1", "replace")
parts = first.split()
assert len(parts) >= 2 and parts[1] == "431", f"expected 431 for oversized headers, got: {first}"
PY
ok "header-size-431"

# (i) Idle keep-alive connection: closed by the (harness-shortened) idle
# window.
python3 - "$caddy_port" "$IDLE_TIMEOUT_S" "$work/cert.pem" <<'PY' || fail "idle-connection-closed"
import socket
import ssl
import sys
import time

caddy_port, idle_s, cert = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
host = "slaif-boundary.test"
raw = socket.create_connection(("127.0.0.1", caddy_port), timeout=5)
ctx = ssl.create_default_context(cafile=cert)
sock = ctx.wrap_socket(raw, server_hostname=host)
sock.settimeout(30.0)
sock.sendall(
    f"GET /health/live HTTP/1.1\r\nHost: {host}:{caddy_port}\r\n\r\n".encode()
)
buf = b""
while b"\r\n\r\n" not in buf:
    chunk = sock.recv(4096)
    if not chunk:
        break
    buf += chunk
head, body = buf.split(b"\r\n\r\n", 1)
length = 0
for line in head.decode("latin-1").split("\r\n")[1:]:
    if line.lower().startswith("content-length:"):
        length = int(line.split(":", 1)[1].strip())
while len(body) < length:
    chunk = sock.recv(4096)
    if not chunk:
        break
    body += chunk
started = time.monotonic()
try:
    chunk = sock.recv(1)
    assert chunk == b"", f"expected clean EOF, got {len(chunk)} bytes"
except socket.timeout:
    raise SystemExit("idle connection not closed within bound")
finally:
    sock.close()
elapsed = time.monotonic() - started
assert elapsed <= idle_s + 5.0, f"idle connection held too long: {elapsed:.1f}s"
PY
ok "idle-connection-closed"

# --- Canary log privacy ----------------------------------------------------
canary_path="oap033b-boundary-canary"
canary_status="$(https_get -o /dev/null -w '%{http_code}' "$base/no-such/${canary_path}/")"
[ "$canary_status" = "404" ] || fail "canary-404"
sleep 1
canary_logs="$(docker logs "$app_cid" 2>&1)"
echo "$canary_logs" | grep -q "$canary_path" && fail "canary-in-app-log"
grep -q "$canary_path" "$work/caddy.out" && fail "canary-in-caddy-log"
ok "canary-log-privacy"

# --- Malformed request straight at the app (published port): 400, no echo -
canary_req="oap033b-malformed-req"
cat >"$work/probe_malformed.py" <<'PY'
import socket
import sys

port = int(sys.argv[1])
canary = sys.argv[2]
sock = socket.create_connection(("127.0.0.1", port), timeout=5)
sock.settimeout(5)
sock.sendall(f"GET\x00{canary} /health/live HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n".encode())
buf = b""
while b"\r\n\r\n" not in buf:
    chunk = sock.recv(8192)
    if not chunk:
        break
    buf += chunk
sock.close()
status = buf.split(b"\r\n", 1)[0].split(b" ", 2)[1].decode("latin-1")
body = buf.split(b"\r\n\r\n", 1)[1] if b"\r\n\r\n" in buf else b""
print(status)
print("canary-in-body" if canary.encode() in body else "clean-body")
PY
chmod 600 "$work/probe_malformed.py"
malformed_out="$(python3 "$work/probe_malformed.py" "$app_port" "$canary_req" \
  2>/dev/null)" || fail "malformed-probe"
[ "$(echo "$malformed_out" | head -n 1)" = "400" ] || fail "malformed-400"
echo "$malformed_out" | grep -q 'clean-body' || fail "malformed-raw-echo"
sleep 1
malformed_logs="$(docker logs "$app_cid" 2>&1)"
echo "$malformed_logs" | grep -q "$canary_req" && fail "malformed-in-app-log"
ok "malformed-request-safe"

# --- Safe Gunicorn logger is live: JSON categories, never raw lines --------
logger_logs="$(docker logs "$app_cid" 2>&1)"
echo "$logger_logs" | grep -q '"category":"access"' || fail "gunicorn-access-format"
echo "$logger_logs" | grep -q '"category":"invalid-request"' \
  || fail "gunicorn-invalid-request-format"
ok "gunicorn-logger-live"

# --- Direct host -> app (published port, no proxy headers): 301 only ------
direct_status="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 \
  "http://127.0.0.1:${app_port}/health/live")"
[ "$direct_status" = "301" ] || fail "direct-plain-http-redirect"
curl -sS -D - -o /dev/null --max-time 10 "http://127.0.0.1:${app_port}/health/live" \
  | grep -qi '^location: https://' || fail "direct-redirect-location"
ok "direct-redirect"

# Clean up body fixtures before the final marker.
rm -f "$work/bigbody" "$work/formcap" "$work/midbody" "$work/body-a" \
  "$work/body-b" "$work/body-c" "$work/body-d1" "$work/body-e" \
  "$work/curl-csrf.conf" "$work/login-post.data" "$work/token-post.data"

printf 'https-boundary=ok\n'
