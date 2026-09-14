# SLAIF Asset Reservation

A professional reservation authority for shared laboratory assets, designed for both authenticated humans and authenticated software agents.

The initial deployment targets scattered Linux compute machines and their GPUs. The domain model remains asset-oriented so that other exclusive laboratory resources can be added without recreating the legacy appointment-salon abstraction.

## Status

**CI-green, production-shaped internal-alpha candidate. Not production-ready; a real deployment has not yet been evidenced.**

- The Codex-only Concentrated OAP conversion (WO0014) is **adopted and operational**:
  the one-time adoption was merged by the human, and OAP objectives 015-a through 023-a
  were executed on `main` since. Live orders and reports live under `oap/orders/` and
  `oap/reports/`; workflow references are `docs/oap-workflow.md`, `docs/OAP-RUNBOOK.md`,
  and `docs/BOOTSTRAP-SOURCES.md`. The accepted pre-conversion architecture snapshot is
  preserved at `docs/bootstrap/1/previous/docs-architecture.md`; the live
  `docs/architecture.md` path is a compatibility pointer.
- Work Orders 0001–0013 are completed history. Verified starting point:
  `main SHA before Work Order 0001: 5cf7fbc46c7d45e966215ebf07a81e8722b8a572`.
- The repository contains a minimal Django/PostgreSQL application: custom user model,
  health checks, hierarchical asset inventory, sanitized bootstrap asset import,
  member-visible inventory web pages, staff-session-only inventory API, generated OpenAPI
  support with local Swagger UI assets, CI, and container configuration. It now also
  contains reservation policy, reservations, PostgreSQL exclusivity, audit-event core, a
  server-rendered human MVP for active administrator-created accounts, an owner-managed
  API-token lifecycle UI, initial bearer-token API endpoints for `/api/v1/me/`, advisory
  availability, and owner-scoped reservation list/create/detail/cancel/release, plus a
  staff-only management area for policies, coarse maintenance blackouts, cross-user
  reservation inspection and lifecycle actions, and audit browsing/export.
  Operational-hardening artifacts include production-shaped Compose/proxy examples,
  structured production logging, operational checks, idempotency cleanup, backup/restore
  wrappers, operator runbooks, and synthetic-fixture-driven SmartScheduling migration
  tooling.
- Still absent: real production deployment, project/group authorization, full
  operating-hours calendar, token lifecycle API, management REST API, OIDC/password
  reset, notification system, API throttling, execution gateway, automated scheduler,
  production monitoring stack, and real SmartScheduling import/cutover. Private exports
  remain outside Git and CI.
- Internal-alpha authorization caveat: until project/group authorization is
  implemented, every active human account may browse active assets and request any
  active, reservable, exclusive asset with an effective policy. This is temporary
  internal-alpha behavior, not the production authorization model.

## Where to look

- `INSTALL.md` — the canonical installation and deployment document (Docker/Compose
  is the deployment path; `uv` is the development path).
- `docs/README.md` — the documentation index.
- `docs/deployment.md` — deeper deployment reference and rationale, including the
  environment-variable reference.
- `docs/runbooks/` — operator runbooks and readiness gates.
- `AGENTS.md` — role router for Codex agents; `docs/oap-workflow.md` — OAP workflow.

## Product promise

A reservation accepted by the system is:

- conflict-free for its asset and time range;
- evaluated under the same policy for web and API clients;
- attributable to an authenticated principal;
- auditable;
- revocable or releasable through explicit state transitions.

## Intended clients

- **Humans:** browser-based resource discovery, availability, reservation, cancellation, and administration.
- **Agents:** versioned REST API with scoped, expiring tokens; idempotent mutations; stable machine-readable errors. Endpoint and request/response contract: `docs/api-contract.md`.
- **Future execution gateways:** deterministic services that verify reservation entitlement before using a machine or accelerator. Workload execution is deliberately outside the core application.

## Chosen shape

- Django 5.2 LTS monolith (locked 5.2.17)
- Django REST Framework (locked 3.17.2)
- PostgreSQL 17
- server-rendered UI, progressively enhanced
- OpenAPI-described `/api/v1/`
- Docker Compose deployment on an external Linux server behind HTTPS

## Development quickstart

Development path only — for installation and deployment, see `INSTALL.md`.

```bash
docker compose up -d db            # development PostgreSQL on 127.0.0.1:5432
uv sync --locked --all-groups      # locked dependencies (Python 3.13 managed by uv)
cp .env.example .env               # placeholders for host-side `uv run --env-file .env ...`
uv run --env-file .env python manage.py migrate
uv run --env-file .env python manage.py runserver
```

Log in at `http://127.0.0.1:8000/login/`; accounts are administrator-created
(`uv run --env-file .env python manage.py createsuperuser`). The committed Compose
file is development-only and loopback-only. Standard verification command set:
`TESTING.md`. Full development-workflow details: `INSTALL.md`, section 4.

## Legacy system

The current scheduler repurposes SmartScheduling employees as GPUs and services as fixed reservation durations. Its sanitized resource inventory is retained in `data/bootstrap/assets.yaml` only as migration input. The new application does not preserve salon-specific concepts. Do not commit private exports, cookies, screenshots, browser traces, phone numbers, raw emails, or legacy private notes.

## Repository workflow

All implementation is performed through issue-scoped pull requests under the
Concentrated OAP workflow: the coding agent reads `AGENTS.md`, executes exactly one
activated order, opens a PR, and never merges it. The strategic role reviews evidence
and performs delegated development merges under the 2026-09-14 human authority file;
humans retain product-meaning (D2), release, deployment, and milestone decisions.
See `docs/oap-workflow.md` and `docs/DECISION-POLICY.md`.

## License

Apache License 2.0. See `LICENSE`.
