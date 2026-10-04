#!/usr/bin/env bash
# Real-HTTPS trust-boundary qualification (OAP 033-a).
#
# Runs an owned, disposable, loopback-only real TLS edge: Caddy (pinned
# v2.11.6) in front of the real Gunicorn/Django production stack, with a
# synthetic short-lived certificate and explicit per-client CA trust
# (curl --cacert). No public DNS, no ACME, no OS trust-store changes.
#
# Ownership contract (SAR-031, STRATEGIC 033-a safety recovery):
# - Every file, process and container belongs to THIS run: a fresh mktemp
#   work directory, a fresh source copy (with Git metadata for the
#   ignore-boundary fixture), and uniquely named PostgreSQL 17
#   container/volume. Existing resources are never adopted, terminated,
#   dropped or migrated: a name collision is a refusal, not an adoption.
# - Nothing is inherited: DATABASE_URL/TEST_DATABASE_URL and the
#   repository .env are never loaded. The explicit synthetic DATABASE_URL
#   is passed to EVERY migration/seed/check invocation.
# - The PostgreSQL container publishes a kernel-assigned loopback port
#   only; Caddy binds 127.0.0.1 on a kernel-assigned port with admin off
#   and automatic HTTP/ACME listeners disabled; every app process runs in
#   its own session and is terminated, force-killed, reaped and
#   orphan-audited, including on failure.
# - Secret material (database/user passwords, secret keys, peppers) is
#   generated into 0600 work files or passed via environment, never
#   printed and never placed on a command line.
#
# Exit codes:
# - 0: all checks passed (prints https-boundary=ok)
# - 1: a check failed, prerequisites collided, or cleanup was incomplete
# - 42: prerequisites not met (Caddy unavailable or not v2.11.6,
#   openssl/curl/docker/python3 missing) - callers may skip
set -Eeuo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Never inherit product database or settings configuration.
unset DATABASE_URL TEST_DATABASE_URL DJANGO_SETTINGS_MODULE SLAIF_TRUSTED_PROXY_PEERS 2>/dev/null || true

CADDY_VERSION="v2.11.6"
PG_IMAGE="postgres:17@sha256:d13db94ae661d517c5ed57c509a578d5ea64aae639871ba25294f4f42d83de28"
HOSTNAME_SYNTHETIC="slaif-boundary.test"
# Server-side (incoming) deadlines for this qualification run. The shipped
# deploy/Caddyfile.example relies on Caddy's built-in server defaults
# (read_header_timeout 60s, read/write idle 60s, idle 5 min; see
# docs/deployment.md section 8); this run pins tighter values so each
# deadline is actually exercised within a bounded test budget.
# Server-level (Caddyfile `servers { timeouts { ... } }`) deadlines for
# this qualification run, chosen tight so each deadline is exercised
# within a bounded test budget. The shipped example uses looser values
# (deploy/Caddyfile.example). v2.11.6: only the server-level deadlines
# are observed to take effect on stalled body reads; the route-level
# `timeouts` directive's read deadline was observed NOT to fire.
READ_HEADER_TIMEOUT_S=5
READ_BODY_IDLE_S=3
IDLE_TIMEOUT_S=10
READ_HEADER_TIMEOUT_NS=$((READ_HEADER_TIMEOUT_S * 1000000000))
READ_BODY_IDLE_NS=$((READ_BODY_IDLE_S * 1000000000))
IDLE_TIMEOUT_NS=$((IDLE_TIMEOUT_S * 1000000000))
CADDY_BODY_MAX="10MB"
# Must stay strictly below CADDY_BODY_MAX (see Caddyfile.example).
CADDY_REQ_BUFFERS="1MB"

work=""
container=""
volume=""
pg_port=""
gunicorn_port=""
dead_port=""
caddy_port=""
pg_password_file=""
user_password_file=""
proc_gunicorn=""
proc_gunicorn_dead=""
proc_caddy=""
cleanup_incomplete=0
container_created=0
volume_created=0

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
  # Bounded terminate/kill/reap of an owned session leader ($1, pid).
  local pid="$1" i
  [ -n "$pid" ] || return 0
  if ! kill -0 "$pid" 2>/dev/null; then
    wait "$pid" 2>/dev/null || true
    return 0
  fi
  kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
  for i in $(seq 1 20); do
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.5
  done
  if kill -0 "$pid" 2>/dev/null; then
    kill -KILL -- "-$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
  fi
  wait "$pid" 2>/dev/null || true
}

orphan_count() {
  # Count live processes whose cmdline carries the bind marker ($1).
  local marker="$1" n=0 d
  for d in /proc/[0-9]*; do
    local pid="${d#/proc/}"
    if [ "$pid" = "$$" ]; then
      continue
    fi
    if ( tr '\0' ' ' <"$d/cmdline" ) 2>/dev/null | grep -qF -- "$marker"; then
      n=$((n + 1))
    fi
  done
  printf '%s\n' "$n"
}

cleanup() {
  local status=$?
  set +u
  kill_session "$proc_gunicorn"
  kill_session "$proc_gunicorn_dead"
  kill_session "$proc_caddy"
  if [ "$container_created" = "1" ] && [ -n "$container" ]; then
    docker rm -f "$container" >/dev/null 2>&1 || true
    if docker inspect "$container" >/dev/null 2>&1; then
      log "cleanup=incomplete container=$container still present"
      cleanup_incomplete=1
    fi
  fi
  if [ "$volume_created" = "1" ] && [ -n "$volume" ]; then
    docker volume rm "$volume" >/dev/null 2>&1 || true
    if docker volume inspect "$volume" >/dev/null 2>&1; then
      log "cleanup=incomplete volume=$volume still present"
      cleanup_incomplete=1
    fi
  fi
  if [ -n "$work" ]; then
    rm -rf "$work"
  fi
  local orphans
  if [ -n "$gunicorn_port" ]; then
    orphans="$(orphan_count "--bind 127.0.0.1:${gunicorn_port}")"
    if [ "$orphans" != "0" ]; then
      log "cleanup=incomplete orphans=${orphans} (gunicorn)"
      cleanup_incomplete=1
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
caddy_bin="${SLAIF033A_BOUNDARY_CADDY:-$(command -v caddy || true)}"
if [ -z "$caddy_bin" ]; then
  skip "caddy-missing"
fi
caddy_version="$("$caddy_bin" version | head -n 1)"
case "$caddy_version" in
  "$CADDY_VERSION"*) ;;
  *) skip "caddy-version-$caddy_version" ;;
esac
command -v openssl >/dev/null 2>&1 || skip "openssl-missing"
command -v curl >/dev/null 2>&1 || skip "curl-missing"
command -v docker >/dev/null 2>&1 || skip "docker-missing"
command -v python3 >/dev/null 2>&1 || skip "python3-missing"

work="$(mktemp -d "${TMPDIR:-/tmp}/slaif033a-boundary.XXXXXX")" || fail "workdir"

# Fresh owned source copy (with Git metadata for the ignore-boundary
# fixture). The rehearsal never writes into the valuable checkout.
cp -a "$repo_root" "$work/src" || fail "src-copy"
umask 077

# ---------------------------------------------------------------------------
# Synthetic short-lived certificate (owned, private to this run)
# ---------------------------------------------------------------------------
openssl req -x509 -newkey rsa:2048 -sha256 -nodes -days 1 \
  -keyout "$work/key.pem" -out "$work/cert.pem" \
  -subj "/CN=${HOSTNAME_SYNTHETIC}" \
  -addext "subjectAltName=DNS:${HOSTNAME_SYNTHETIC}" >/dev/null 2>&1 \
  || fail "cert-gen"

# ---------------------------------------------------------------------------
# Owned PostgreSQL 17 (unique name; collisions are refused, not adopted)
# ---------------------------------------------------------------------------
rand_hex="$(openssl rand -hex 4)"
container="${SLAIF033A_BOUNDARY_CONTAINER:-slaif033a-bdb-$$-${rand_hex}}"
volume="${SLAIF033A_BOUNDARY_VOLUME:-slaif033a-bvol-$$-${rand_hex}}"
if docker inspect "$container" >/dev/null 2>&1; then
  fail "foreign-container-$container"
fi
if docker volume inspect "$volume" >/dev/null 2>&1; then
  fail "foreign-volume-$volume"
fi

pg_password_file="$work/pg_password"
if [ -n "${SLAIF033A_BOUNDARY_DB_PASSWORD:-}" ]; then
  printf '%s' "$SLAIF033A_BOUNDARY_DB_PASSWORD" >"$pg_password_file"
else
  openssl rand -base64 48 | tr -d '=+/\n' | head -c 32 >"$pg_password_file"
fi
chmod 600 "$pg_password_file"

pg_port="$(free_port)" || fail "pg-port"
# Ownership begins at the creation attempt: after the foreign-name
# refusals above, only this run can create these names, so cleanup may
# remove them; on a refusal the flags stay 0 and the names are foreign.
container_created=1
volume_created=1
if ! docker run -d --name "$container" \
  -v "$volume:/var/lib/postgresql/data" \
  -v "$pg_password_file:/run/secrets/postgres_password:ro" \
  -e POSTGRES_DB=slaif_reservation \
  -e POSTGRES_USER=slaif \
  -e POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password \
  -p "127.0.0.1:${pg_port}:5432" \
  "$PG_IMAGE" >/dev/null; then
  fail "pg-create"
fi
pg_ready=0
for _ in $(seq 1 90); do
  if docker exec "$container" pg_isready -U slaif -d slaif_reservation >/dev/null 2>&1; then
    pg_ready=1
    break
  fi
  sleep 1
done
[ "$pg_ready" = "1" ] || fail "pg-ready"
ok "owned-pg"

db_password="$(cat "$pg_password_file")"
db_url="postgres://slaif:${db_password}@127.0.0.1:${pg_port}/slaif_reservation"

# ---------------------------------------------------------------------------
# Application dependencies, statics, migrations, seed (owned copy only;
# every invocation gets the explicit synthetic DATABASE_URL)
# ---------------------------------------------------------------------------
(
  cd "$work/src"
  uv sync --locked
) >/dev/null 2>&1 || fail "uv-sync"

(
  cd "$work/src"
  env DJANGO_SETTINGS_MODULE=slaif_reservation.config.settings.local \
    uv run python manage.py collectstatic --no-input
) >/dev/null 2>&1 || fail "collectstatic"

secret_key_file="$work/django_secret_key"
openssl rand -base64 48 | tr -d '=+/\n' | head -c 48 >"$secret_key_file"
pepper_file="$work/token_pepper"
openssl rand -base64 48 | tr -d '=+/\n' | head -c 48 >"$pepper_file"

(
  cd "$work/src"
  env DJANGO_SETTINGS_MODULE=slaif_reservation.config.settings.production \
    DATABASE_URL="$db_url" \
    SLAIF_DJANGO_SECRET_KEY="$(cat "$secret_key_file")" \
    SLAIF_API_TOKEN_PEPPER="$(cat "$pepper_file")" \
    SLAIF_ALLOWED_HOSTS="${HOSTNAME_SYNTHETIC},127.0.0.1" \
    SLAIF_CSRF_TRUSTED_ORIGINS="https://${HOSTNAME_SYNTHETIC}" \
    SLAIF_TRUSTED_PROXY_PEERS=127.0.0.1 \
    uv run python manage.py migrate --noinput
) >/dev/null 2>&1 || fail "db-migrate"

user_password_file="$work/user_password"
openssl rand -base64 24 | tr -d '=+/\n' | head -c 24 >"$user_password_file"
(
  cd "$work/src"
  env DJANGO_SETTINGS_MODULE=slaif_reservation.config.settings.production \
    DATABASE_URL="$db_url" \
    SLAIF_DJANGO_SECRET_KEY="$(cat "$secret_key_file")" \
    SLAIF_API_TOKEN_PEPPER="$(cat "$pepper_file")" \
    SLAIF_ALLOWED_HOSTS="${HOSTNAME_SYNTHETIC},127.0.0.1" \
    SLAIF_CSRF_TRUSTED_ORIGINS="https://${HOSTNAME_SYNTHETIC}" \
    SLAIF_TRUSTED_PROXY_PEERS=127.0.0.1 \
    BOUNDARY_USER_EMAIL="boundary@example.test" \
    BOUNDARY_USER_PASSWORD="$(cat "$user_password_file")" \
    uv run python manage.py shell -c '
import os

from django.contrib.auth import get_user_model

User = get_user_model()
User.objects.create_user(
    email=os.environ["BOUNDARY_USER_EMAIL"],
    password=os.environ["BOUNDARY_USER_PASSWORD"],
)
'
) >/dev/null 2>&1 || fail "db-create-user"
ok "app-provisioned"

# ---------------------------------------------------------------------------
# Gunicorn instances (production settings, synthetic env, owned ports)
# ---------------------------------------------------------------------------
gunicorn_port="$(free_port)" || fail "app-port"
dead_port="$(free_port)" || fail "dead-port"
caddy_port="$(free_port)" || fail "caddy-port"

python_v="$work/src/.venv/bin/python"
[ -x "$python_v" ] || fail "venv-missing"

# The shipped production command line (Dockerfile CMD), without its bind.
mapfile -t gunicorn_cmd < <(
  python3 - "$repo_root/Dockerfile" <<'PY'
import json
import sys

line = [l for l in open(sys.argv[1], encoding="utf-8") if l.strip().startswith("CMD [")][0]
tokens = json.loads(line.strip()[len("CMD "):])
assert tokens[0] == "gunicorn"
assert tokens[1] == "slaif_reservation.config.wsgi:application"
out = []
skip = False
for token in tokens[2:]:
    if skip:
        skip = False
        continue
    if token == "--bind":
        skip = True
        continue
    out.append(token)
print("\n".join(out))
PY
)

gunicorn_env=(
  "DJANGO_SETTINGS_MODULE=slaif_reservation.config.settings.production"
  "DATABASE_URL=$db_url"
  "SLAIF_DJANGO_SECRET_KEY=$(cat "$secret_key_file")"
  "SLAIF_ALLOWED_HOSTS=${HOSTNAME_SYNTHETIC},127.0.0.1"
  "SLAIF_CSRF_TRUSTED_ORIGINS=https://${HOSTNAME_SYNTHETIC}"
  "SLAIF_TRUSTED_PROXY_PEERS=127.0.0.1"
  "SLAIF_API_TOKEN_PEPPER=$(cat "$pepper_file")"
  "PYTHONPATH=$work/src/src"
  "PYTHONUNBUFFERED=1"
  "PATH=${PATH:-/usr/bin:/bin}"
)

env "${gunicorn_env[@]}" setsid "$python_v" -m gunicorn \
  slaif_reservation.config.wsgi:application \
  --bind "127.0.0.1:${gunicorn_port}" \
  "${gunicorn_cmd[@]}" \
  --access-logfile - --error-logfile - \
  >"$work/gunicorn.log" 2>&1 &
proc_gunicorn=$!

# Dead-DB instance: liveness/readiness without any reachable database.
env "${gunicorn_env[@]/#DATABASE_URL=*/DATABASE_URL=postgres://slaif:slaif@127.0.0.1:1/slaif_reservation}" \
  setsid "$python_v" -m gunicorn \
  slaif_reservation.config.wsgi:application \
  --bind "127.0.0.1:${dead_port}" \
  --workers 1 --threads 2 --keep-alive 5 --timeout 30 \
  --forwarded-allow-ips 127.0.0.1,::1 \
  --header-map drop \
  --logger-class slaif_reservation.config.gunicorn.SlaifGunicornLogger \
  >"$work/gunicorn-dead.log" 2>&1 &
proc_gunicorn_dead=$!

app_ready=0
for _ in $(seq 1 60); do
  if curl -sS -o /dev/null -w '%{http_code}' --max-time 3 \
    -H 'X-Forwarded-Proto: https' "http://127.0.0.1:${gunicorn_port}/health/live" 2>/dev/null | grep -q '^200$'; then
    app_ready=1
    break
  fi
  sleep 1
done
[ "$app_ready" = "1" ] || fail "app-ready"
ok "app-up"

# ---------------------------------------------------------------------------
# Caddy edge (derived JSON: the shipped contract's handlers plus explicit
# loopback listen and bounded incoming deadlines)
# ---------------------------------------------------------------------------
cat >"$work/Caddyfile" <<EOF
{
	admin off
	auto_https off
	servers {
		timeouts {
			read_header ${READ_HEADER_TIMEOUT_S}s
			read_body_idle ${READ_BODY_IDLE_S}s
			idle ${IDLE_TIMEOUT_S}s
		}
	}
}
https://${HOSTNAME_SYNTHETIC}:${caddy_port} {
	tls ${work}/cert.pem ${work}/key.pem
	header {
		-Server
	}
	request_body {
		max_size ${CADDY_BODY_MAX}
	}
	reverse_proxy 127.0.0.1:${gunicorn_port} {
		header_up X-Forwarded-Proto {scheme}
		header_up X-Forwarded-For {remote_host}
		request_buffers ${CADDY_REQ_BUFFERS}
		transport http {
			dial_timeout 10s
			response_header_timeout 30s
			read_timeout 60s
			write_timeout 60s
			keepalive 3s
		}
	}
}
EOF
"$caddy_bin" adapt --config "$work/Caddyfile" >"$work/adapted.json" \
  2>"$work/adapt-warnings.log" || fail "caddy-adapt"
if ! python3 - "$work/adapted.json" "$work/caddy.json" "$caddy_port" \
  "$READ_HEADER_TIMEOUT_NS" "$READ_BODY_IDLE_NS" "$IDLE_TIMEOUT_NS" <<'PY'
import json
import sys

raw_path, out_path, port, rht_ns, rbi_ns, idle_ns = sys.argv[1:7]
raw = open(raw_path, encoding="utf-8").read()
decoder = json.JSONDecoder()
docs = []
i = 0
while i < len(raw):
    while i < len(raw) and raw[i] in " \t\r\n":
        i += 1
    if i >= len(raw):
        break
    try:
        obj, j = decoder.raw_decode(raw, i)
    except json.JSONDecodeError:
        break
    docs.append(obj)
    i = j
http_docs = [d for d in docs if "http" in d.get("apps", {})]
assert http_docs, "no http app in adapted Caddy config"
servers = http_docs[0]["apps"]["http"]["servers"]
assert len(servers) == 1, f"expected one server, got {len(servers)}"
server = next(iter(servers.values()))
# The incoming deadlines must have come from the Caddyfile
# servers{timeouts} block (the only observed-effective mechanism in
# v2.11.6); fail loudly if a Caddy behavior change dropped them.
assert server.get("read_header_timeout") == int(rht_ns), (
    "server read_header_timeout missing or changed"
)
assert server.get("read_idle_timeout") == int(rbi_ns), (
    "server read_idle_timeout missing or changed"
)
assert server.get("idle_timeout") == int(idle_ns), (
    "server idle_timeout missing or changed"
)
server["listen"] = [f"127.0.0.1:{port}"]
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(http_docs[0], fh)
PY
then
  fail "caddy-inject"
fi
"$caddy_bin" validate --config "$work/caddy.json" >/dev/null 2>&1 \
  || fail "caddy-validate"
env PATH="${PATH:-/usr/bin:/bin}" setsid "$caddy_bin" run --config "$work/caddy.json" \
  >"$work/caddy.log" 2>&1 &
proc_caddy=$!

base="https://${HOSTNAME_SYNTHETIC}:${caddy_port}"
resolve="${HOSTNAME_SYNTHETIC}:${caddy_port}:127.0.0.1"
https_get() {
  curl -sS --cacert "$work/cert.pem" --resolve "$resolve" --max-time 15 "$@"
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
# Checks
# ---------------------------------------------------------------------------
live_body="$(https_get "$base/health/live")"
[ "$(https_get -o /dev/null -w '%{http_code}' "$base/health/live")" = "200" ] \
  || fail "tls-health-status"
echo "$live_body" | grep -Eq '"status": *"ok"' || fail "tls-health-body"
ok "tls-health"

if curl -sS --resolve "$resolve" --max-time 10 -o /dev/null "$base/health/live" 2>/dev/null; then
  fail "tls-accepted-without-ca"
fi
ok "tls-requires-owned-ca"

if curl -sS --max-time 10 -o /dev/null "http://${HOSTNAME_SYNTHETIC}:${caddy_port}/health/live" 2>/dev/null; then
  fail "plain-http-on-tls-port"
fi
ok "tls-port-rejects-plain-http"

headers="$(https_get -D - -o /dev/null "$base/health/live")"
echo "$headers" | grep -qi '^x-content-type-options: nosniff' || fail "header-nosniff"
echo "$headers" | grep -qi '^referrer-policy: strict-origin-when-cross-origin' \
  || fail "header-referrer-policy"
echo "$headers" | grep -qi '^x-frame-options: deny' || fail "header-xfo"
echo "$headers" | grep -qi '^server:' && fail "header-server-exposed"
ok "response-headers"

# One-hop forwarding from the real connection: a client-sent
# X-Forwarded-Proto must be overwritten by the edge (https), never honored.
spoof_status="$(https_get -H 'X-Forwarded-Proto: http' -o /dev/null -w '%{http_code}' \
  "$base/health/live")"
[ "$spoof_status" = "200" ] || fail "edge-xfp-overwrite"
# An ambiguous client XFF chain must be replaced by the edge's single
# real-client value: the app would log a proxy-ambiguity warning otherwise.
chain_status="$(https_get -H 'X-Forwarded-For: 203.0.113.9, 203.0.113.10' \
  -o /dev/null -w '%{http_code}' "$base/health/live")"
[ "$chain_status" = "200" ] || fail "edge-xff-overwrite"
grep -q 'proxy-ambiguity' "$work/gunicorn.log" && fail "edge-xff-ambiguity-leaked"
# Underscore wire variant: canonicalized and overwritten by the edge.
underscore_status="$(https_get -H 'X_Forwarded_Proto: http' -o /dev/null -w '%{http_code}' \
  "$base/health/live")"
[ "$underscore_status" = "200" ] || fail "edge-underscore-header"
ok "forwarding-overwrite"

# Login flow under real TLS: Secure cookies and a working CSRF round-trip.
login_status="$(https_get -c "$work/cookies" -o "$work/login-page.html" -w '%{http_code}' \
  "$base/login/")"
[ "$login_status" = "200" ] || fail "login-page"
csrf_token="$(sed -n 's/.*name="csrfmiddlewaretoken" value="\([^"]*\)".*/\1/p' \
  "$work/login-page.html" | head -n 1)"
[ -n "$csrf_token" ] || fail "login-csrf-token"
# curl's jar format: host<TAB>subdomains<TAB>path<TAB>secure<TAB>expiry<TAB>name<TAB>value
awk -F'\t' '$6 == "csrftoken" { print $4 }' "$work/cookies" | grep -qx 'TRUE' \
  || fail "csrf-cookie-secure"
user_email="boundary@example.test"
user_password="$(cat "$user_password_file")"
{
  printf 'csrfmiddlewaretoken=%s\n' "$csrf_token"
  printf 'username=%s\n' "$user_email"
  printf 'password=%s\n' "$user_password"
} | python3 -c 'import sys, urllib.parse
lines = dict(l.strip().split("=", 1) for l in sys.stdin if l.strip())
print(urllib.parse.urlencode(lines))' >"$work/login-post.data"
login_resp="$(https_get -H "Origin: https://${HOSTNAME_SYNTHETIC}" \
  -b "$work/cookies" -c "$work/cookies" -D "$work/login-post-headers" \
  -o /dev/null -w '%{http_code}' \
  --data @"$work/login-post.data" \
  "$base/login/")" || fail "login-post"
[ "$login_resp" = "302" ] || fail "login-success"
grep -i '^set-cookie: sessionid=' "$work/login-post-headers" | grep -q 'Secure' \
  || fail "session-cookie-secure"
ok "login-secure"

# Layered body-size contract (docs/deployment.md section 8):
#  (a) form content types are rejected by the app's own
#      DATA_UPLOAD cap (400, Content-Length pre-check, body unread);
#  (b) multipart file uploads are read by the app, so the edge's
#      10MB request_body cap rejects them with 413;
#  (c) bodies the app never reads (e.g. octet-stream) are ignored by
#      the app; the edge's memory stays bounded by the 1MB request
#      buffer and the pool remains responsive.
# A fresh CSRF round-trip per check keeps the material out of argv.
head -c 11534336 /dev/zero | tr '\0' 'x' >"$work/bigbody"
chmod 600 "$work/bigbody"

csrf_fetch() {
  curl -sS --cacert "$work/cert.pem" --resolve "$resolve" --max-time 15 \
    -c "$1" -o "$2" "$base/login/" >/dev/null 2>&1
}
csrf_token_to() {
  sed -n 's/.*name="csrfmiddlewaretoken" value="\([^"]*\)".*/\1/p' "$1" | head -n 1 >"$2"
  chmod 600 "$2"
}

jar_a="$work/jar-bodycap-a"
csrf_fetch "$jar_a" "$work/page-bodycap-a" || fail "body-cap-a-csrf"
csrf_token_to "$work/page-bodycap-a" "$work/token-bodycap-a"
[ -s "$work/token-bodycap-a" ] || fail "body-cap-a-token"
python3 - "$work/token-bodycap-a" "$work/bigbody" "$work/bodycap-a.body" <<'PYA'
import sys

token = open(sys.argv[1], encoding="utf-8").read().strip()
payload = open(sys.argv[2], "rb").read()
with open(sys.argv[3], "wb") as fh:
    fh.write(b"csrfmiddlewaretoken=" + token.encode())
    fh.write(b"&payload=" + payload)
PYA
app_cap_status="$(https_get -b "$jar_a" -c "$jar_a" \
  -H "Origin: https://${HOSTNAME_SYNTHETIC}" \
  -o /dev/null -w '%{http_code}' -X POST \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-binary @"$work/bodycap-a.body" "$base/login/" 2>/dev/null || true)"
[ "$app_cap_status" = "400" ] || fail "body-cap-app observed=${app_cap_status:-none}"
ok "body-cap-app"

jar_b="$work/jar-bodycap-b"
csrf_fetch "$jar_b" "$work/page-bodycap-b" || fail "body-cap-b-csrf"
csrf_token_to "$work/page-bodycap-b" "$work/token-bodycap-b"
[ -s "$work/token-bodycap-b" ] || fail "body-cap-b-token"
python3 - "$work/token-bodycap-b" "$work/bigbody" "$work/bodycap-b.body" <<'PYB'
import sys

token = open(sys.argv[1], encoding="utf-8").read().strip()
data = open(sys.argv[2], "rb").read()
boundary = "----slaif033a-bodycap-boundary"
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
PYB
edge_cap_status="$(https_get -b "$jar_b" -c "$jar_b" \
  -H "Origin: https://${HOSTNAME_SYNTHETIC}" \
  -o /dev/null -w '%{http_code}' -X POST \
  -H 'Content-Type: multipart/form-data; boundary=----slaif033a-bodycap-boundary' \
  --data-binary @"$work/bodycap-b.body" "$base/login/" 2>/dev/null || true)"
[ "$edge_cap_status" = "413" ] || fail "body-cap-edge observed=${edge_cap_status:-none}"
ok "body-cap-edge"

jar_c="$work/jar-bodycap-c"
csrf_fetch "$jar_c" "$work/page-bodycap-c" || fail "body-cap-c-csrf"
csrf_token_to "$work/page-bodycap-c" "$work/token-bodycap-c"
[ -s "$work/token-bodycap-c" ] || fail "body-cap-c-token"
{
  printf 'header = "X-CSRFToken: %s"\n' "$(cat "$work/token-bodycap-c")"
} >"$work/curl-bodycap-c"
chmod 600 "$work/curl-bodycap-c"
unread_status="$(https_get -b "$jar_c" -c "$jar_c" -K "$work/curl-bodycap-c" \
  -H "Origin: https://${HOSTNAME_SYNTHETIC}" \
  -o /dev/null -w '%{http_code}' -X POST \
  -H 'Content-Type: application/octet-stream' \
  --data-binary @"$work/bigbody" "$base/login/" 2>/dev/null || true)"
[ "$unread_status" = "200" ] || fail "body-cap-unread observed=${unread_status:-none}"
pool_status="$(https_get -o /dev/null -w '%{http_code}' "$base/health/live")"
[ "$pool_status" = "200" ] || fail "body-cap-pool observed=${pool_status:-none}"
rm -f "$work/bigbody" "$work/bodycap-a.body" "$work/bodycap-b.body"
ok "body-cap-unread"

# Bounded incoming deadlines (this run's explicit values): a stalled body
# read is cut by the route read_timeout, a slow header read by the server
# read_header_timeout, and an idle connection closes after idle_timeout -
# while /health/live stays prompt throughout.
if ! python3 - "$caddy_port" "$HOSTNAME_SYNTHETIC" "$READ_BODY_IDLE_S" "$work/cert.pem" <<'PY'
import socket
import ssl
import sys
import threading
import time

caddy_port, host, stall_s, cert = int(sys.argv[1]), sys.argv[2], float(sys.argv[3]), sys.argv[4]

def tls_conn():
    raw = socket.create_connection(("127.0.0.1", caddy_port), timeout=5)
    ctx = ssl.create_default_context(cafile=cert)
    return ctx.wrap_socket(raw, server_hostname=host)

def health_prompt() -> None:
    sock = tls_conn()
    try:
        sock.settimeout(2.0)
        sock.sendall(
            f"GET /health/live HTTP/1.1\r\nHost: {host}:{caddy_port}\r\n"
            "X-Forwarded-Proto: https\r\nConnection: close\r\n\r\n".encode()
        )
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
        assert buf.startswith(b"HTTP/1.1 200"), "health not prompt during body stall"
    finally:
        sock.close()

stall_result = {}

def probe_slow_body() -> None:
    # Content-Length 5MB (under the 10MB cap) with only 1KB actually sent:
    # the stalled body read must be cut by the server read_body_idle deadline.
    sock = tls_conn()
    head = (
        f"POST /health/live HTTP/1.1\r\n"
        f"Host: {host}:{caddy_port}\r\n"
        "X-Forwarded-Proto: https\r\n"
        "Content-Type: application/octet-stream\r\n"
        "Content-Length: 5242880\r\n"
        "\r\n"
    )
    try:
        sock.settimeout(0.5)
        sock.sendall(head.encode() + b"x" * 1024)
        started = time.monotonic()
        outcome = "hung"
        while time.monotonic() - started < 20:
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
                outcome = "error-response"
                break
        stall_result["outcome"] = outcome
        stall_result["elapsed"] = time.monotonic() - started
    except OSError:
        stall_result["outcome"] = "refused"
        stall_result["elapsed"] = 0.0
    finally:
        sock.close()

threading.Thread(target=probe_slow_body, daemon=True).start()
deadline = time.monotonic() + 30.0
health_prompt()
while "outcome" not in stall_result:
    if time.monotonic() > deadline:
        raise AssertionError("stalled body read never bounded")
    time.sleep(0.5)
health_prompt()
outcome = stall_result["outcome"]
elapsed = stall_result["elapsed"]
assert outcome in ("eof", "closed", "error-response"), (
    f"stalled body read not bounded: {outcome}"
)
assert elapsed <= stall_s + 8.0, f"stalled body read took too long: {elapsed:.1f}s"
PY
then
  fail "body-stall-bounded"
fi
ok "body-stall-bounded"

if ! python3 - "$caddy_port" "$READ_HEADER_TIMEOUT_S" "$work/cert.pem" <<'PY'
import socket
import ssl
import sys
import threading
import time

caddy_port, rht_s, cert = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
host = "slaif-boundary.test"

def tls_conn():
    raw = socket.create_connection(("127.0.0.1", caddy_port), timeout=5)
    ctx = ssl.create_default_context(cafile=cert)
    return ctx.wrap_socket(raw, server_hostname=host)

def slow_header():
    sock = tls_conn()
    try:
        sock.sendall(
            f"GET /health/live HTTP/1.1\r\nHost: {host}\r\n".encode()
        )
        started = time.monotonic()
        while time.monotonic() - started < 20:
            try:
                chunk = sock.recv(4096)
            except socket.timeout:
                continue
            except OSError:
                return "closed", time.monotonic() - started
            if not chunk:
                return "eof", time.monotonic() - started
    finally:
        sock.close()
    return "hung", 20.0

def health_prompt():
    sock = tls_conn()
    try:
        sock.settimeout(2.0)
        sock.sendall(
            f"GET /health/live HTTP/1.1\r\nHost: {host}:{caddy_port}\r\n"
            f"X-Forwarded-Proto: https\r\nConnection: close\r\n\r\n".encode()
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

result = {}
def run_header():
    result["slow"] = slow_header()
threading.Thread(target=run_header, daemon=True).start()
time.sleep(1.0)
health_prompt()
for _ in range(40):
    if "slow" in result:
        break
    time.sleep(0.5)
assert "slow" in result, "slow-header probe incomplete"
outcome, elapsed = result["slow"]
assert outcome in ("eof", "closed"), f"slow headers not bounded: {outcome}"
assert elapsed <= rht_s + 3.0, f"slow-header cutoff too slow: {elapsed:.1f}s"
PY
then
   fail "slow-header-bounded"
fi
ok "slow-header-bounded"

if ! python3 - "$caddy_port" "$IDLE_TIMEOUT_S" "$work/cert.pem" <<'PY'
import socket
import ssl
import sys
import time

caddy_port, idle_s, cert = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
raw = socket.create_connection(("127.0.0.1", caddy_port), timeout=5)
ctx = ssl.create_default_context(cafile=cert)
sock = ctx.wrap_socket(raw, server_hostname="slaif-boundary.test")
sock.settimeout(30.0)
sock.sendall(
    f"GET /health/live HTTP/1.1\r\nHost: slaif-boundary.test:{caddy_port}\r\n"
    f"X-Forwarded-Proto: https\r\n\r\n".encode()
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
# Connection is now established and idle (keep-alive).
started = time.monotonic()
try:
    chunk = sock.recv(1)
    assert chunk == b"", f"expected clean EOF, got {len(chunk)} bytes"
except socket.timeout:
    raise AssertionError("idle connection not closed within bound")
finally:
    sock.close()
elapsed = time.monotonic() - started
bound_s = idle_s + 5.0
assert elapsed <= bound_s, f"idle connection held too long: {elapsed:.1f}s"
PY
then
   fail "idle-connection-closed"
fi
ok "idle-connection-closed"

# Canary path: 404, and the canary must not survive in any captured log.
canary_path="oap033a-boundary-canary"
canary_status="$(https_get -o /dev/null -w '%{http_code}' "$base/no-such/${canary_path}/")"
[ "$canary_status" = "404" ] || fail "canary-404"
sleep 1
grep -q "$canary_path" "$work/gunicorn.log" && fail "canary-in-gunicorn-log"
grep -q "$canary_path" "$work/caddy.log" && fail "canary-in-caddy-log"
ok "canary-log-privacy"

# Malformed request line straight at the app: 400, no raw echo, no log leak.
canary_req="oap033a-malformed-req"
malformed="$(python3 - "$gunicorn_port" "$canary_req" <<'PY'
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
)"
[ "$(echo "$malformed" | head -n 1)" = "400" ] || fail "malformed-400"
echo "$malformed" | grep -q 'clean-body' || fail "malformed-raw-echo"
sleep 1
grep -q "$canary_req" "$work/gunicorn.log" && fail "malformed-in-gunicorn-log"
ok "malformed-request-safe"

# The safe Gunicorn logger must be live: JSON categories, not raw lines.
https_get -o /dev/null "$base/health/live"
sleep 1
grep -q '"category":"access"' "$work/gunicorn.log" || fail "gunicorn-access-format"
grep -q '"category":"invalid-request"' "$work/gunicorn.log" \
  || fail "gunicorn-invalid-request-format"
ok "gunicorn-logger-live"

# Direct app edge without forwarding headers: plain transport, 301 only.
direct_status="$(curl -sS -o /dev/null -w '%{http_code}' \
  "http://127.0.0.1:${gunicorn_port}/health/live")"
[ "$direct_status" = "301" ] || fail "direct-plain-http-redirect"
curl -sS -D - -o /dev/null "http://127.0.0.1:${gunicorn_port}/health/live" \
  | grep -qi '^location: https://' || fail "direct-redirect-location"
ok "direct-redirect"

# Dead-DB instance: liveness stays 200, readiness is a bare 503.
dead_live="$(curl -sS -H 'X-Forwarded-Proto: https' "http://127.0.0.1:${dead_port}/health/live")"
[ "$(curl -sS -o /dev/null -w '%{http_code}' -H 'X-Forwarded-Proto: https' \
  "http://127.0.0.1:${dead_port}/health/live")" = "200" ] || fail "dead-db-liveness"
echo "$dead_live" | grep -Eq '"status": *"ok"' || fail "dead-db-liveness-body"
dead_ready_body="$(curl -sS -H 'X-Forwarded-Proto: https' "http://127.0.0.1:${dead_port}/health/ready")"
[ "$(curl -sS -o /dev/null -w '%{http_code}' -H 'X-Forwarded-Proto: https' \
  "http://127.0.0.1:${dead_port}/health/ready")" = "503" ] || fail "dead-db-ready-status"
echo "$dead_ready_body" | grep -Eq '"status": *"unavailable"' || fail "dead-db-ready-body"
echo "$dead_ready_body" | grep -qiE 'psycopg|operationalerror|connection|database' \
  && fail "dead-db-ready-details"
ok "dead-db-boundary"

printf 'https-boundary=ok\n'
