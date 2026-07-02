# Project Handoff

**Snapshot date:** 2026-06-22
**Purpose:** compact strategic continuity aid; verify against live GitHub before every work order

## Product goal

Build an authenticated asset reservation authority for shared laboratory compute resources, equally usable by humans and software agents, deployed on an external Linux server.

## Repository baseline before bootstrap

- repository: `ulfe-lmi/slaif-asset-reservation`;
- default branch: `main`;
- baseline commit: `f36be853799794ed11d7ce08dc9b166c9827f70c` (`Initial commit`);
- existing files: Apache-2.0 license, broad Python `.gitignore`, two-line README;
- no application scaffold, CI, AGENTS, issues, or PR implementation evidence observed.

## Accepted strategic decisions

- replace rather than extend the SmartScheduling salon model;
- generic hierarchical asset model, initial focus on machines/GPUs;
- Django 5.2 LTS + DRF 3.16 + PostgreSQL 17;
- modular monolith, server-rendered UI, OpenAPI agent API;
- human sessions and separately scoped/expiring API tokens;
- database-enforced exclusive ranges;
- UTC storage, `Europe/Ljubljana` display default, half-open intervals;
- reservation authority separate from workload execution;
- no Redis/Celery/microservices/SPA in initial release;
- OAP development through issue-scoped Codex PRs and human merge authority.

## Legacy facts retained

- 29 public GPU resources plus one `ChatGPT Pro` record;
- one disabled GPU record in admin inventory;
- Neumann has four public A100-SXM4-80GB records;
- legacy resource suffixes cannot be treated as physical GPU indices;
- durations are legacy services and are not migrated as new domain entities;
- no private clients/appointments are included in repository artifacts.

## Current milestone after Work Order 0008 merge

Constitution and architecture accepted. Work Orders 0001 through 0008 are merged into `main`.
Work Order 0001 established the executable foundation:

- Django project under `src/slaif_reservation/`;
- custom UUID user model with email identity;
- PostgreSQL-backed initial migrations;
- `/health/live`, `/health/ready`, and empty `/api/v1/` shell;
- generated OpenAPI support with private-by-default docs permissions and local Swagger UI assets;
- `uv` lockfile, pytest/Ruff/mypy/pip-audit tooling;
- Dockerfile with collected static assets, Compose, and GitHub Actions jobs named `quality`,
  `test`, `security`, and `container`.

Verified `main` foundation commit before Work Order 0002:

```text
ba9b83061e12766d884c54f02e49aa2b063b3f01
```

Work Order 0002 added hierarchical assets, sanitized bootstrap import, staff-only inventory
admin/web/API read paths, and OpenAPI coverage. Verified `main` baseline before Work Order 0003:

```text
bec3b42d694e837fd1ff78078403ec6fd2beb23c
```

Work Order 0003 added reservation policies, reservations, `btree_gist`, PostgreSQL exclusion-based
conflict enforcement, authoritative create/cancel/release services, UTC/DST semantics, and
application/ORM-level append-only audit evidence. Verified `main` baseline before Work Order 0004:

```text
463eff9ec219c841e1a4e716dd85da93152eead1
```

Work Order 0004 added active-human login/profile, member asset browsing, privacy-safe advisory
availability, and owner reservation create/list/detail/cancel/release pages. Verified `main`
baseline before Work Order 0005:

```text
fbf3a962d767497a2424ceac2244decf2f1eca23
```

Work Order 0005 added scoped API-token lifecycle, one-time plaintext display, revocation,
verification primitives, and owner-facing management pages. Verified `main` baseline before Work
Order 0006:

```text
543f38fe68b8e62572a5ef498e68d9e7ec04b5ae
```

Work Order 0006 added bearer-authenticated `/api/v1/me/`, advisory availability, owner reservation
list/create/detail/cancel/release, idempotency records, problem-details responses, and correlation
IDs. Verified `main` baseline before Work Order 0007:

```text
ccb82582b30818a0d14714a47d0759045fe84e94
```

Work Order 0007 added active-staff-only management pages for policies, maintenance blackouts,
cross-user reservation inspection/lifecycle operations, audit browsing, and bounded CSV export.
Verified `main` baseline before Work Order 0008:

```text
6e5e69f8634e648cc35f6db1386972996162cfb4
```

Work Order 0008 added production-shaped examples, structured logging, operational checks,
backup/restore wrappers, idempotency cleanup, deployment smoke guidance, and operator runbooks.
Verified `main` baseline before Work Order 0009:

```text
28e9e6198fcf3b632c21d26cf55c9fd8e93143d3
```

## Next recommended task

Work Order 0009 is the current slice: SmartScheduling migration tooling.

After Work Order 0009 is reviewed and merged, Work Order 0010 is the next major slice:
alpha verification and remediation.

## Do not do next

- do not build the polished calendar first;
- do not integrate Neumann execution;
- do not scrape/import private SmartScheduling data;
- do not add OIDC without provider details;
- do not design microservices or a queue;
- do not assume normalized hardware data is verified;
- do not open multiple overlapping domain-model PRs.

## Open decisions to revisit later

- institutional OIDC;
- production host/DNS/proxy;
- policy defaults and project governance;
- retention/privacy details;
- notification requirements;
- physical machine/device identifiers;
- historical migration scope;
- gateway authentication design.
