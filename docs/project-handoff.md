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

## Current milestone after bootstrap merge

Constitution and architecture accepted. Work Order 0001 has an executable foundation in progress:

- Django project under `src/slaif_reservation/`;
- custom UUID user model with email identity;
- PostgreSQL-backed initial migrations;
- `/health/live`, `/health/ready`, and empty `/api/v1/` shell;
- generated OpenAPI support with private-by-default docs permissions and local Swagger UI assets;
- `uv` lockfile, pytest/Ruff/mypy/pip-audit tooling;
- Dockerfile with collected static assets, Compose, and GitHub Actions jobs named `quality`,
  `test`, `security`, and `container`.

Verified starting `main` SHA for Work Order 0001:

```text
5cf7fbc46c7d45e966215ebf07a81e8722b8a572
```

## Next recommended task

After human review and merge of Work Order 0001, start the next approved work order from the
resulting `main` branch. Likely next slices are account/admin hardening or the first asset model,
depending on maintainer priority.

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
