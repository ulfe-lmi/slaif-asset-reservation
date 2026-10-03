<div align="center">
  <a href="https://www.slaif.si">
    <img src="https://www.slaif.si/assets/slaif-logo.svg" width="300" alt="SLAIF">
  </a>
</div>

# SLAIF Asset Reservation

<div align="center">

[![CI](https://github.com/ulfe-lmi/slaif-asset-reservation/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ulfe-lmi/slaif-asset-reservation/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)

**A single reservation authority for shared laboratory assets — for both
authenticated humans and authenticated software agents.**

</div>

SLAIF Asset Reservation gives researchers and their tools one conflict-free
way to book exclusive laboratory resources — initially the laboratory's
scattered Linux compute machines and their GPUs, with an asset-oriented
model that other exclusive resources can join without redesign. A
reservation accepted by the system is:

- **conflict-free** for its asset and time range — exclusivity is enforced
  by PostgreSQL, not by application checks alone;
- **policy-gated** — duration, lead time, horizon, purpose and per-principal
  counters under the active policy, failing closed when no policy applies;
- **attributable** to an authenticated principal (human account or scoped
  API token);
- **auditable** — every lifecycle transition is recorded atomically with its
  domain mutation;
- **reducible** — owner or permitted staff can cancel or release it through
  explicit, audited transitions.

## Get started

- **[QUICKSTART.md](QUICKSTART.md)** — the essential Docker path to a
  running local evaluation instance in roughly 5–10 minutes (loopback-only,
  development settings).
- **[INSTALL.md](INSTALL.md)** — the full operator guide for a controlled
  internal-alpha deployment: prerequisites, protected secrets, reverse
  proxy, readiness gates, backup and restore, upgrades and rollback.

## How it works

```mermaid
flowchart TD
    human["Humans — browser session"]
    agent["Software agents — scoped bearer tokens"]
    staff["Staff — /manage/ session"]
    app["SLAIF Asset Reservation (Django monolith)\npolicy, reservations, blackouts, audit"]
    db["PostgreSQL 17\nper-asset exclusive time ranges (btree_gist)"]
    human --> app
    agent --> app
    staff --> app
    app --> db
```

One monolith owns the scheduling records and the authoritative domain
operations. Humans reserve through the server-rendered web UI; agents use a
versioned REST API with scoped, expiring tokens and idempotent mutations;
staff configure policies, maintenance blackouts and cross-user lifecycle
through a separate management area. Reservations are **entitlements**: the
system deliberately does not run jobs, allocate hardware, or enforce usage —
that is the boundary of a future, separate execution gateway.

## What you can do

| Client | Capabilities |
| --- | --- |
| **Humans (browser)** | Browse active assets, see privacy-safe advisory availability, create / cancel / release own reservations, manage own API tokens (one-time display), set display name and timezone. Accounts are administrator-created; there is no self-registration. |
| **Agents (API)** | `/api/v1/me/`, per-asset advisory availability, and owner-scoped reservation list / detail / create / cancel / release with bounded `Idempotency-Key` mutations and machine-readable problem details. Contract: [docs/api-contract.md](docs/api-contract.md). Asset list/detail endpoints remain staff-session-only — a token alone grants no asset discovery. |
| **Staff (management)** | `/manage/`: reservation policies, coarse maintenance blackouts, cross-user reservation inspection and lifecycle, audit review and bounded export. Operational: `/health/live`, `/health/ready`, `operational_check`, `pilot_readiness_check`, backup/restore tooling. |

## Supported runtime

- **Python 3.13**, **Django 5.2** (locked 5.2.17), **DRF** (locked 3.17.2),
  **PostgreSQL 17**; dependencies locked in `uv.lock`.
- **Docker Compose** on a single Linux host (`linux/amd64` is the supported
  and verified architecture): loopback-only development Compose, and a
  production-shaped example (non-root `10001:10001`, read-only root
  filesystem) behind an HTTPS reverse proxy.
- Server-rendered UI with local static assets; generated OpenAPI schema with
  locally served Swagger UI.

## Documentation

| Topic | Document |
| --- | --- |
| Local Docker evaluation | [QUICKSTART.md](QUICKSTART.md) |
| Installation and deployment (operator) | [INSTALL.md](INSTALL.md) |
| API contract (`/api/v1/`) | [docs/api-contract.md](docs/api-contract.md) |
| Human UI | [docs/human-ui.md](docs/human-ui.md) |
| Domain model and time semantics | [docs/domain-model.md](docs/domain-model.md) |
| Deployment reference | [docs/deployment.md](docs/deployment.md) |
| Security model | [docs/security-model.md](docs/security-model.md) |
| Testing and verification | [TESTING.md](TESTING.md) |
| Operator runbooks and readiness gates | [docs/runbooks/](docs/runbooks/) |
| Architecture decision records | [docs/decisions/](docs/decisions/) |
| Full documentation index | [docs/README.md](docs/README.md) |

## Important limitations

- **Trusted internal pilot only.** No unrestricted public-Internet exposure;
  no project/group authorization — every active authenticated human account
  can browse active assets and request any active, reservable, exclusive
  asset with an effective policy.
- No login throttling or API rate limiting.
- No OIDC, password reset, email, or notification system; accounts are
  administrator-created, and service accounts cannot log in to the human UI.
- Reservations are entitlements, not enforcement: no workload execution,
  physical allocation, or monitoring of actual usage.
- Shared privileged PostgreSQL role; scheduled and off-host backup are
  operator-owned responsibilities.
- The execution gateway, scheduler, monitoring stack, and real
  SmartScheduling migration/cutover are outside the current core.

## Developers

Python 3.13 with `uv` (locked dependencies) and a local PostgreSQL 17:

```bash
docker compose up -d db
uv sync --locked --all-groups
cp .env.example .env
uv run --env-file .env python manage.py migrate
uv run --env-file .env python manage.py runserver
```

Standard verification commands are in [TESTING.md](TESTING.md); contribution
rules in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[Apache License 2.0](LICENSE).

---

Development in this repository runs under the Codex-only **Concentrated OAP**
workflow: the root [AGENTS.md](AGENTS.md) routes agent roles,
[docs/oap-workflow.md](docs/oap-workflow.md) describes the live workflow, and
orders and immutable reports live under `oap/`. Earlier work-order history is
preserved for reference under [docs/work-orders/](docs/work-orders/) and
[docs/project-handoff.md](docs/project-handoff.md).
