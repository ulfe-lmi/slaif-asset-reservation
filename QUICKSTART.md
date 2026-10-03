# Quickstart — local Docker evaluation (about 5–10 minutes)

The shortest real path to a running local instance of SLAIF Asset
Reservation, using the committed development `compose.yaml` (loopback-only
bindings, development settings and development secrets). It exists so you
can evaluate the product on one machine; it is not a long-running service
deployment. For that, see [INSTALL.md](INSTALL.md).

Budget about 5–10 minutes with a warm Docker cache and good network
connectivity; a first run is longer because Compose builds the application
image and pulls the pinned PostgreSQL 17 image.

## Before you start

- A **Linux `x86_64` (amd64)** host. The committed images are pinned to
  `linux/amd64` digests; no other architecture is supported or verified on
  this path.
- **Docker Engine** with the **Compose v2 plugin** (`docker compose version`).
- **Git** and access to the private repository
  `ulfe-lmi/slaif-asset-reservation`.
- The host loopback ports **`127.0.0.1:5432`** (PostgreSQL) and
  **`127.0.0.1:8000`** (application) must be free. If something else already
  listens on either port, identify the owner first (for example
  `ss -ltnp`). **Never stop or reconfigure a service you do not own**, and do
  not edit the committed Compose file to work around a host collision —
  coordinate with the service owner, or evaluate at a different time.

The development stack uses development-only secrets that are safe to run
locally but are **not** acceptable for any real deployment.

## 1. Clone the repository

```bash
git clone <private-repo-url> slaif-asset-reservation
cd slaif-asset-reservation
```

Check out the revision you want to evaluate (for a review, the exact commit
SHA).

## 2. Start the evaluation stack (detached)

Run every Compose command in this quickstart with the dedicated evaluation
project name **`slaif-eval`**. This keeps the evaluation isolated from the
default project (whose name is the repository directory): its database lives
in the volume `slaif-eval_postgres-data`, so stopping or tearing down the
evaluation can never touch a normal development stack or any other project.

```bash
docker compose -p slaif-eval up -d --build app
```

This starts PostgreSQL and the application in the background (the app waits
for a healthy database), so the commands below can run afterwards. Then wait
for both services to settle:

```bash
docker compose -p slaif-eval ps
```

Expect `db` to become `healthy` and `app` to be `running`. If a container is
failing, inspect `docker compose -p slaif-eval logs app` (and `db`).

## 3. Apply migrations (deliberate)

Migrations are a deliberate command, never hidden in application startup:

```bash
docker compose -p slaif-eval exec app python manage.py migrate --noinput
```

This installs the `btree_gist` extension and the
`reservation_no_overlap_per_asset` exclusion constraint that enforce
reservation exclusivity in PostgreSQL.

## 4. Optional: import the sanitized bootstrap asset inventory

The repository ships a **sanitized** asset inventory as a static file. It is
a bootstrap data set, **not a verified hardware inventory**: the import
preserves verification flags and explicit unknown locators, and imported
assets are not treated as probed or online machines.

Dry run first (validates only, changes nothing), then apply:

```bash
docker compose -p slaif-eval exec app \
  python manage.py import_bootstrap_assets --input data/bootstrap/assets.yaml
docker compose -p slaif-eval exec app \
  python manage.py import_bootstrap_assets --input data/bootstrap/assets.yaml --apply
```

This step is optional: the application runs without it and simply has no
asset set.

## 5. Create the first administrator

Accounts are administrator-created; there is no self-registration.

```bash
docker compose -p slaif-eval exec app python manage.py createsuperuser
```

The command is interactive (email address, then password twice).
Non-interactive alternative:

```bash
docker compose -p slaif-eval exec -e DJANGO_SUPERUSER_PASSWORD=<your-password> app \
  python manage.py createsuperuser --noinput --email admin@example.org
```

Logins in this application use the account's **email address** as the
identifier, not a username. Do not invent or seed accounts for anyone else;
create only the administrator you will use for the evaluation.

## 6. Log in and verify the endpoints

1. Log in at <http://127.0.0.1:8000/login/> with the administrator from
   step 5.
2. Check the health endpoints (no login required):

   ```bash
   curl http://127.0.0.1:8000/health/live    # liveness, no database dependency
   curl http://127.0.0.1:8000/health/ready   # database reachable, migrations current
   ```

3. After login, the member UI offers: `/` (dashboard), `/assets/` and
   `/assets/<uuid>/` (inventory with privacy-safe advisory availability),
   `/assets/<uuid>/reserve/`, `/reservations/` and
   `/reservations/<uuid>/` (cancel/release), `/tokens/` and `/tokens/new/`
   (API tokens, one-time plaintext display), and `/profile/` (display name
   and timezone). Staff-only areas: `/manage/` (policies, blackouts,
   cross-user reservations, audit) and `/admin/`. Service accounts cannot
   log in to the human UI.

## 7. Configure a policy before booking

A reservation is only accepted when an **active policy** resolves for the
asset — exact asset, then parent machine, then global. A missing or
ambiguous policy **fails closed**. The evaluation database ships **no
policies and no fake seed data**: until an operator configures policies
through `/manage/`, no reservation can be created. That is the correct,
expected behavior on an empty evaluation database — not a defect — and an
empty evaluation database is **not** a pilot-ready database.

## 8. Stop and teardown (data-preserving by default)

```bash
# Stop the stack; all data is preserved in the volume.
docker compose -p slaif-eval stop

# Start it again later.
docker compose -p slaif-eval start
```

`docker compose -p slaif-eval down` (without `-v`) removes the containers
but keeps the `slaif-eval_postgres-data` volume.

> **WARNING — destructive.**
> `docker compose -p slaif-eval down -v` **permanently deletes the
> evaluation database** (volume `slaif-eval_postgres-data`) together with
> the containers. Run it only for this evaluation project, only when you
> intend to discard the evaluation data, and never as an unscoped
> `docker compose down -v`. It is the only step in this quickstart that
> deletes data.

## Minimal troubleshooting

| Symptom | First check |
| --- | --- |
| Compose fails to publish a port | The port is already in use (section "Before you start"). Identify the owner; never stop a foreign service. |
| `db` never becomes healthy | `docker compose -p slaif-eval logs db`; the first start pulls the image. |
| `app` crashes or restarts | `docker compose -p slaif-eval logs app`; confirm step 3 ran against this project's database. |
| Login rejected | You used a different project's database or a different administrator (steps 2 and 5 must use the same `-p slaif-eval`). |
| No assets listed | Step 4 was optional; apply the bootstrap import if you want the sanitized set. |

## Next

- [INSTALL.md](INSTALL.md) — the full operator guide for a controlled
  internal-alpha deployment (production-shaped Compose, protected secrets,
  reverse proxy, backup/restore, upgrades).
- [README.md](README.md) — product overview, capabilities and
  documentation map.
- [docs/api-contract.md](docs/api-contract.md) — the implemented `/api/v1/`
  contract for agent clients.
