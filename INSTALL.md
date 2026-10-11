# INSTALL — Installation and Deployment

**Target:** an authenticated HTTPS pilot on a single Linux host. Keep the
application and database private behind an operator-owned reverse proxy.

This is the operator guide for SLAIF Asset Reservation. Docker/Compose is
the deployment path; the `uv` workflow is the development path. For the
shortest local evaluation, see [QUICKSTART.md](QUICKSTART.md). Deeper
configuration reference and rationale: [Deployment reference](docs/deployment.md). Operator
checklists and recovery procedures: [runbooks](docs/runbooks/).

**Contents:** [1. Supported deployment shape](#1-supported-deployment-shape) · [2. Prerequisites](#2-prerequisites) · [3. Fast local evaluation](#3-fast-local-evaluation-docker-loopback-only) · [4. Development installation](#4-development-installation-uv--development-path) · [5. Authenticated pilot deployment](#5-authenticated-pilot-docker-deployment-canonical-procedure) · [6. Rehearsal](#6-rehearsal-what-it-does-and-does-not-prove) · [7. Persistence](#7-persistence) · [8. Backup and restore](#8-backup-and-restore) · [9. Upgrades and rollback](#9-upgrading-to-a-new-reviewed-revision-manual-procedure) · [10. Shutdown and restart](#10-shutdown-and-restart) · [11. Security boundaries](#11-security-boundaries) · [12. Operating limits](#12-operating-limits) · [13. Documentation map](#13-documentation-map) · [14. Uninstall and data retention](#14-uninstall-and-data-retention) · [15. Troubleshooting](#15-troubleshooting)

**Testing on this computer?** Use [QUICKSTART.md](QUICKSTART.md).
**Need access from another computer or the Internet?** Use section 5 below.
Remote users connect to the HTTPS hostname, never directly to port 8000.

## 1. Supported deployment shape

```text
clients (browsers, API agents)
  -> HTTPS reverse proxy (Caddy or equivalent) on the host
    -> Django/Gunicorn container — published on 127.0.0.1 only
      -> PostgreSQL 17 container on the private Compose network
```

- The application is published on the host's loopback interface only
  (`127.0.0.1:${SLAIF_APP_HOST_PORT:-8000}`). This binding is intentional:
  all external access comes exclusively through the reverse proxy.
- PostgreSQL has no host port at all in the production-shaped example; it is
  reachable only from the private Compose network.
- The production-shaped image runs as non-root user `10001:10001` with a
  read-only root filesystem.
- The supported host is a single Linux host on **`x86_64` (amd64)**: the
  application runtime image is built from `python:3.13-slim` pinned to a
  `linux/amd64` digest in the `Dockerfile`, and the PostgreSQL service image
  is pinned to a `linux/amd64` digest in the Compose files. Other
  architectures are not supported or verified on the documented deployment
  path.
- The repository is a single-host Compose stack. There is no
  Kubernetes/Swarm/Helm/Terraform/Ansible path, no image registry, and no
  automated deployment.

The application container runs Gunicorn with the `gthread` worker pool —
3 workers, 8 threads per worker, 5 s keep-alive, 30 s worker timeout — in
every supported default (the `Dockerfile` `CMD`, the development Compose
app command, and the production example app command). The threaded pool
keeps `/health/live` and ordinary requests responsive while a handful of
slow or idle clients hold connections; under the legacy single-threaded
`sync` pool, three stalled clients can occupy all workers and time out
new requests. Worker sizing is a responsiveness baseline, not a load
guarantee: the service remains published on loopback only, and all
external access still comes exclusively through the HTTPS reverse proxy,
which must buffer client bodies and enforce its own read/idle timeouts.
See `docs/deployment.md` (section 5, "Gunicorn worker pool") for the full
rationale and the responsiveness regression.

## 2. Prerequisites

What this deployment actually requires:

- A Linux host (`x86_64`/amd64, see section 1).
- Docker Engine with Docker Compose v2.24.0 or later (the examples use
  [optional `env_file` entries](https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/#additional-information-1)).
- Git, curl, and Bash for the commands below.
- Outbound connectivity to pull `python:3.13-slim` (pinned by digest in the
  `Dockerfile`) and the PostgreSQL service image (pinned by digest in the
  Compose files).
- Persistent disk for the Compose `postgres-data` volume. All reservation
  state lives in that volume.
- For real HTTPS: a DNS name resolving to the host and a TLS plan (Caddy
  automatic TLS, or institutionally managed certificates).
- A protected secret store or host-only protected secret files for the
  values in sections 5.2 and 5.3.
- The database role that runs migrations must be able to create the
  `btree_gist` extension in the application database. The Compose defaults
  satisfy this: the `postgres:17` image grants the initial `POSTGRES_USER`
  role (default `slaif`) superuser rights.

## 3. Fast local evaluation (Docker, loopback only)

The shortest truthful Docker path to a running instance is
[QUICKSTART.md](QUICKSTART.md): the committed development `compose.yaml`
(loopback-only bindings, development settings and development secrets)
under a dedicated, unused evaluation Compose project, with deliberate
migrations, an optional fictitious demo import, and an interactive
first administrator. It is for local evaluation and development, not
long-running service deployment.

## 4. Development installation (uv — development path)

The developer workflow — Python 3.13 managed by `uv` with the committed
`uv.lock`, PostgreSQL 17 through the development Compose file, `.env`
handling, and the standard verification command set — is documented in
[CONTRIBUTING.md](CONTRIBUTING.md), with required test tooling and
evidence rules in [TESTING.md](TESTING.md). It is not the recommended
long-running service deployment; use the controlled operator procedure in
section 5 for a service.

## 5. Authenticated pilot Docker deployment (canonical procedure)

Before deployment, select a reviewed immutable commit with green checks and
current qualification/audit evidence, complete the local rehearsals (section 6),
and approve the real host, accounts, secrets, DNS/TLS and operating responsibilities.
Development checks and local rehearsal do not perform those real actions.

1. **Clone and checkout the reviewed commit.** The reviewed commit is
   operator-selected (reviewed and qualified, with green CI). The
   read prompt keeps it out of any committed command and requires the
   full commit, not a prefix:

   ```bash
   git clone https://github.com/ulfe-lmi/slaif-asset-reservation.git slaif-asset-reservation
   cd slaif-asset-reservation
   read -r -p "Reviewed commit SHA (full 40-character): " REVIEWED_SHA
   [[ "$REVIEWED_SHA" =~ ^[0-9a-f]{40}$ ]] || { echo "Not a full commit SHA." >&2; exit 1; }
   git checkout "$REVIEWED_SHA"
   ```

   **Choose and record the Compose project name before running any Compose command.**
   For a new service installation:

   ```bash
   SAR_COMPOSE_PROJECT=slaif-asset-reservation
   ```

   For an existing installation, set `SAR_COMPOSE_PROJECT` to its existing project
   name instead. Find it in the deployment record or the container's
   `com.docker.compose.project` label, and verify the database container's volume
   mount. Use the same value in every shell running the commands below. Do not
   switch an existing `slaif-test`, evaluation or other project to the new name:
   that selects a different `<project>_postgres-data` volume and can start an empty
   database. A rename requires a separate backed-up migration, explicit volume
   identity checks and verified proxy peers; never adopt or delete volumes by name.

2. **Prepare the application environment file.** If
   `deploy/env.production` already exists on this host, review and reuse
   it — do not overwrite it with the example. To create it fresh, set
   the restrictive umask and mode **before** real values are written:

   ```bash
   umask 077
   install -m 0600 deploy/env.production.example deploy/env.production
   ```

   Then replace every placeholder in the git-ignored `deploy/env.production`
   from a protected secret store — never commit it, and keep it mode
   `0600`:

   - `SLAIF_DJANGO_SECRET_KEY` (at least 32 bytes);
   - `SLAIF_ALLOWED_HOSTS` — **both** the approved service hostname
     (the service hostname served through the HTTPS proxy) **and**
     `127.0.0.1`. The service hostname serves browser/API traffic through
     the proxy; `127.0.0.1` is required because the Compose app
     healthcheck probes `http://127.0.0.1:8000/health/live` from inside
     the application container, and Django rejects a host not in
     `ALLOWED_HOSTS`. Omitting `127.0.0.1` leaves the app container
     permanently unhealthy. Entries are validated fail-closed at settings
     load: explicit bare hostnames, IPv4/IPv6 literals, or Django dotted
     subdomain wildcards (`.example.org`) only — schemes, ports, userinfo,
     whitespace, and malformed entries are rejected without echoing the
     configured value, and the bare `*` wildcard is unsafe and refused.
   - `SLAIF_CSRF_TRUSTED_ORIGINS` (the approved service hostname,
     `https://` origin);
   - `SLAIF_API_TOKEN_PEPPER` (at least 32 bytes, distinct from
     `SLAIF_DJANGO_SECRET_KEY`);
   - `DATABASE_URL` — the database password here **must match** the secret
     file from step 3.
   - `SLAIF_TRUSTED_PROXY_PEERS` — start with `127.0.0.1` for the
     in-container probe. After PostgreSQL creates the Compose network in
     step 6, discover and add the actual host-proxy socket peer before
     starting the application. Entries are explicit IP addresses or
     point-to-point networks (IPv4 `/31`, IPv6 `/127`); broad ranges are
     rejected.

   Do not weaken `SLAIF_SECURE_SSL_REDIRECT` or the trusted-peer list to
   make the healthcheck pass: the probe dials `127.0.0.1` from inside the
   application container and sends `X-Forwarded-Proto: https`, so
   `127.0.0.1` must be present in `SLAIF_TRUSTED_PROXY_PEERS` (and in
   `SLAIF_ALLOWED_HOSTS`, as above). The production settings no longer use
   a blanket `SECURE_PROXY_SSL_HEADER`: only the listed trusted peers may
   supply TLS/client-identity forwarding, and the reverse proxy must
   overwrite `X-Forwarded-Proto` / `X-Forwarded-For` from the real
   connection (step 12).

3. **Prepare the PostgreSQL secret file.** If it already exists, retain it and
   verify that it matches the existing database role and application URL. Do not
   rotate it as an installation step: changing the file does not change the
   password in an initialized PostgreSQL volume. For a new installation only:

   ```bash
   install -d -m 700 deploy/secrets
   umask 077
   test ! -e deploy/secrets/postgres_password || { echo "Existing secret: review and reuse it." >&2; exit 1; }
   head -c 32 /dev/urandom | base64 | tr -d '=+/\n' | head -c 32 \
     > deploy/secrets/postgres_password
   ```

   The file contains exactly one line: the database password, with no
   trailing newline. The same password is structurally required in TWO
   places: the `db` container reads `deploy/secrets/postgres_password` via
   `POSTGRES_PASSWORD_FILE`, and the app connects through `DATABASE_URL` in
   `deploy/env.production`. If the two do not match, the app cannot start.

4. **Build the image at the reviewed commit.** The production Compose
   example expects the tag `slaif-asset-reservation:pilot`, which
   is a mutable tag: build it at the reviewed commit, and keep a
   commit-addressable copy for application rollback.

   ```bash
   docker build --tag slaif-asset-reservation:pilot .
   docker tag slaif-asset-reservation:pilot \
     "slaif-asset-reservation:$(git rev-parse --short HEAD)"
   ```

   There is no release platform or registry; the image is built on the
   deployment host from the reviewed commit.

5. **Render and validate the configuration.** Use the quiet form — it
   exits non-zero on a broken configuration and prints nothing:

   ```bash
   docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml config --quiet
   ```

   Do not run plain `config` while real values are in place: it prints the
   fully resolved environment, including the `deploy/env.production`
   values (secret key, pepper, and the database password inside
   `DATABASE_URL`).

6. **Start PostgreSQL only.**

   ```bash
   docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml up -d db
   docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml ps
   ```

   Wait until the `db` service is healthy. Its private network now exists;
   inspect the network name and gateway without printing application secrets:

   ```bash
   SAR_DB_CONTAINER=$(docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml ps -q db)
   SAR_COMPOSE_NETWORK=$(docker inspect "$SAR_DB_CONTAINER" --format '{{range $name, $network := .NetworkSettings.Networks}}{{$name}}{{end}}')
   docker network inspect "$SAR_COMPOSE_NETWORK" --format '{{range .IPAM.Config}}{{.Gateway}}{{end}}'
   ```

   For the canonical host-side Caddy proxy dialing the published loopback port,
   the app normally observes this bridge gateway as its peer. Add that explicit
   IP to `SLAIF_TRUSTED_PROXY_PEERS` in the protected application environment,
   retaining `127.0.0.1` for the in-container probe. Verify the actual peer during
   the HTTPS checks; Docker forwarding behavior can vary. Do not trust the whole
   subnet or copy an address from another installation.

7. **Run migrations deliberately.**

   ```bash
   docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml run --rm app \
     python manage.py migrate --noinput
   ```

   This installs the `btree_gist` extension and the
   `reservation_no_overlap_per_asset` exclusion constraint.

   Then initialize the fresh-install default policy, deliberately and
   immediately after migrations:

   ```bash
   docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml run --rm app \
     python manage.py initialize_default_policy
   ```

   On a fresh database this creates the active global fallback policy
   `default` (step 9 documents its values). On a database that already
   has any policy row it is a no-op: no writes, no audit, no
   reactivation. Migrations and application startup never run it
   implicitly.

8. **Run the operational check.**

   ```bash
   docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml run --rm app \
     python manage.py operational_check
   ```

9. **Configure initial assets and policies.** Create your own verified inventory
   through administration. The bundled 14-asset inventory is entirely fictitious;
   the commands below are optional for a fresh evaluation database, not a real
   service inventory or an upgrade. [Bootstrap format](data/bootstrap/README.md). A fresh database already has the
   step 7 initializer's active global fallback policy `default` with these
   chosen explicit defaults: minimum duration 1 minute; maximum duration
   2880 minutes (48 hours / 2 days); booking horizon 7 days by reservation
   START; minimum lead 0; cancellation cutoff 0; purpose optional; no
   restricted operating-hour window; and, per principal across all assets
   and that principal's API tokens, up to 50 upcoming reservations, and a
   new booking requires fewer than 8 existing blocking records intersecting
   the proposed interval (8 or more existing intersecting records rejects
   it; the new record would be the 8th). This is a count of records
   intersecting the proposed interval, not a maximum simultaneous-occupancy
   sweep. Manual policy creation is no longer a
   prerequisite for a fresh install. Staff manage all policies through the
   existing audited services in the staff management UI at `/manage/`.
   Reservations resolve an active policy for the exact asset, its parent
   machine, or global; a missing or ambiguous policy fails closed.

   ```bash
   docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml run --rm app \
     python manage.py import_bootstrap_assets --input data/bootstrap/assets.yaml
   docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml run --rm app \
     python manage.py import_bootstrap_assets --input data/bootstrap/assets.yaml --apply
   ```

10. **Create the first administrator** (interactive; accounts are
    administrator-created; the account's email address is its login
    identifier).

    ```bash
    docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml run --rm app \
      python manage.py createsuperuser
    ```

    The command is interactive: it prompts for `Email`, then `Password`
    (entered twice to confirm).

11. **Start the application service.**

    ```bash
    docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml up -d app
    ```

12. **Configure the reverse proxy** from `deploy/Caddyfile.example`
    (qualified with Caddy v2.11.6): replace the placeholder hostname and
    replace or remove the placeholder email. The operator owns certificate
    provisioning: Caddy automatic HTTPS or institutionally managed certificates.
    Qualification uses synthetic certificates and does not provision public ACME. The
    example overwrites (never appends) `X-Forwarded-Proto` and
    `X-Forwarded-For` from the actual client connection, caps body size and
    read/idle time, drops the `Server` and `Via` identity headers, and
    applies its `Referrer-Policy` edge policy as a **deferred default**
    (Caddy `?` modifier) so stricter per-view policies — in particular the
    one-time token page's `no-referrer` / `no-store, private` contract —
    pass through the proxy unchanged. Set
    `SLAIF_TRUSTED_PROXY_PEERS` to the source peer the application actually
    sees from the proxy. For a host proxy dialing a Docker-published loopback
    port, this is normally the bridge gateway; discover and verify it as
    in step 6. Keep `127.0.0.1` separately for the in-container probe: the application
    honors that peer's forwarding and treats every other peer as a direct
    client. In both cases the application strips every forwarding header it
    does not consume (trusted and untrusted alike), keeps the original
    socket peer separately from the normalized client identity
    (`request.client_ip`), and logs only the safe normalized client in its
    request log. Browser POSTs must present an `Origin` exactly matching
    the `SLAIF_CSRF_TRUSTED_ORIGINS` entry. Nginx remains acceptable if
    already operated institutionally; it must implement the same
    overwrite-not-append forwarding, peer allowlist, and deferred-default
    header semantics. Full contract: `docs/deployment.md` section 8.

13. **Verify HTTPS end to end** from outside the host. Enter the approved
    service hostname (without a scheme or path); reuse it for the checks
    below in the same shell:

    ```bash
    read -r -p "Approved service hostname: " SAR_SERVICE_HOST
    curl -fsS "https://${SAR_SERVICE_HOST}/health/live"
    ```

14. **`/health/live`** returns HTTP 200 (liveness; no database dependency).

15. **`/health/ready`** returns HTTP 200 (database reachable, migration state
    current).

16. **`/login/`** returns HTTP 200; sign in with the administrator. `/manage/`
    is active-staff-only and redirects safely for everyone else. An
    unauthenticated API probe must return HTTP 401 — a status-only
    check, deliberately without `curl -f` (which would report the expected
    401 as a curl failure):

    ```bash
    curl -sS -o /dev/null -w '%{http_code}\n' "https://${SAR_SERVICE_HOST}/api/v1/me/"
    # expected: 401 (body intentionally not captured here)
    ```

17. **Once the pilot database is prepared** (assets, staff, users, and
    policies configured), run the pilot readiness gate:

    ```bash
    docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml run --rm app \
      python manage.py pilot_readiness_check --strict
    ```

    This checks database/inventory/account/policy readiness; it does not qualify
    public TLS, proxy trust, abuse capacity or the operator's incident/backup
    arrangements. Pair it with the current HTTPS/security qualification.

### Shared authentication and API budgets

Member and administration login share PostgreSQL counters across workers. API
budgets apply before authentication (including invalid bearer attempts) and also
per authenticated bearer owner/token. Defaults are:

| Budget | Limit | Window | Environment variable |
| --- | --- | --- | --- |
| Login source IP | 30 POST attempts | 300 seconds | `SLAIF_LOGIN_IP_LIMIT` |
| Login identity | 10 POST attempts | 300 seconds | `SLAIF_LOGIN_IDENTITY_LIMIT` |
| API source IP | 1200 requests | 60 seconds | `SLAIF_API_IP_LIMIT` |
| API bearer owner | 600 requests | 60 seconds | `SLAIF_API_OWNER_LIMIT` |
| API token | 300 requests | 60 seconds | `SLAIF_API_TOKEN_LIMIT` |

`SLAIF_LOGIN_WINDOW_SECONDS` and `SLAIF_API_WINDOW_SECONDS` set the respective
windows. All are bounded positive integers validated at settings load. Choose
rates for the expected users/agents and shared network addresses; do not disable
or weaken the protection to work around proxy identity errors. The trusted proxy
must supply the real single-hop client address. Fixed windows can admit a burst
across their boundary; these are application budgets, not distributed-DDoS protection.

Denials return 429, `Retry-After` and `Cache-Control: no-store`; API denials retain
machine-readable problem details and request correlation. An unavailable security
database fails closed with a generic 503. Identity keys are HMAC-derived rather
than raw email/token values. There is no permanent automatic account lockout.
The counter operations bound lock wait to one second and statement execution to
two seconds; production database connection timeouts must be 1–30 seconds
(default five). A small opportunistic cleanup accompanies normal traffic.

Expired counters can also be purged deliberately (dry run, then a bounded batch):

```bash
docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml run --rm app \
  python manage.py purge_expired_abuse_buckets
docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml run --rm app \
  python manage.py purge_expired_abuse_buckets --apply --batch-size 1000
```

Scheduling cleanup, monitoring denials and protecting the public perimeter are
operator responsibilities. See [Security model](docs/security-model.md).

### Optional operator branding (same image, no rebuild)

Appearance overrides (CSS, logos, favicon, one public image) are optional
and off by default. To use them, keep the same application image and add
the read-only overlay — no rebuild, no new service, port or privilege:

```bash
install -d -m 755 deploy/branding
# put at most one file per fixed slot into deploy/branding (docs/branding.md)
docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml \
    -f compose.branding.example.yaml up -d
```

The overlay mounts `./deploy/branding` read-only at `/branding` and sets
`SLAIF_BRANDING_DIR`. Files are validated on use; a missing or invalid
asset falls back to the packaged default for that slot only. The complete
operator contract (slots, formats, size limits, refresh/cache semantics,
trust model and failure behavior) is [docs/branding.md](docs/branding.md).
The same overlay also works with `compose.yaml` for local evaluation.

## 6. Rehearsal: what it does and does not prove

`deploy/rehearse_internal_alpha_deployment.sh` runs a disposable,
synthetic-value, production-shaped rehearsal on this machine:

- creates git-ignored `deploy/env.production` and
  `deploy/secrets/postgres_password` with synthetic values (refusing to run
  if real ones already exist);
- renders the production Compose config and builds the runtime image
  (checking the `10001:10001` runtime user and bundled static/bootstrap
  assets);
- starts a disposable PostgreSQL and the app under a unique Compose project
  on a loopback port (default 18080; `SLAIF_REHEARSAL_PORT` overrides it);
  a port occupied by a non-rehearsal process is never killed — the script
  refuses to start and asks for another port;
- applies migrations and the explicit default-policy initializer, validates the bootstrap import, runs
  `operational_check`, validates OpenAPI, and smokes
  `/health/live`, `/health/ready`, `/login/`, anonymous `/manage/` redirect,
  and unauthenticated `/api/v1/me/` failure;
- removes its own env/secret files, containers, and volume on success.
  A killed run can leave rehearsal-owned residue; inspect with `--status`
  and remove it with `--cleanup-owned` (never automatic). Only
  rehearsal-owned projects (label prefix `slaif-alpha-rehearsal-`) are ever
  touched; foreign projects are never affected.

An opt-in `.github/workflows/deployment-rehearsal.yml` workflow (manual
`workflow_dispatch`) runs the same rehearsal in CI, separately from the four
standard jobs.

The rehearsal checks the documented deployment procedure using
synthetic disposable resources. It is not a deployment: it uses no real DNS,
TLS certificates, secrets, or host, and it cleans itself up. Distinguish the
three evidence levels:

1. **CI** renders/builds the production image and checks its runtime user and
   assets. The standard test job also drives owned production-shaped,
   same-image branding and real-HTTPS boundary qualifications, including
   failure/cleanup paths. It never deploys a real service.
2. **Full local rehearsal** (this script, no flag) runs the production-shaped
   stack with synthetic values. Local evidence only.
3. **A real deployment** is a human-authorized host with real DNS/TLS and
   real secrets from the operator's secret store. It is separate from disposable qualification.

### Real HTTPS boundary qualification

`deploy/rehearse_https_boundary.sh` builds a tracked-source image and drives the
production-shaped application through a pinned Caddy v2.11.6 instance. It uses
loopback-only ports, temporary self-signed certificates, synthetic configuration,
private PostgreSQL and exact owned cleanup. It tests forwarding spoof/ambiguity,
TLS/CSRF/cookies, private schema/docs, error/header/log privacy, body/deadline
bounds and direct untrusted-container access.

Run rehearsals only from an owned disposable checkout. The full scripts may
create/remove deployment configuration and volumes; existing files or foreign
resources are refused. Neither modifies DNS, issues real certificates, changes
host trust or publishes a service. See [Testing](TESTING.md) for the isolation rules.

## 7. Persistence

- All database state lives in the Compose named volume `postgres-data`
  (on-disk name `<compose-project>_postgres-data`, where the project name
  is selected explicitly with `-p` in these instructions).
- `docker compose down -v` DELETES that volume, i.e. it deletes the
  database. Never use it as a routine stop; see section 10.
- Inspect: `docker volume ls | grep postgres-data`.

## 8. Backup and restore

The application image deliberately does not bundle PostgreSQL client tools;
in the Compose deployment shape, backups therefore run from the PostgreSQL
container using its native tools.

Backup — create the artifact, then copy it OFF the host. A backup stored on
the same host as the database does not protect against host loss; the
off-host copy is a requirement, not a suggestion. Choose a protected,
operator-owned destination (the example creates a mode-0700 directory;
adapt the path to your backup policy) and keep the artifact's contents
out of logs and version control:

```bash
install -d -m 0700 /backups
docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml exec db \
  pg_dump -U slaif -d slaif_reservation -Fc \
  -f /tmp/slaif-$(date +%Y%m%d).dump
docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml cp \
  db:/tmp/slaif-$(date +%Y%m%d).dump /backups/slaif-$(date +%Y%m%d).dump
# then transfer /backups/slaif-YYYYMMDD.dump to another machine (operator choice)
```

Restore — only under a separately human-approved incident plan, never as a
routine operation. The application is stopped first and must not be
restarted after a failed restore:

```bash
# Replace YYYYMMDD with the date of the selected, verified backup.
# Each command runs only if the preceding command succeeded.
docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml stop app &&
docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml cp \
  /backups/slaif-YYYYMMDD.dump db:/tmp/slaif-YYYYMMDD.dump &&
docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml exec db \
  pg_restore -U slaif -d slaif_reservation \
  --clean --if-exists --exit-on-error /tmp/slaif-YYYYMMDD.dump &&
docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml run --rm app \
  python manage.py operational_check &&
docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml start app
```

`--exit-on-error` (present in the pinned PostgreSQL 17 image's
`pg_restore --help`) stops the restore at the first error instead of
continuing. With `--clean --if-exists`, a failed restore can leave the
database partially restored: if the command fails, leave the application
stopped, treat the database as suspect, and repeat the restore from the
last known-good backup (or escalate under the incident plan) — do not
start the app against a half-restored database.

The repository also provides tested wrappers around the same
`pg_dump`/`pg_restore` tools — `python manage.py backup_database --output
... --apply`, `python manage.py restore_database --input ... --apply`, and
the codified isolated round-trip drill `python manage.py restore_drill`
(dry-run by default; the drill target database must not exist yet). Those
run where the pg client tools and a `DATABASE_URL` are both available
(host-side or development environments), not inside the app container. Full
procedure and refusal semantics: `docs/runbooks/backup-and-restore.md`.

An untested backup is not sufficient. Until a restore into an isolated
target has been verified (`restore_drill` or an equivalent drill), treat
backups as unverified. Scheduled, off-host backup remains an
operator-owned responsibility; the repository provides no scheduler.

## 9. Upgrading to a new reviewed revision (manual procedure)

Before upgrading, recover the recorded Compose project name and set
`SAR_COMPOSE_PROJECT` to that exact name. **Never import the demo inventory as an
upgrade step.** Existing database assets stay unchanged. The current example image
alias is `slaif-asset-reservation:pilot`; older installations may have used
`:internal-alpha`. Record the previous image identity for rollback before building
the new alias. Changing the image alias does not change project or volume identity.

1. Obtain the reviewed revision (commit with green CI) and human approval.
2. Back up the database first (section 8).
3. Build the new image at the new commit under the example tag; do NOT delete
   the previous commit-addressable image tag — it is the application
   rollback point:

   ```bash
   docker build --tag slaif-asset-reservation:pilot .
   docker tag slaif-asset-reservation:pilot \
     "slaif-asset-reservation:$(git rev-parse --short HEAD)"
   ```

4. Review pending migrations before applying them:

   ```bash
   docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml run --rm app \
     python manage.py showmigrations
   ```

5. Apply migrations deliberately:

   ```bash
   docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml run --rm app \
     python manage.py migrate --noinput
   ```

   Upgrades do not initialize or change policies: migrations alone never
   create the default policy, and existing policy configuration is never
   touched. An upgraded installation that still has no policy rows may
   deliberately run the same explicit initializer
   (`python manage.py initialize_default_policy`); any existing policy
   configuration makes it a no-op.

6. Restart the application on the new image:

   ```bash
   docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml up -d app
   ```

7. Verify `/health/ready`, re-run `operational_check`, and re-run
   `pilot_readiness_check --strict` where the pilot database exists.

There is no automatic rollback. Application rollback means retagging the
recorded previous commit-addressable image back to the example tag and
restarting on it; it is only safe while the database stays compatible
with the older code. Database rollback means restoring from backup
(section 8). Both are explicit human decisions.

```bash
read -r -p "Recorded previous image tag (slaif-asset-reservation:commit): " SAR_PREVIOUS_IMAGE
read -r -p "Approved service hostname: " SAR_SERVICE_HOST
# Verify the image exists before changing the application tag.
docker image inspect "$SAR_PREVIOUS_IMAGE" --format '{{.Id}}' &&
docker tag "$SAR_PREVIOUS_IMAGE" slaif-asset-reservation:pilot &&
docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml up -d app &&
curl -fsS "https://${SAR_SERVICE_HOST}/health/ready" &&
docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml run --rm app \
  python manage.py operational_check
```

If the already-applied migrations are not compatible with the older code,
an application rollback is unsafe: do not guess with `git revert` or
`migrate` — restore from the approved backup (section 8) instead.

## 10. Shutdown and restart

```bash
# stop/start/restart preserve all persistent data
docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml stop app
docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml start app
docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml restart app
```

- Both services are configured with `restart: unless-stopped`, so the
  containers restart automatically when the Docker daemon (re)starts after a
  host reboot; `docker compose ... up -d` recovers any container the daemon
  did not restart.
- `docker compose down` (without `-v`) removes containers but keeps the
  `postgres-data` volume. `docker compose down -v` deletes the database
  (section 7).

## 11. Security boundaries

- Never commit `deploy/env.production` or `deploy/secrets/` (both are
  git-ignored); keep the secret file mode `0600` and its directory `0700`.
- PostgreSQL is never public: the production-shaped example publishes no
  database port, and the application is loopback-only behind the proxy.
- Production settings fail closed: `SLAIF_DJANGO_SECRET_KEY`,
  `SLAIF_ALLOWED_HOSTS`, `SLAIF_CSRF_TRUSTED_ORIGINS`,
  `SLAIF_TRUSTED_PROXY_PEERS`, `DATABASE_URL`, and
  `SLAIF_API_TOKEN_PEPPER` are all required, the pepper must be distinct and
  at least 32 bytes, and `SLAIF_DEBUG` is rejected. `SLAIF_ALLOWED_HOSTS`
  entries must be explicit bare hosts (hostnames, IP literals, or Django
  dotted subdomain wildcards); out-of-contract HSTS combinations are
  rejected (a non-zero `SLAIF_SECURE_HSTS_SECONDS` requires the SSL redirect
  enabled; the subdomain/preload flags require a non-zero max-age). Trusted
  proxy peers must be explicit IP addresses or point-to-point networks
  (broad ranges are rejected); only those peers may supply
  TLS/client-identity forwarding, every other peer is a direct client with
  all forwarding headers stripped. Secure session/CSRF
  cookies and SSL redirect are on by default; HSTS stays disabled until the
  final HTTPS hostname is verified, then must be enabled explicitly.
- Administrator-created local accounts support the authenticated pilot.
  Institutional OIDC and password-reset/email workflows remain deferred.
- Internet access uses the qualified HTTPS proxy boundary and shared PostgreSQL
  budgets for member/admin login and API traffic. Keep the application listener
  private; configure explicit proxy peers, overwrite forwarding headers, preserve
  secure cookies/CSRF and review logs. Perimeter protection, monitoring, account
  administration and incident response remain operator responsibilities.
- No real secret, token, credential, or private export may ever enter the
  repository, the image, logs, or this document.

## 12. Operating limits

- No institutional OIDC or SSO; accounts are administrator-created only.
- No password reset or email workflow; lost credentials require
  administrator-level recovery.
- No notification system (no reservation emails or reminders).
- No execution enforcement: the system grants reservation entitlement only;
  it does not run jobs or allocate/enforce GPU usage.
- No automatic SmartScheduling cutover; the migration tooling is
  synthetic-fixture only and human-supervised.
- No production monitoring stack or alert routing; the operator owns proxy,
  health, database, and backup monitoring, and scheduled off-host backup.
- Login and API abuse budgets use shared PostgreSQL counters. They do not
  replace perimeter protection against distributed or volumetric attacks.
- Shared privileged PostgreSQL role: the application, migrations, and
  backups all run as the same database role (`slaif`, a superuser under the
  Compose defaults). Role separation is a known operational limitation.
- No project/group authorization: every active human account may browse
  active assets and request any active, reservable, exclusive asset with an
  effective policy. This is the current authenticated-pilot authorization
  model; account creation does not create project-scoped resource permissions.

## 13. Documentation map

- [QUICKSTART.md](QUICKSTART.md) — shortest local Docker evaluation path.
- `docs/deployment.md` — deeper deployment reference and rationale
  (configuration reference, container image facts, proxy/TLS, logging and
  monitoring, scheduled work, release process, rollback, readiness gates,
  remaining gaps).
- `docs/runbooks/` — operator runbooks: first authenticated HTTPS deployment
  checklist, pilot readiness gates, pilot preparation pack, backup and
  restore.
- `docs/api-contract.md`, `docs/human-ui.md`, `docs/security-model.md` —
  implemented API contract, UI, and security references.

## 14. Uninstall and data retention

Stopping is not uninstalling: `stop` and `down` (without `-v`) leave the
named volume `postgres-data` — the entire database — on disk. Make the
data-retention decision deliberately.

- **Retain the data (default):**
  `docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml down` removes the
  containers; the named volume survives for a later re-deployment. Export
  the database (section 8) if it must live beyond this host.
- **Delete the data (destructive):** only after the retention decision,
  on this operator-owned project only:

  ```bash
  docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml down -v
  ```

  This permanently deletes the named volume and all reservations, users,
  API tokens, policies, blackouts, and audit rows. Never run an unscoped
  `docker compose down -v`, and never delete a volume you did not create.
- **Remove the rest:** the image tags
  (`slaif-asset-reservation:pilot` and the commit-addressable
  tag), `deploy/env.production` and `deploy/secrets/` (handle them per
  your secret-retention policy), and the proxy vhost. This deployment
  installs no scheduler or other host service.

## 15. Troubleshooting

| Symptom | First checks |
| --- | --- |
| Compose cannot publish the app port | The loopback port is taken (for example `ss -ltnp`): coordinate with the owner or change `SLAIF_APP_HOST_PORT` consistently. Never stop a service you do not own. |
| App cannot start: database password mismatch | The password in `DATABASE_URL` (`deploy/env.production`) must equal the content of `deploy/secrets/postgres_password`. If the `postgres-data` volume already exists, changing `POSTGRES_PASSWORD_FILE` does **not** change the existing database's password — PostgreSQL applies it only when initializing an empty volume. Align the password file with the existing database, or re-provision the volume (destructive). |
| App unhealthy / liveness probe fails with HTTP 400 | `DisallowedHost`: `SLAIF_ALLOWED_HOSTS` is missing `127.0.0.1` (the in-container healthcheck probe) or the service hostname (step 2). |
| `/health/ready` returns 503 | Database unreachable or migrations not applied: check `docker compose -p "$SAR_COMPOSE_PROJECT" -f compose.production.example.yaml ps` and the `db` logs, then run the deliberate migration step (section 5, step 7). |
| HTTPS redirect or CSRF failures behind the proxy (301 loops, missing secure cookies, CSRF 403) | The trusted-peer list must include the peer the proxy actually presents: `SLAIF_TRUSTED_PROXY_PEERS` needs `127.0.0.1` (in-container probe) and, for a Docker-network proxy, the bridge gateway IP; the proxy must overwrite `X-Forwarded-Proto` from the real connection (steps 2 and 12). `SLAIF_CSRF_TRUSTED_ORIGINS` must be the exact `https://` service origin, and browser POSTs must carry the matching `Origin`. |
| Underscore header variants (`X_Forwarded_*` etc.) have no effect | Deliberate: Gunicorn runs with `--header-map drop`, so wire headers containing underscores are discarded at the parser and never reach the application; the supported contract uses only the canonical hyphenated names written by the trusted proxy. |
| No reservation accepted | No unambiguous active policy resolves for the asset (exact asset, parent machine, global) — the system fails closed. Fresh installs run `initialize_default_policy` after migrate (section 5, step 7); otherwise configure a policy in `/manage/`. |
| Backup/restore tools missing in the app container | The application image deliberately contains no PostgreSQL client tools; backups run from the `db` container (section 8), and the `manage.py` wrappers run host-side where a pg client and `DATABASE_URL` are available. |

### Abuse-control configuration and cleanup

The production example supplies positive shared login/API budgets. See
[the allowances and tradeoffs](docs/decisions/0016-shared-abuse-controls.md)
before changing them for a shared NAT or agent integration. Counter expiry
does not permanently lock an account. Inspect expiry with
`python manage.py purge_expired_abuse_buckets`; add `--apply --batch-size 1000`
for bounded removal. Run inside the configured application container like
other maintenance commands. No periodic cleanup job is installed; bounded
opportunistic cleanup also runs. Database connection timeouts default to five
seconds and production requires a positive value no greater than thirty.
