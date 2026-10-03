# Quickstart — local Docker evaluation (about 5–10 minutes)

The shortest real path to a running local instance of SLAIF Asset
Reservation, using the committed development `compose.yaml` (loopback-only
bindings, development settings and development secrets). It is for
evaluating the product on one machine, not for long-running service
deployment — for that, see [INSTALL.md](INSTALL.md). A first run is
longer because Compose builds the image and pulls the pinned PostgreSQL
17 image.

## Before you start

- A **Linux `x86_64` (amd64)** host (committed images are pinned to
  `linux/amd64` digests; no other architecture is supported or verified).
- **Docker Engine** with the **Compose v2 plugin** (`docker compose version`).
- **Git** and access to the private repository
  `ulfe-lmi/slaif-asset-reservation`.
- **curl** for the health endpoint checks.
- Host loopback ports **`127.0.0.1:5432`** (PostgreSQL) and
  **`127.0.0.1:8000`** (application) free. If something else listens
  there, identify the owner first (for example `ss -ltnp`) and coordinate —
  never stop a service you do not own, and do not edit the committed
  Compose file to work around a collision.

The development stack uses development-only secrets that are safe locally
but **not** acceptable for any real deployment.

## 1. Clone the repository

```bash
git clone https://github.com/ulfe-lmi/slaif-asset-reservation.git slaif-asset-reservation
cd slaif-asset-reservation
```

Check out the revision you want to evaluate; for a review, the exact commit SHA.

## 2. Start the evaluation stack (detached)

Run every Compose command in this quickstart with the dedicated evaluation
project name **`slaif-eval`** (its own containers and volume
`slaif-eval_postgres-data`). The name must be unused on this host: check
with `docker compose -p slaif-eval ps` and `docker volume ls | grep
slaif-eval` that no such project or volume exists, and if one does, do not
adopt or delete it — choose another project name (for example
`slaif-eval-2`) and use it consistently for every command in this
quickstart.

```bash
docker compose -p slaif-eval up -d --build app
docker compose -p slaif-eval ps
```

Wait until `db` is `healthy` and `app` is `running`; if a container is
failing, inspect `docker compose -p slaif-eval logs app` (and `db`).

## 3. Apply migrations (deliberate)

Migrations are a deliberate command, never hidden in application startup:

```bash
docker compose -p slaif-eval exec app python manage.py migrate --noinput
```

This installs the `btree_gist` extension and the
`reservation_no_overlap_per_asset` exclusion constraint.

## 4. Optional: import the sanitized bootstrap asset inventory

The repository ships a **sanitized** bootstrap asset inventory. It is a
bootstrap data set, not a hardware verification: imported assets keep
their stored verification flags and explicit unknown locators, and are not
treated as probed or online machines.

Dry run first (validates only, changes nothing), then apply:

```bash
docker compose -p slaif-eval exec app \
  python manage.py import_bootstrap_assets --input data/bootstrap/assets.yaml
docker compose -p slaif-eval exec app \
  python manage.py import_bootstrap_assets --input data/bootstrap/assets.yaml --apply
```

This step is optional: without it the application simply has no asset set.

## 5. Create the first administrator

Accounts are administrator-created; there is no self-registration. The
login identifier is the account's **email address**, not a username.

```bash
docker compose -p slaif-eval exec app python manage.py createsuperuser
```

The command is interactive: it prompts for `Email`, then `Password`
(entered twice to confirm).

## 6. Log in and verify the endpoints

1. Log in at <http://127.0.0.1:8000/login/> with the administrator from step 5.
2. Check the health endpoints (no login required); both must return HTTP 200:

   ```bash
   curl -fsS http://127.0.0.1:8000/health/live    # liveness, no database dependency
   curl -fsS http://127.0.0.1:8000/health/ready   # database reachable, migrations current
   ```

3. After login, the member UI offers `/` (dashboard), `/assets/` and
   `/assets/<uuid>/` (inventory with advisory availability),
   `/assets/<uuid>/reserve/`, `/reservations/` (cancel/release),
   `/tokens/` (API tokens, one-time display) and `/profile/` (display name
   and timezone). Staff-only areas: `/manage/` (policies, blackouts,
   cross-user reservations, audit) and `/admin/`. Service accounts cannot
   log in to the human UI.

## 7. Configure a policy before booking

A reservation is only accepted when an **active policy** resolves for the
asset (exact asset, then parent machine, then global); a missing or
ambiguous policy fails closed. Before the first booking, staff create an
active policy in `/manage/`.

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
| Compose fails to publish a port | The port is already in use ("Before you start"). Identify the owner; never stop a foreign service. |
| `db` never becomes healthy | `docker compose -p slaif-eval logs db`; the first start pulls the image. |
| `app` crashes or restarts | `docker compose -p slaif-eval logs app`; confirm step 3 ran against this project's database. |
| Login rejected | Different project's database or administrator (steps 2 and 5 must use the same project name). |
| No assets listed | Step 4 was optional; apply the bootstrap import if you want the sanitized set. |
| No reservation accepted | No active policy resolves for the asset; see step 7. |

## Next

Next steps: [INSTALL.md](INSTALL.md) — the full operator guide for a
controlled internal-alpha deployment; [README.md](README.md) — product
overview and documentation map; [docs/api-contract.md](docs/api-contract.md)
— the implemented `/api/v1/` contract for agent clients.
