# Discovery Brief: SLAIF Asset Reservation

**Status:** Accepted strategic baseline for repository bootstrap
**Date:** 2026-06-19
**Repository:** `ulfe-lmi/slaif-asset-reservation`
**Deployment intent:** externally hosted Linux service, reachable over HTTPS
**Primary users:** LMI/SLAIF human users, administrators, and authenticated software agents

## 1. Executive decision

Build a first-class **laboratory asset reservation authority** rather than extending or automating the current SmartScheduling deployment.

The product will provide one scheduling domain and one source of truth for:

- humans using a browser;
- agents using a stable REST API;
- administrators managing assets and policy;
- future deterministic machine gateways verifying whether an actor is entitled to use a resource.

The initial domain is shared compute infrastructure, especially machines and individual GPUs. The model is intentionally asset-oriented rather than GPU-only so that other exclusive laboratory resources can be added without inventing a second reservation service.

The first implementation is a modular Django monolith backed by PostgreSQL. It is deployed as a small professional Linux service, not as a collection of microservices and not as a workload scheduler.

## 2. Current situation

### 2.1 Operational problem

The laboratory owns many scattered compute assets that are frequently idle, while users lack a purpose-built, machine-accessible way to discover and reserve them. Human reservation exists today, but agents cannot use a supported API and the existing domain model does not match the laboratory.

Typical desired agent workflow:

1. discover an asset matching capability constraints;
2. find a free short time window;
3. create an authenticated, auditable reservation;
4. run a task through a separate machine-specific mechanism;
5. release the resource early when finished.

Typical human workflow:

1. sign in;
2. inspect assets and availability;
3. reserve a resource for a clear purpose;
4. see and cancel or release own reservations;
5. receive understandable conflict and policy feedback.

### 2.2 Legacy scheduler

SmartScheduling is a generic appointment scheduler adapted as follows:

| Legacy concept | Current laboratory meaning |
|---|---|
| Business/account | LSI UL FE reservation site |
| Staff/employee | GPU or other schedulable resource |
| Service | Fixed reservation duration |
| Appointment | Reservation |
| Client | User entering contact details |
| Staff calendar | Resource calendar |

The legacy public inventory contains 30 online records: 29 GPU resources and one `ChatGPT Pro` service-like record. The administrator account also contains disabled resources and human administrator records. Public durations are modeled as 5, 15, and 30 minutes; 1, 2, 4, and 8 hours; and three separate 12-hour services. Public booking uses a 5-minute grid and a 14-day horizon.

This was a resourceful temporary solution, but it creates the wrong abstractions:

- hardware is represented as people;
- duration is represented as a product/service;
- human contact data is shaped for salon appointments;
- public automation depends on HTML forms, anti-forgery state, redirects, and Turnstile;
- resource identity is encoded in legacy usernames whose suffixes do not reliably match displayed GPU numbers;
- machine clients have no supported, scoped API contract;
- scheduling policy and physical machine integration cannot evolve cleanly.

The legacy system remains useful as migration evidence and as a temporary fallback during cutover. It is not the target architecture.

## 3. Product definition

> SLAIF Asset Reservation is an authenticated, policy-aware reservation authority for shared laboratory assets, with a unified human interface and machine API, an auditable reservation lifecycle, and extension points for deterministic execution gateways.

### 3.1 Product category

The product is:

- a resource inventory;
- a reservation and policy service;
- a browser application;
- an agent-facing API;
- an audit source;
- a future entitlement authority for machine gateways.

The product is not:

- Slurm or a replacement for Slurm;
- a process launcher;
- a remote shell service;
- a GPU monitoring system;
- an appointment/salon application;
- a public anonymous booking page;
- a general commercial scheduling SaaS product.

## 4. Stakeholders and actors

### Human roles

- **Member:** browses permitted assets and manages own reservations.
- **Resource manager:** maintains selected assets, availability, and policies; sees reservations for those assets.
- **Administrator:** manages users, groups, global settings, tokens, policies, and migration.
- **Auditor/read-only operator:** can inspect inventory, reservations, and audit evidence without mutation authority.

### Machine roles

- **User agent:** acts on behalf of a human or project through a scoped API token.
- **Service account:** non-human principal with a responsible owner, explicit scopes, expiry, and resource restrictions.
- **Execution gateway, future:** deterministic service running near a machine; verifies a reservation before accepting an execution request.
- **Inventory/probe agent, future:** reports physical state such as reachability and accelerator metadata. It does not create reservation entitlement.

## 5. Goals

### G1. Unified behavior

Human and machine clients must call the same reservation and policy operations. A reservation cannot be accepted through one interface and rejected by another under the same facts.

### G2. Correct concurrency

Exclusive asset reservations must remain conflict-free under concurrent requests. Database constraints, not UI assumptions, provide the final guarantee.

### G3. Professional authentication and authorization

Humans use secure sessions. Agents use separately revocable, expiring, scoped bearer tokens. Every action is authorized against the principal, asset, group/project, and requested operation.

### G4. Agent-native API

The API is versioned, documented by OpenAPI, idempotent for mutations, stable in its error format, and usable without browser automation.

### G5. Useful human experience

The web application clearly answers:

- what assets exist;
- what is available now or later;
- who may reserve an asset;
- why a request is rejected;
- what reservations the current user owns;
- how to cancel or release them.

### G6. Auditable governance

Reservation, asset, policy, permission, and token lifecycle mutations are attributable and reviewable.

### G7. Deployability and recovery

The service can be installed on an ordinary Linux server, configured through documented secrets and environment settings, backed up, restored, monitored, and upgraded without hidden state.

### G8. Migration without legacy contamination

Import useful resource identity and approved reservation history while discarding salon-specific concepts and avoiding uncontrolled import of private contact data.

## 6. Non-goals for the first release

- workload execution or SSH credential handling;
- physical GPU locking or process termination;
- real-time utilization-aware allocation;
- preemption and priority queues;
- usage billing;
- multi-institution tenancy;
- recurring reservations;
- arbitrary capacity sharing within one GPU;
- automatic SmartScheduling browser operation after cutover;
- public anonymous bookings;
- phone-number collection;
- a native mobile application;
- complex email/SMS notification infrastructure;
- Redis, Celery, Kafka, Kubernetes, or microservices.

## 7. Core use cases

### UC1. Human creates a reservation

1. User authenticates.
2. User filters visible assets.
3. User chooses start/end and purpose.
4. Server evaluates policy and attempts one transaction.
5. PostgreSQL enforces non-overlap.
6. User receives a confirmed reservation or a clear conflict/policy error.
7. Audit evidence is written.

### UC2. Agent creates a short reservation

1. Agent authenticates with a scoped token.
2. Agent lists assets and availability.
3. Agent sends an idempotent reservation request.
4. Server verifies token scope, owner policy, time range, and asset state.
5. Server creates the reservation atomically or returns `409`.
6. Agent records the reservation ID and expiry.
7. Agent releases early when work finishes.

### UC3. Administrator takes an asset out of service

1. Administrator marks an asset unavailable or creates a maintenance block.
2. The operation is audited.
3. New reservations are rejected for the blocked interval.
4. Existing affected reservations are surfaced for explicit resolution; they are not silently deleted.

### UC4. Future execution gateway verifies entitlement

1. Client presents a reservation ID and its own gateway credential.
2. Gateway asks the reservation service whether the reservation is valid for the requested asset and current time.
3. The reservation service returns a minimal allow/deny decision with correlation data.
4. Gateway independently verifies physical GPU state before execution.

This integration is designed now but implemented after the reservation MVP.

## 8. Functional requirements

### Inventory

- hierarchical assets: machine parent and reservable children such as GPUs;
- stable opaque IDs and human-readable slugs/names;
- kind, capabilities, location, active state, and arbitrary validated metadata;
- tags and filters;
- legacy provenance fields for migration;
- no inference of device identity from display text.

### Availability

- default and per-asset timezone;
- regular availability rules, initially 24/7 for compute assets;
- maintenance/blackout intervals;
- existing reservations;
- policy-aware available-start calculation;
- all computation uses aware datetimes and half-open ranges.

### Reservations

- create, retrieve, list, cancel before start, and release early;
- purpose and optional project/group association;
- source classification: web, API, admin, migration;
- immutable identity and creation facts;
- explicit state transitions;
- no hard deletion in ordinary workflows;
- conflict response with stable machine-readable code;
- idempotency for API mutations.

### Policy

Initial policies must be able to express:

- minimum and maximum duration;
- booking horizon;
- earliest allowed start;
- cancellation cutoff;
- maximum concurrent/upcoming reservations per principal;
- allowed users/groups/projects;
- asset active/maintenance state;
- whether purpose is required.

Policy resolution must be deterministic and testable. Start with one global default plus per-asset overrides; do not build a generic policy language.

### Authentication and authorization

- custom user model from the first migration;
- email-based human identity for the local-auth MVP;
- roles and groups;
- future OIDC integration point;
- separately managed API tokens with prefix, owner, scopes, expiry, last-used time, and one-way verifier;
- object-level authorization;
- administrator token revocation.

### Audit

Capture:

- principal and authentication method;
- action and target type/ID;
- timestamp;
- correlation/request ID;
- source IP or privacy-reviewed network metadata;
- safe before/after summary;
- no bearer tokens, passwords, cookies, or private request bodies.

### Administration

- Django admin for low-level operations during early milestones;
- purpose-built views for common asset, policy, and reservation management before beta;
- safe user/token lifecycle;
- export of inventory and reservations in an approved format;
- maintenance/blackout management.

## 9. Quality attributes

### Correctness

Reservation overlap is a transactional invariant. Timezone and daylight-saving behavior are explicitly tested. Policy decisions are deterministic.

### Security

Least privilege, secure sessions, one-way token storage, CSRF, HTTPS, explicit CORS policy, no public mutation endpoints, and safe logging are baseline requirements.

### Privacy

Collect only data needed to authenticate, contact, authorize, and audit. Do not require phone numbers. Define retention before importing legacy clients or historical appointments.

### Reliability

A single application instance may be sufficient initially, but correctness must survive multiple web workers. PostgreSQL remains the consistency authority.

### Operability

Provide liveness/readiness endpoints, structured logs, migrations, backup/restore procedures, deployment configuration, and upgrade/rollback notes.

### Maintainability

Prefer a boring monolith, few dependencies, explicit services, typed code where practical, small PRs, generated API schema, ADRs, and comprehensive tests.

### Accessibility

Human workflows target WCAG 2.2 AA principles: semantic HTML, keyboard navigation, visible focus, understandable validation, color-independent status, and responsive layout.

## 10. Architecture decision

### Chosen stack

- Python 3.13;
- Django 5.2 LTS;
- Django REST Framework 3.16;
- PostgreSQL 17;
- psycopg 3;
- generated OpenAPI;
- server-rendered templates with progressive enhancement;
- `uv` and committed lockfile;
- pytest, pytest-django, Ruff, mypy/django-stubs, and PostgreSQL integration tests;
- Docker Compose deployment behind Caddy or Nginx.

### Why this shape

Django supplies mature authentication, sessions, CSRF, forms, migrations, admin, and permission foundations needed by a human-and-machine institutional application. DRF provides a conventional API layer. PostgreSQL supplies range types and exclusion constraints required for robust reservation concurrency. A modular monolith keeps deployment and transaction boundaries simple while leaving clear future integration seams.

### Deferred infrastructure

Do not introduce Redis/Celery until a measured requirement exists for asynchronous notifications or expensive background work. Periodic housekeeping can initially run as an idempotent Django management command under a systemd timer or cron.

## 11. Data model summary

Primary entities:

- `User`
- `Group` / `Project` and memberships
- `ApiToken`
- `Asset` with optional parent asset
- `AssetTag` and capability metadata
- `AvailabilityRule`
- `Blackout`
- `ReservationPolicy`
- `Reservation`
- `AuditEvent`

Use UUID primary keys for public domain objects. Use PostgreSQL `tstzrange` semantics and an exclusion constraint for active blocking reservations on exclusive assets.

Full detail is in `docs/domain-model.md`.

## 12. Human and agent contract

The human UI is not a separate scheduling implementation. Views submit commands to the same service layer used by the REST API. The agent API must not scrape HTML or depend on visual labels.

Initial API surface:

- list/retrieve assets;
- query asset availability;
- list/create/retrieve reservations;
- cancel and release own reservations;
- inspect current principal and effective scopes.

A later atomic allocation endpoint may select one asset from a capability filter. Exact-time reservation comes first; a conflict returns `409` and is safe to retry with a new time or asset.

## 13. Security and trust boundaries

Trust boundaries:

1. public Internet to reverse proxy;
2. browser session to web application;
3. bearer-token client to API;
4. application to PostgreSQL;
5. future gateway to reservation-verification interface;
6. administrators to privileged operations.

No production OpenAI key, SmartScheduling password/cookie, SSH private key, or machine root credential belongs in this application or its repository.

Detailed threats and controls are in `docs/security-model.md`.

## 14. Migration approach

1. Import and verify sanitized inventory.
2. Add physical identifiers manually or through an approved inventory tool.
3. Decide whether historical reservations are operationally necessary.
4. Export approved data through administrator-supported paths, not secret URLs or copied cookies.
5. Dry-run migration and produce reconciliation totals.
6. Run both systems briefly with one authoritative writer.
7. Cut over and retain the legacy account read-only for a defined period.
8. Remove legacy automation after validation.

Do not automatically import phone numbers, arbitrary client notes, or all historical client records. See `docs/migration-from-smartscheduling.md`.

## 15. Initial release plan

### Bootstrap merge

Repository constitution, architecture, seed inventory, templates, and Codex work order.

### Milestone A: executable foundation

Django scaffold, custom user, PostgreSQL development environment, health endpoints, generated OpenAPI shell, CI, and deployment skeleton.

### Milestone B: inventory and reservation core

Assets, policies, reservations, database conflict invariant, audit events, and administrator interfaces.

### Milestone C: unified human/API MVP

Human reservation UI, scoped tokens, API, idempotency, cancellation/release, and end-to-end tests.

### Milestone D: migration and operational beta

Inventory migration, optional approved reservation import, backups, restore test, monitoring, security review, and beta deployment.

### Milestone E: execution integration

Separate, deterministic Neumann or other machine gateway verifies reservations. This is not required for the reservation-system beta.

## 16. Alpha acceptance criteria

The project may call itself an internal alpha only when:

- a clean Linux environment can start the app and PostgreSQL from documented commands;
- humans can authenticate and reserve an authorized asset;
- agents can authenticate with a scoped token and perform the same operation;
- overlapping requests cannot both commit, including a concurrent test;
- back-to-back ranges are accepted;
- cancellation and early release make future time available and retain history;
- unauthorized users/tokens cannot read or mutate protected resources;
- OpenAPI is generated and exercised by API tests;
- audit records exist for all core mutations;
- no private legacy client data is in the repository;
- CI is green;
- limitations are documented.

## 17. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Agent and web paths drift | One domain service layer and shared tests |
| Race creates double booking | PostgreSQL exclusion constraint plus transaction tests |
| Legacy IDs map to wrong GPU | Opaque new IDs; explicit verified mapping; no suffix inference |
| Tokens leak | One-time display, one-way verifier, redacted logs, expiry, scopes |
| Reservation hoarding | duration/horizon/concurrency policy and audit |
| Timezone/DST defects | UTC storage, half-open intervals, dedicated boundary tests |
| Overbuilt architecture | modular monolith; no broker/microservice without ADR |
| Weak deployment recovery | automated backup, documented restore, tested restore gate |
| Codex scope creep | `AGENTS.md`, issue work orders, one PR per task, human merge gate |
| Private-data migration | explicit approval, minimization, dry-run reconciliation |

## 18. Open decisions

These do not block PR 1 but must be resolved before relevant features:

- institutional OIDC provider, claims, and group mapping;
- authoritative list of users/projects and who may create service accounts;
- final global duration, horizon, and concurrency defaults;
- notification requirements;
- data retention for reservations and audit events;
- production DNS, hosting jurisdiction, backup destination, and administrator access path;
- exact physical identifiers and hostnames for each asset;
- whether any non-compute legacy resources should be imported;
- cutover date and historical-data scope.

## 19. Development governance

The repository follows the OAP workflow in `docs/oap-workflow.md`:

- human maintains intent, risk, and merge authority;
- strategic model maintains architecture, work orders, and evidence review;
- Codex programming agent implements one approved issue through one PR;
- repository, PRs, CI, ADRs, and handoffs are durable truth;
- no agent self-merge;
- skipped or unrun checks remain unknown, not passed.
