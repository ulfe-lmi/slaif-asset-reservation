# INSTALL — Canonical Installation and Deployment

**Status:** CI-green, production-shaped internal-alpha candidate; a real
deployment has not yet been evidenced.

This is the single canonical installation and deployment document for SLAIF
Asset Reservation. Docker/Compose is the deployment path. The `uv` workflow is
the development path. Deeper configuration reference and rationale:
`docs/deployment.md`. Operator checklists and gates: `docs/runbooks/`.

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
- The repository is a single-host Compose stack. There is no
  Kubernetes/Swarm/Helm/Terraform/Ansible path, no image registry, and no
  automated deployment.

## 2. Prerequisites

What this deployment actually requires:

- A Linux host.
- Supported host architecture: Linux, x86_64 (amd64) only. The application
  runtime image is built from `python:3.13-slim`, pinned to a linux/amd64
  digest in the `Dockerfile`, and the PostgreSQL service image is pinned to a
  linux/amd64 digest in the Compose files; other architectures (for example
  arm64) are not supported or verified for the documented deployment path.
- Docker Engine with the Docker Compose v2 plugin.
- Outbound connectivity to pull `python:3.13-slim` (pinned by digest in the
  `Dockerfile`) and the PostgreSQL service image (pinned by digest in the
  Compose files).
- Persistent disk for the Compose `postgres-data` volume. All reservation
  state lives in that volume.
- For real HTTPS: a DNS name resolving to the host and a TLS plan (Caddy
  automatic TLS, or institutionally managed certificates).
- The database role that runs migrations must be able to create the
  `btree_gist` extension in the application database. The Compose defaults
  satisfy this: the `postgres:17` image grants the initial `POSTGRES_USER`
  role (default `slaif`) superuser rights.

No other requirements are invented by this document.

## 3. Fast local evaluation (Docker, loopback only)

The shortest truthful Docker path to a running instance, using the committed
development `compose.yaml` (loopback-only bindings, development secrets):

```bash
# 1. Start PostgreSQL 17 (published on 127.0.0.1:5432 only)
docker compose up -d db

# 2. Build and start the application (waits for the db to be healthy)
docker compose up --build app

# 3. Migrations are a deliberate command, never hidden in app startup
docker compose exec app python manage.py migrate --noinput

# 4. Optional: import the sanitized bootstrap asset inventory
docker compose exec app python manage.py import_bootstrap_assets \
  --input data/bootstrap/assets.yaml --apply

# 5. Accounts are administrator-created; create the first administrator
docker compose exec app python manage.py createsuperuser
# non-interactive alternative:
docker compose exec -e DJANGO_SUPERUSER_PASSWORD=<password> app \
  python manage.py createsuperuser --noinput --email admin@example.org
```

Then log in at `http://127.0.0.1:8000/login/` and check
`http://127.0.0.1:8000/health/live` and `http://127.0.0.1:8000/health/ready`.

Member UI after login: `/` dashboard; `/assets/` and `/assets/<uuid>/` (detail with
privacy-safe advisory availability); `/assets/<uuid>/reserve/`; `/reservations/` and
`/reservations/<uuid>/`; `/tokens/` and `/tokens/new/` (one-time plaintext display);
`/profile/` (display name and timezone). Staff-only: `/manage/` (policies, blackouts,
cross-user reservations, audit review/export) and `/admin/`. Accounts are
administrator-created only; service accounts cannot log into the human UI.

Required steps: 1, 2, 3, 5. Step 4 is optional: the application runs without
the bootstrap inventory, it simply has no imported asset set. This stack is
for local evaluation and development, not long-running service deployment.
Tear it down (including its local data volume) with `docker compose down -v`.

## 4. Development installation (uv — development path)

This is the developer workflow, not the recommended long-running service
deployment. Use the Docker path in sections 3 and 5 for anything that will
stay up.

- Python 3.13 managed by `uv`, with the committed `uv.lock` (never edit it
  by hand).
- PostgreSQL 17 via the development Compose file.

```bash
docker compose up -d db            # development database on 127.0.0.1:5432
uv sync --locked --all-groups      # locked development dependencies
cp .env.example .env               # host-side placeholders; do not commit real .env
uv run --env-file .env python manage.py migrate
uv run --env-file .env python manage.py runserver
```

Django does not automatically load `.env` files; host-side commands pass it
explicitly with `uv run --env-file .env`. Its `DATABASE_URL` points at the
loopback-published development database; Compose supplies the application
container with its own container-internal `DATABASE_URL` using hostname
`db`. The standard verification command set for changes is in `TESTING.md`.

## 5. Internal-alpha Docker deployment (canonical procedure)

Entry gates before starting: CI green on the reviewed commit, the local
rehearsal passed (section 6), and human approval of the reviewed commit.
Every command below corresponds to current repository behavior.

1. **Clone and checkout the reviewed commit.**

   ```bash
   git clone <private-repo-url> slaif-asset-reservation
   cd slaif-asset-reservation
   git checkout <reviewed-commit-sha>
   ```

2. **Prepare the application environment file.**

   ```bash
   cp deploy/env.production.example deploy/env.production
   ```

   Replace every placeholder in the git-ignored `deploy/env.production` from
   a protected secret store — never commit it:

   - `SLAIF_DJANGO_SECRET_KEY` (at least 32 bytes);
   - `SLAIF_ALLOWED_HOSTS` and `SLAIF_CSRF_TRUSTED_ORIGINS` (your real
     hostname, `https://` origin);
   - `SLAIF_API_TOKEN_PEPPER` (at least 32 bytes, distinct from
     `SLAIF_DJANGO_SECRET_KEY`);
   - `DATABASE_URL` — the database password here **must match** the secret
     file from step 3.

3. **Create the PostgreSQL secret file.**

   ```bash
   install -d -m 700 deploy/secrets
   umask 077
   head -c 32 /dev/urandom | base64 | tr -d '=+/\n' | head -c 32 \
     > deploy/secrets/postgres_password
   ```

   The file contains exactly one line: the database password, with no
   trailing newline. The same password is structurally required in TWO
   places: the `db` container reads `deploy/secrets/postgres_password` via
   `POSTGRES_PASSWORD_FILE`, and the app connects through `DATABASE_URL` in
   `deploy/env.production`. If the two do not match, the app cannot start.

4. **Build the image at the reviewed commit.** The production Compose
   example expects the tag `slaif-asset-reservation:internal-alpha`, which is
   a mutable tag: build it at the reviewed commit, and keep a
   commit-addressable copy for application rollback.

   ```bash
   docker build --tag slaif-asset-reservation:internal-alpha .
   docker tag slaif-asset-reservation:internal-alpha \
     "slaif-asset-reservation:$(git rev-parse --short HEAD)"
   ```

   There is no release platform or registry; the image is built on the
   deployment host from the reviewed commit.

5. **Render and validate the configuration.**

   ```bash
   docker compose -f compose.production.example.yaml config
   ```

6. **Start PostgreSQL only.**

   ```bash
   docker compose -f compose.production.example.yaml up -d db
   docker compose -f compose.production.example.yaml ps
   ```

   Wait until the `db` service is healthy.

7. **Run migrations deliberately.**

   ```bash
   docker compose -f compose.production.example.yaml run --rm app \
     python manage.py migrate --noinput
   ```

   This installs the `btree_gist` extension and the
   `reservation_no_overlap_per_asset` exclusion constraint.

8. **Run the operational check.**

   ```bash
   docker compose -f compose.production.example.yaml run --rm app \
     python manage.py operational_check
   ```

9. **Configure initial assets and policies.** Import the sanitized bootstrap
   inventory (dry-run first, then apply), then configure reservation
   policies through the staff management UI at `/manage/`. Reservations
   resolve an active policy for the exact asset, its parent machine, or
   global; a missing or ambiguous policy fails closed.

   ```bash
   docker compose -f compose.production.example.yaml run --rm app \
     python manage.py import_bootstrap_assets --input data/bootstrap/assets.yaml
   docker compose -f compose.production.example.yaml run --rm app \
     python manage.py import_bootstrap_assets --input data/bootstrap/assets.yaml --apply
   ```

10. **Create the first administrator** (interactive; accounts are
    administrator-created).

    ```bash
    docker compose -f compose.production.example.yaml run --rm app \
      python manage.py createsuperuser
    ```

    Non-interactive alternative:

    ```bash
    docker compose -f compose.production.example.yaml run --rm \
      -e DJANGO_SUPERUSER_PASSWORD=<password> app \
      python manage.py createsuperuser --noinput --email admin@example.org
    ```

11. **Start the application service.**

    ```bash
    docker compose -f compose.production.example.yaml up -d app
    ```

12. **Configure the reverse proxy** from `deploy/Caddyfile.example`: replace
    the placeholder hostname and email, keep the `X-Forwarded-Proto`
    forwarding (production settings trust that header for HTTPS redirect and
    secure cookies). Nginx remains acceptable if already operated
    institutionally; see `docs/deployment.md` section 8.

13. **Verify HTTPS end to end** from outside the host:

    ```bash
    curl -fsS https://<your-hostname>/health/live
    ```

14. **`/health/live`** returns HTTP 200 (liveness; no database dependency).

15. **`/health/ready`** returns HTTP 200 (database reachable, migration state
    current).

16. **`/login/`** returns HTTP 200; sign in with the administrator. `/manage/`
    is active-staff-only and redirects safely for everyone else.

17. **Once the pilot database is prepared** (assets, staff, users, and
    policies configured), run the pilot readiness gate:

    ```bash
    docker compose -f compose.production.example.yaml run --rm app \
      python manage.py pilot_readiness_check --strict
    ```

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
  on a loopback port;
- applies migrations, validates the bootstrap import, runs
  `operational_check`, validates OpenAPI, and smokes
  `/health/live`, `/health/ready`, `/login/`, anonymous `/manage/` redirect,
  and unauthenticated `/api/v1/me/` failure;
- removes its own env/secret files, containers, and volume on success.
  A killed run can leave rehearsal-owned residue; inspect with
  `--status` and remove it with `--cleanup-owned` (never automatic).

The rehearsal proves that the documented deployment procedure coheres with
synthetic disposable resources. It is not a deployment: it uses no real DNS,
TLS certificates, secrets, or host, and it cleans itself up. Distinguish the
three evidence levels:

1. **CI** renders the production Compose config, builds the production
   image, and checks the runtime user and bundled assets. CI deliberately
   does not bring up the production-shaped stack.
2. **Full local rehearsal** (this script, no flag) runs the production-shaped
   stack with synthetic values. Local evidence only.
3. **A real deployment** is a human-authorized host with real DNS/TLS and
   real secrets from the operator's secret store. It has not been performed.

## 7. Persistence

- All database state lives in the Compose named volume `postgres-data`
  (on-disk name `<compose-project>_postgres-data`, where the project name
  defaults to the repository directory name or the `-p` value).
- `docker compose down -v` DELETES that volume, i.e. it deletes the
  database. Never use it as a routine stop; see section 10.
- Inspect: `docker volume ls | grep postgres-data`.

## 8. Backup and restore

The application image deliberately does not bundle PostgreSQL client tools;
in the Compose deployment shape, backups therefore run from the PostgreSQL
container using its native tools.

Backup — create the artifact, then copy it OFF the host. A backup stored on
the same host as the database does not protect against host loss; the
off-host copy is a requirement, not a suggestion:

```bash
mkdir -p /backups
docker compose -f compose.production.example.yaml exec db \
  pg_dump -U slaif -d slaif_reservation -Fc \
  -f /tmp/slaif-$(date +%Y%m%d).dump
docker compose -f compose.production.example.yaml cp \
  db:/tmp/slaif-$(date +%Y%m%d).dump /backups/slaif-$(date +%Y%m%d).dump
# then transfer /backups/slaif-YYYYMMDD.dump to another machine (operator choice)
```

Restore — only under a separately human-approved incident plan, never as a
routine operation, with the application stopped first:

```bash
docker compose -f compose.production.example.yaml stop app
docker compose -f compose.production.example.yaml cp \
  /backups/slaif-YYYYMMDD.dump db:/tmp/slaif-YYYYMMDD.dump
docker compose -f compose.production.example.yaml exec db \
  pg_restore -U slaif -d slaif_reservation --clean --if-exists \
  /tmp/slaif-YYYYMMDD.dump
docker compose -f compose.production.example.yaml start app
docker compose -f compose.production.example.yaml run --rm app \
  python manage.py operational_check
```

The repository also provides tested wrappers around the same
`pg_dump`/`pg_restore` tools — `python manage.py backup_database --output
... --apply`, `python manage.py restore_database --input ... --apply`, and
the codified isolated round-trip drill `python manage.py restore_drill`
(dry-run by default; the drill target database must not exist yet). Those
run where the pg client tools and a `DATABASE_URL` are both available
(host-side or development environments). Full procedure and refusal
semantics: `docs/runbooks/backup-and-restore.md`.

An untested backup is not sufficient. Until a restore into an isolated
target has been verified (`restore_drill` or an equivalent drill), treat
backups as unverified.

## 9. Upgrading to a new reviewed revision (manual alpha procedure)

1. Obtain the reviewed revision (commit with green CI) and human approval.
2. Back up the database first (section 8).
3. Build the new image at the new commit under the example tag; do NOT delete
   the previous commit-addressable image tag — it is the application
   rollback point:

   ```bash
   docker build --tag slaif-asset-reservation:internal-alpha .
   docker tag slaif-asset-reservation:internal-alpha \
     "slaif-asset-reservation:$(git rev-parse --short HEAD)"
   ```

4. Review pending migrations before applying them:

   ```bash
   docker compose -f compose.production.example.yaml run --rm app \
     python manage.py showmigrations
   ```

5. Apply migrations deliberately:

   ```bash
   docker compose -f compose.production.example.yaml run --rm app \
     python manage.py migrate --noinput
   ```

6. Restart the application on the new image:

   ```bash
   docker compose -f compose.production.example.yaml up -d app
   ```

7. Verify `/health/ready`, re-run `operational_check`, and re-run
   `pilot_readiness_check --strict` where the pilot database exists.

There is no automatic rollback. Application rollback means restarting on the
previous image tag, which is only safe while the database stays compatible
with the older code. Database rollback means restoring from backup
(section 8). Both are explicit human decisions.

## 10. Shutdown and restart

```bash
# stop/start/restart preserve all persistent data
docker compose -f compose.production.example.yaml stop app
docker compose -f compose.production.example.yaml start app
docker compose -f compose.production.example.yaml restart app
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
  `SLAIF_ALLOWED_HOSTS`, `SLAIF_CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`, and
  `SLAIF_API_TOKEN_PEPPER` are all required, the pepper must be distinct and
  at least 32 bytes, and `SLAIF_DEBUG` is rejected. Secure session/CSRF
  cookies and SSL redirect are on by default; HSTS stays disabled until the
  final HTTPS hostname is verified, then must be enabled explicitly.
- Local Django accounts, created by administrators, are acceptable for the
  deliberately constrained internal alpha but are not the final
  institutional identity solution (institutional OIDC is deferred).
- Public Internet exposure requires additional authentication, rate-limiting,
  and monitoring decisions that are currently deferred; do not expose this
  service publicly without them.
- No real secret, token, credential, or private export may ever enter the
  repository, the image, logs, or this document.

## 12. Known alpha limitations (operator-relevant)

- No institutional OIDC or SSO; accounts are administrator-created only.
- No password reset or email workflow; lost credentials require
  administrator-level recovery.
- No notification system (no reservation emails or reminders).
- No execution enforcement: the system grants reservation entitlement only;
  it does not run jobs or allocate/enforce GPU usage.
- No automatic SmartScheduling cutover; the migration tooling is
  synthetic-fixture only and human-supervised.
- No production monitoring stack or alert routing; the operator owns
  proxy, health, database, and backup monitoring.
- No API rate limiting or throttling.
- No project/group authorization: every active human account may browse
  active assets and request any active, reservable, exclusive asset with an
  effective policy. This is temporary internal-alpha behavior, not the final
  authorization model.

## 13. Documentation map

- `docs/deployment.md` — deeper deployment reference and rationale
  (configuration reference, container image facts, proxy/TLS, logging and
  monitoring, scheduled work, release process, rollback, readiness gates,
  remaining gaps).
- `docs/runbooks/` — operator runbooks: first internal-alpha deployment
  checklist, pilot readiness gates, pilot preparation pack, backup and
  restore.
- `docs/api-contract.md`, `docs/human-ui.md`, `docs/security-model.md` —
  product contract, UI, and security references.
