# ARCHITECTURE — SLAIF Asset Reservation

**New consolidated canonical edition for workflow conversion.** This is not a byte-identical copy
of a previously approved root architecture: no root ARCHITECTURE.md existed in the inspected tree.
The accepted `docs/architecture.md` is preserved unchanged in `sources/repository/docs-architecture.md`
(Git blob `246870a7771452ce3878c228b9ad7ffd8e71eda0`). This edition consolidates that design with
implemented Work Orders 0001–0013 and explicitly labels future scope and proof gaps. It changes no
application behavior. Its adoption is part of the conversion review, not retrospective approval.

Observed software revision: `1fcc2c91d793556a91711365abef562604b62f84` (main, merged PR27).
Repository: private `ulfe-lmi/slaif-asset-reservation`. Requirement IDs SAR-001–SAR-038 are stable;
new editions append IDs and record controlled changes rather than silently repurpose them.

## A-01. System boundary and purpose

The product is a durable laboratory asset reservation authority. It replaces the wrong-shaped
salon scheduler workflow with authenticated human and agent access to a shared policy/booking
engine. The domain centers on exclusive time on assets, not employees, treatments or phone-first
clients. Machines may parent GPU/device records. A reservation is an entitlement recorded by this
service, not proof that an operating system process has obeyed it.

Human members request and inspect their own reservations; human staff manage inventory/policies,
blackouts and permitted cross-user lifecycle operations; software agents use human-owned expiring
tokens. Future deterministic gateways could verify entitlement before admitting jobs and would
still own actual GPU/process isolation and physical-state validation. A gateway, GPU inference
server, Slurm adapter, discovery probe or payment service is not hidden inside this monolith.
No LLM/provider model is required by the product runtime. Codex is a development client, not a
reservation principal type or an application decision engine.

The original Neumann motivation (shared four-A100 laboratory machine and deterministic gateway)
is preserved as domain context. This architecture does not authorize access to Neumann, other lab
machines, an inference endpoint, live SmartScheduling, or a production deployment. Names and
GPU descriptions in the sanitized bootstrap inventory are provenance/labels, not verified hardware.

## A-02. Two planes, deliberately separate

```text
PRODUCT PLANE (existing application, preserved)
  human browser -------------> Django web/member adapters ---+
  staff browser -------------> management_ui adapters --------+-> shared domain services
  agent bearer API client ---> DRF api adapters --------------+        |
  synthetic import command --> legacy_import service --------+        v
                                                    PostgreSQL transactions/ranges/audit

DEVELOPMENT PLANE (this conversion; initially inactive)
  accountable human -> Codex STRATEGIC (separate home)
                           | exact immutable work order + active pointer
                           | control.fifo two-byte wakeup
                           v
                       fresh Codex CODING (existing repository)
                           | bounded implementation/tests + PR + final report-only commit
                           | response.fifo two-byte wakeup
                           v
                       strategic exact-head review + delegated development merge
  independent closure auditor -> architecture-to-exact-main evidence -> human target gate
```

No development FIFO, agent credential, control socket, role-home directory or prompt becomes a
Django endpoint, database authority, Docker production mount or user-facing API. Governance helpers
live under oap/ and run only in the approved development runtime. The product Dockerfile must not
be broadened to copy private control-plane homes, tokens, logs, FIFOs or installation receipts.

## A-03. Stack and topology

The declared stack at this revision is Python `>=3.13,<3.14`, Django `>=5.2,<5.3`, DRF
`>=3.16,<3.18`, PostgreSQL17, uv with a committed lockfile, psycopg, Gunicorn, WhiteNoise,
PyYAML/jsonschema, drf-spectacular plus its local sidecar. Tests use pytest/pytest-django,
Playwright, coverage, Ruff, mypy/django-stubs and pip-audit. These are observed constraints, not a
request to upgrade dependencies. Exact resolved versions come from the preserved uv.lock.

The intended service deployment is a Linux host: HTTPS reverse proxy (Caddy example) -> Gunicorn
Django application -> private PostgreSQL. The runtime image uses UID:GID 10001:10001 and includes
collected member/admin/Swagger assets and sanitized bootstrap files. `compose.yaml` is development;
`compose.production.example.yaml` is an example, not proof of deployment. App host port is
parameterized by SLAIF_APP_HOST_PORT with ordinary default 8000; rehearsal chooses its own single
loopback port via SLAIF_REHEARSAL_PORT. PostgreSQL must not be publicly published by the production
shape. Operator-owned TLS, real secrets, firewall/network and backup storage remain unqualified.

There is no application queue, scheduler, Redis/Celery, monitoring vendor, OIDC tenant or email
relay configured by this conversion. Documentation suggesting cron/systemd describes an operator
option, not an installed scheduler. Agent role homes/FIFOs should be on local POSIX storage, not
unqualified NFS/SMB mounts; qualify locking, SQLite client state and FIFO semantics rather than
assuming all mounted homes behave locally.

## A-04. Implemented modules and ownership

| Package under src/slaif_reservation | Implemented responsibility | Excluded responsibility |
|---|---|---|
| accounts | UUID/email users, timezone validation, API token model/helpers/services, metadata admin | project/membership authorization and service-account token issuance are deferred |
| assets | Asset/AssetTag hierarchy, safe read selectors, staff-session API, sanitized import/admin | online probing, inferred CUDA identity, scheduling writes |
| reservations | ReservationPolicy, Reservation, MaintenanceBlackout, UTC/time utilities, transactional services, migrations | HTTP forms/serialization; physical execution |
| audit | bounded event model, append operations and metadata validators | raw request retention, credential storage, privileged-DB tamper resistance |
| web | session/profile/dashboard/member assets/availability/reservation/token views and local templates | duplicated policy evaluation; staff member-route bypass |
| api | explicit bearer adapters, serializers/permissions, problem details, idempotency and operational commands | global bearer access; admin/token lifecycle REST |
| management_ui | staff forms/selectors/views for policies/blackouts/reservations/audit export | unrestricted ORM editing or delegated resource roles |
| legacy_import | strict synthetic parsing/mapping/planning/apply/provenance/reports/commands | live exports, private people autocreation, scraping |
| config | settings/URL/WSGI/ASGI/logging/health/operational checks | domain ownership or production authorization |

The old architecture's module table included future membership and availability-rule responsibilities
as if present. This edition distinguishes them explicitly: MaintenanceBlackout is in reservations;
projects/memberships and full operating-hours rules are not implemented baseline capabilities.

## A-05. Data ownership and lifecycle

**Users.** The custom UUID user model owns email identity, active/staff/service-account flags and a
validated display timezone. Case-insensitive identity uniqueness is an existing constraint.
Manual account administration is supported; self-registration, OIDC association and reset/email
workflows are deferred. Staff role is operational access, not automatic cross-user rights everywhere.

**Inventory.** Asset records own public UUID/slug/display identity, kind, optional parent, active/
reservable/booking mode, tags/capabilities, verification state and bounded legacy provenance.
Preserve nullable/unknown physical locator data. Legacy source and identifier are paired meaningful
values or both null. Sanitized import must validate before writing, be idempotent and reject
conflicting mapping instead of silently changing identity. Bootstrap data carries 17 machine groups
and 30 GPU child entries historically imported as 47 assets; recheck current input counts at
installation. `chatgptpro` is excluded, not converted to a fictitious device. The explicit
`neumanngpu4` mapping is `neumann-gpu-0`, not a CUDA index inference.

**Policies.** Policy rows govern duration, horizon, lead, cancellation cutoff, upcoming/concurrent
counts and purpose requirements. Resolution is active exact asset, parent machine, global fallback;
absence/ambiguity fails closed. Preserve the implemented unique active-scope constraints. There is
no institution-wide guessed policy seeded by bootstrap, and no implicit grant to every resource
through a token scope alone.

**Reservations.** Reservation identity/owner/asset/original interval/history remain durable.
Confirmed, cancelled and released are stored states; active/upcoming/completed are time-derived
lifecycle labels. start_at/end_at are original aware instants. effective_end_at starts as end_at;
release reduces it and records released_at. Confirmed/released rows block the consumed prefix;
cancelled rows do not block. Source web/api/admin/migration and audit correlation preserve causality.
Hard deletion and ordinary ORM history rewriting are prohibited workflows. Pure Python markers and
managers are defense-in-depth application controls, not a boundary against a database administrator.

**Blackouts.** A MaintenanceBlackout owns asset, creator, reason, aware half-open time range, active/
deactivation timestamps and actor. Deactivation retains history. Management confirmation handles
existing affected reservations conservatively and does not auto-cancel them. Current exact-asset
checks must not be casually generalized to parent/child physical exclusion without an approved
product decision; policy inheritance is not automatically blackout inheritance.

**Audit.** AuditEvent records occurred_at, action, actor reference, target type/UUID, source,
correlation and safe bounded metadata. Append-only application/ORM/admin behavior is not a
cryptographic ledger or DB-trigger guarantee. Tokens, credentials, private notes, raw payloads and
physical locators are forbidden metadata. Export applies allowlists/redaction, bounded filters and
CSV safety. Identity shown to staff on a detail page is not permission to export unrestricted data.

**API idempotency.** IdempotencyRecord owns user/token/action/key uniqueness, canonical request
hash, method/path, response status/safe body, safe header allowlist, target/correlation and expiry.
No raw request or credential storage. A matching expired row fails explicitly until cleanup;
purging it permits later reuse under the documented retention semantics, not permanent exactly-once
delivery. Cancellation/release replay returns the original accepted response rather than rerunning
lifecycle decisions against the new time. Stored replay content never grants cross-owner access.

**Legacy import.** LegacyImportBatch/LegacyImportRecord preserve safe source checksums, summary,
mode/status and source+legacy-ID mapping without raw export payload. They are separate from API
idempotency. Source changes for an imported ID are classified, not overwritten. Apply records actual
final classifications and reservation references only where appropriate; the plan is advisory.

## A-06. Transactional reservation flows

Create: adapter authenticates/authorizes, validates shape and aware times, supplies principal and
source/correlation, then the service opens a transaction, normalizes UTC and locks the principal,
asset and selected policy before applying constraints/counters. Early reservation/blackout checks
provide useful errors; the named PostgreSQL GiST exclusion constraint is the final concurrent
reservation-vs-reservation arbiter. The reservation and success audit commit together. Unknown
integrity failures remain errors for investigation; never reclassify every DB failure as conflict.

Cancellation: owner or specifically permitted staff operation locks authoritative state and applies
future/cutoff rules. It records cancellation and audit without deleting original history.
Release: authorized lifecycle reduces future entitlement and records the consumed effective end;
it must not strand a reservation merely because the asset or former policy became inactive.

Concurrency across policy changes, blackout creation, API idempotency, legacy apply and ordinary
booking needs consistent locking and boundary-faithful tests. Locking a row found by a query does
not lock the absence of future rows; PostgreSQL reservation exclusion does not by itself enforce
blackout-vs-reservation ordering. This is an explicit verification obligation, not a claim that
all cross-service races have already been proven. Do not change locking order independently in
one adapter without reviewing the other write paths.

## A-07. Human and management workflows

Existing member routes include login, POST logout, profile, dashboard, asset browsing, availability,
reservation create/list/detail/cancel/release and token list/new/revoke. Browser mutations use CSRF;
GET is read-only. Invalid/inactive/service-account sessions must terminate safely. A malformed stored
timezone leads to profile correction; UTC machine-readable time markup coexists with localized
visible labels and an explicit display zone. Lists are bounded and upcoming reservations sort
soonest first. A staff session on member routes remains owner-scoped.

Management routes under /manage/ require active staff and non-service-account identity. Forms use
existing audited policy/blackout/lifecycle services. Policy display distinguishes exact/parent/global
resolution and missing/ambiguous state. Blackout creation shows affected reservations and requires
explicit confirmation without automatic cancellation. Reservation management filters cover asset,
user text, status/lifecycle and validated aware windows. Audit list/export reuse validated filters;
navigation-only parameters do not disable bounded default windows. Django admin remains read-only
or service-backed for protected models; it is not a bypass route.

## A-08. Token and API interface map

| Interface | Authentication/authority | Behavior |
|---|---|---|
| /api/v1/ | existing root behavior | preserve current root, no implicit protected operation |
| /api/v1/me/ | explicit bearer; active allowed owner | safe principal/token context, no verifier/pepper/admin flags |
| /api/v1/assets/ and /api/v1/assets/{id}/ | staff session | preserve this limitation; assets:read scope alone does not enable discovery |
| /api/v1/assets/{id}/availability/ | bearer + availability:read | advisory private intervals, bounded dates/days/timezone |
| /api/v1/reservations/ GET | bearer + reservations:read | owner-only filtered bounded listing |
| /api/v1/reservations/ POST | bearer + reservations:create | known fields, aware times, required idempotency; 201 + safe Location |
| /api/v1/reservations/{id}/ GET | bearer + reservations:read | owner-only representation/non-disclosing 404 |
| .../{id}/cancel/ POST | bearer + reservations:cancel | service-backed owner mutation with idempotency |
| .../{id}/release/ POST | bearer + reservations:release | service-backed owner mutation with idempotency |
| /api/schema/ and /api/docs/ | configured private staff policy | local Swagger assets; no accidental public production docs |

Scopes are `assets:read`, `availability:read`, `reservations:read`, `reservations:create`,
`reservations:cancel`, `reservations:release`; do not invent wildcards/admin/group restrictions.
Authentication distinguishes no/other scheme from a malformed Bearer attempt, preserves unrelated
headers for downstream authenticators, redacts Bearer metadata, compares HMAC with constant-time
helper and enforces owner/revocation/exclusive expiry. Last-use write is isolated best-effort and
not an audit event. One-time display protects repr/inner exception handling and browser Back cache.
Pepper replacement invalidates existing tokens; there is no accepted key-ring rotation design.

Mutation adapters validate scope, serializer, idempotency and service results; they do not duplicate
business rules. The canonical request hash/scoped key binds the request. Exact same request replays
status/body/original correlation and safe Location, changed request returns idempotency_conflict,
expired matching row returns idempotency_expired without a new write. Real concurrent tests must
prove one mutation and one success audit. X-Request-ID accepts a UUID or the server generates one.
Problem details include type/title/status/code/detail/correlation with no raw exceptions. Generated
OpenAPI describes only implemented surfaces; no management/token/admin REST routes are introduced.

## A-09. Availability and privacy

Shared availability resolves the active/reservable asset and policy; builds a validated 1–7-day
local window; normalizes instants; clips confirmed/released reservation prefixes and active
blackouts; merges intersecting/adjacent busy ranges; computes free complement and policy-visible
latest-start constraints. Cancelled and deactivated blackout rows do not block. Local midnight can
itself be ambiguous/nonexistent in some zones; never silently guess a boundary. Reads remain
advisory because competing bookings or maintenance can occur after the response.

Ordinary members and bearer callers cannot learn another user's email/name/purpose/reason/reservation
UUID from unavailability. Private blackout reasons stay staff-only. Policy/access state, not a
hidden UI button, determines permissible operations. Pilot selection by inactive/nonreservable flags
is a limited operational convention, not implemented project/group authorization.

## A-10. Operations, diagnostics and recovery

Production settings fail closed for missing/short/known-placeholder SECRET_KEY and pepper, equality
between the two, absent DB/hosts and invalid security fields. HSTS defaults remain conservative
opt-in. Production docs are private. WSGI/ASGI default to production; explicit local/test settings
are a separate environment. Keep generated env.production, secret files, dumps and browser artifacts
out of Git and Docker contexts.

/health/live reports process responsiveness; /health/ready additionally checks DB/migration state.
operational_check covers DB, migrations, static assets, sanitized inventory and cleanup command
registration. pilot_readiness_check reports aggregate counts and strict/non-strict gates without
identifiers or mutation. A successful readiness count is not authentication, a resource grant or a
backup/restore proof. At the inspected revision, count queries precede the DB-readiness helper and
policy-resolution errors use a broad catch; failure-boundary qualification is a follow-up evidence
candidate, not something this conversion silently fixes.

Production JSON logs and correlation are operational breadcrumbs, not raw forensic dumps. No
Authorization/cookies/payload/private free text. Backup/restore commands use PostgreSQL tools,
default dry-run and explicit apply. The documented isolated restore drill remains to be proved with
actual fixture data and result comparison before any recovery guarantee. Rehearsal uses production
settings with synthetic local values and intentionally no real TLS; it validates image, migrations,
bootstrap dry-run, health/login/anonymous management/API failure and schema. It is not evidence for
an authenticated live pilot, public TLS, real identity or network enforcement.

The existing rehearsal script writes temporary deployment files and owns disposable Compose
resources; its overwrite/refusal/cleanup proof must include symlinks, pre-existing resources and
partial failure. The baseline operational test suite writes a fixture at repository deployment
paths, so never run it against a valuable checkout containing real env/secrets. Use a disposable
copy until its ownership boundary has been explicitly qualified. No default `docker compose down
-v` against an unknown project is allowed. Sequential product pytest invocations avoid the
historically observed test-DB contention from parallel independent runs.

Upgrade: add reviewed forward migrations; never edit merged migrations. Back up before real changes,
qualify fresh and upgrade paths on isolated DBs, and document rollback/restore limitations. Reverting
Git code does not undo database changes or release risk. No real restore, secrets rotation or
production data migration is delegated merely by a development work order.

## A-11. Synthetic legacy migration

The parser accepts the explicitly defined fake fixture format, not a claim to support arbitrary
vendor exports. It rejects URL schemes, unsupported extensions, unknown/private fields, duplicate
legacy IDs, impossible/naive/ambiguous times according to format and explicit timezone. Mapping
resolves existing users/assets and classifies unknown/ambiguous/inactive cases without echoing raw
identity. No user autocreation, hardware inference or live service request is permitted.

Plan is read-only and produces deterministic safe categories. Apply is explicit, transactionally
revalidates import-record idempotency, current asset/user/policy, blackouts and blocking reservations,
then writes reservation/audit/import record together. Past completed records have only the documented
migration exception; future bookings obey current policy. Changed source data is reported, not
silently reconciled. Source+legacy ID and DB range constraints remain final consistency layers;
concurrent import and ordinary service lock interaction requires real qualification. Report files
are explicit local paths with safe final counts, batch/mode and classifications, never raw notes,
phones, emails, cookies or original export rows.

## A-12. Evolution and source conflicts

Do not rewrite the original accepted architecture snapshot. Before adopting this root as canonical,
archive old docs/architecture.md exactly and replace its live path with a short link to this edition.
The conflicting legacy statements are recorded in SOURCE-MAP.md: deferred reservation APIs versus
later implemented API flow; proposed membership/restrictions versus explicit alpha deferral;
early generic end_at intervals versus ADR0007 effective_end_at; operational targets versus no real
deployment; human-only development merge versus the newly requested conditional strategic merge.
This is an explicit reconciliation, not permission to alter human-owned product meaning.

Architecture evolution inside the agreed monolith/entitlement boundary is strategic D0/D1 work;
changed product meaning, external exposure, sensitive data, new institutional rights and real
infrastructure are D2. A source hash proves identity, not authority. New requirements link to
human/architecture/evidence/independent-audit/CRITICAL provenance. Existing IDs must remain
implemented, explicitly deferred, or unproven; a revised task queue cannot erase an invariant.

## A-13. Verification, milestones and confidence

Use exact current source/commit plus real entry-point evidence. Product regression requires the
four preserved CI jobs and appropriate unit, PostgreSQL concurrency, browser, API, migration and
operational suites. Harness tests use disposable Git/remote/client/FIFO fixtures; they cannot
certify Django functionality, client behavior, independent judgment or deployment readiness.

M-CONVERSION requires a reviewed migration diff, full helper acceptance, an explicitly authorized
round-trip canary and an independent exact-merged-revision conversion audit. Pre-activation candidate
review and human adoption permit only the selected canary, not a claim that this milestone is already
complete. Final human M-CONVERSION acceptance follows canary evidence and current-revision ICA. M-EXISTING is the preserved historical internal-alpha baseline, not re-certified
by this package. M-LOCAL-PILOT-EVIDENCE is a proposed future target for actual local end-to-end and
restore evidence; M-EXTERNAL-PILOT and release require separate human scope and authorization.
Record independent audit rows as IMPLEMENTED/PARTIAL/ABSENT/UNPROVEN at exact audited revision.
Initially all rows below are UNPROVEN for a new ICA, even where source/test existence is observed.
The historical WO0010 report did not establish a separate independent auditor/context provenance,
so do not rebrand it as the new Concentrated OAP ICA.

## A-14. Stable requirements and enforcement map

Every law below is preserved product scope or an explicit conversion invariant. Source references
refer to the pre-conversion repository unless marked generator/current instruction. Enforcement
paths below are relative to src/slaif_reservation unless otherwise stated. They are an evidence
starting point; presence of a path does not constitute a passing test.

### SAR-001 — One reservation authority

Humans and authenticated software agents share scheduling records and authoritative domain operations. Do not introduce parallel booking logic.

Source: docs/architecture.md §§1,4; conversation original product decision.

Inspect: `src/slaif_reservation/reservations/services.py`. Evidence: Web/API/management create-cancel-release parity; no adapter-only enforcement.
Initial independent-closure classification: **UNPROVEN**.

### SAR-002 — Entitlement is not execution

The reservation monolith does not run jobs, SSH, model inference, containers on lab machines, GPU allocation enforcement or power control. A future deterministic gateway is a separate trust boundary.

Source: docs/architecture.md §§1,12; human separation of local Codex and Neumann gateway.

Inspect: `config/urls.py; api/urls.py; application imports`. Evidence: Inspect actual routes/imports; absence of execution side effects.
Initial independent-closure classification: **UNPROVEN**.

### SAR-003 — Stable resource identity

UUIDs identify public records. Preserve hierarchical machine/child assets, existing slugs and provenance. Never infer CUDA index, GPU UUID, hostname or readiness from legacy suffixes.

Source: AGENTS.md domain invariants 2,12; data/bootstrap/assets.yaml.

Inspect: `assets/models.py; assets/bootstrap.py`. Evidence: Idempotent import; neumanngpu4 mapping; no ordinal inference.
Initial independent-closure classification: **UNPROVEN**.

### SAR-004 — Asset verification

Sanitized bootstrap inventory is not a physical probe or online inventory. Preserve verification flags, explicit unknown locators, inactive/nonreservable rejection and excluded chatgptpro entry.

Source: data/bootstrap/assets.yaml warnings; conversation WO0002.

Inspect: `assets/bootstrap.py; assets/selectors.py`. Evidence: Safe import conflict/dry-run/verification-field preservation tests.
Initial independent-closure classification: **UNPROVEN**.

### SAR-005 — UTC and DST

Store/compare aware UTC instants; display explicit user timezone, default Europe/Ljubljana. Reject naive API instants and ambiguous/nonexistent local times unless an explicit supported occurrence is supplied; invalid stored zones require correction, not silent fallback.

Source: ADRs 0006–0008; conversation timezone repairs.

Inspect: `reservations/time_utils.py; accounts/validators.py; web/forms.py`. Evidence: Spring gap, autumn fold, malformed/overlong/NUL zone, UTC arithmetic and visible zone.
Initial independent-closure classification: **UNPROVEN**.

### SAR-006 — Half-open effective-end history

Original end_at is immutable; effective_end_at initially equals it. Confirmed/released block [start_at,effective_end_at); release records released_at=effective_end_at; cancelled rows do not block. Never erase the historical consumed interval.

Source: ADR0007; docs/architecture.md §5.

Inspect: `reservations/models.py; migrations/0001_initial.py`. Evidence: Adjacent intervals accepted; released prefix preserved; cancelled free.
Initial independent-closure classification: **UNPROVEN**.

### SAR-007 — PostgreSQL exclusivity

PostgreSQL 17 and btree_gist enforce exclusive same-asset range overlap with reservation_no_overlap_per_asset. Application overlap checks are advisory. Translate only the exact named exclusion failure; unrelated integrity failures are not booking conflicts.

Source: docs/architecture.md §§4,5; observed CI configuration.

Inspect: `reservations/migrations/; reservations/services.py`. Evidence: Real concurrent transactions, named constraint inspection, unrelated error test.
Initial independent-closure classification: **UNPROVEN**.

### SAR-008 — Policies and counters

Resolve active exact-asset, parent-machine then global policy; missing/ambiguous policy fails closed. Ordinary future bookings enforce active human, active/reservable/exclusive asset, duration, lead, horizon, purpose and principal counters; start_at==now is active, not upcoming.

Source: ADRs 0007,0008; reservation service work orders.

Inspect: `reservations/services.py; models.py`. Evidence: Boundary and counter races; missing/ambiguous and inactive-policy tests.
Initial independent-closure classification: **UNPROVEN**.

### SAR-009 — Atomic audited lifecycle

Create/cancel/release and audited policy/token/blackout mutations couple persistence and audit transactionally. An audit failure must roll back its domain mutation. Preserve consistent lock ordering across web/API/management/import paths.

Source: docs/architecture.md §4; conversation audited-service decisions.

Inspect: `reservations/services.py; accounts/services.py; legacy_import/importer.py`. Evidence: Fault injection, rollback of every affected row and audit count, deadlock/race tests.
Initial independent-closure classification: **UNPROVEN**.

### SAR-010 — Reducing entitlement remains possible

Owner or permitted active staff may release an active reservation even after asset or policy deactivation. Cancellation retains the accepted cutoff and ownership rules. No implicit cross-user member/API bypass.

Source: ADR0007; docs/architecture.md §4.3.

Inspect: `reservations/services.py; web/views.py; api/reservation_views.py`. Evidence: Release after deactivation; cancelled/released retry and cutoff tests.
Initial independent-closure classification: **UNPROVEN**.

### SAR-011 — Human session boundary

Only active non-service-account users enter member routes. POST logout/mutations require CSRF; GET never mutates. Disallowed sessions terminate safely without redirect loops. Accounts remain administrator-created.

Source: ADR0008; docs/human-ui.md; conversation WO0004.

Inspect: `web/auth.py; web/views.py; accounts/models.py`. Evidence: Anonymous/inactive/service-account/staff/member matrix; CSRF and method tests.
Initial independent-closure classification: **UNPROVEN**.

### SAR-012 — Member ownership

Member and bearer reservation list/detail/cancel/release are owner-scoped, including staff acting on member/API routes. Other-owner and guessed IDs are non-disclosing 404s.

Source: ADRs 0008,0010; docs/api-contract.md.

Inspect: `web/selectors.py; api/reservation_views.py`. Evidence: Cross-user detail and mutation tests through real adapters.
Initial independent-closure classification: **UNPROVEN**.

### SAR-013 — Management authority

Separate /manage/ active-staff, non-service-account session routes allow audited cross-user lifecycle, policy and blackout operations; no delegated resource-manager role or management REST API is implied.

Source: ADR0011; docs/human-ui.md.

Inspect: `management_ui/auth.py; views.py; reservations/admin.py`. Evidence: Role matrix plus CSRF/GET on every mutation; admin bypass tests.
Initial independent-closure classification: **UNPROVEN**.

### SAR-014 — Token secrecy and lifecycle

Tokens use sar_<uuidhex>_<CSPRNG secret>, at least 256 random bits, HMAC-SHA-256 over full token with a distinct server pepper, constant-time compare, mandatory exclusive expiry, revocation, canonical allowlisted scopes, and best-effort monotonic last use. No plaintext persistence or privileged issuance.

Source: ADR0009; conversation token repairs.

Inspect: `accounts/tokens.py; models.py; services.py; api/authentication.py`. Evidence: Secret/pepper/expiry/revocation/owner/scope matrices; failed auth no last-use mutation.
Initial independent-closure classification: **UNPROVEN**.

### SAR-015 — One-time secret handling

One-time token display is no-store/private/no-referrer, never session/messages/URLs/storage. Preserve history scrubbing and redacted repr/exception frames. Verifiers/peppers/credentials never enter UI, API, audit, logs, report artifacts or trace captures.

Source: ADR0009; conversation PR11 repairs.

Inspect: `web/token templates/static; accounts/tokens.py; config/logging.py`. Evidence: History Back; inner exception reports; recursive audit rejection; output canaries.
Initial independent-closure classification: **UNPROVEN**.

### SAR-016 — Scoped API adapters

Explicit bearer-only /me/, availability, and reservation endpoints use action scopes; authenticator is not global. Existing asset list/detail remain staff-session-only. A valid token alone does not grant admin or asset-discovery access.

Source: ADR0010; docs/api-contract.md.

Inspect: `api/urls.py; permissions.py; assets/api.py`. Evidence: Authentication/scope/ownership matrix, missing surfaces and schema.
Initial independent-closure classification: **UNPROVEN**.

### SAR-017 — Strict API contract

API mutations accept bounded known fields and aware ISO instants, return UTC representations and safe problem details plus UUID correlation. No SQL, constraints, ORM text or other-user identity in errors. Keep v1 compatible.

Source: ADR0010; docs/api-contract.md.

Inspect: `api/serializers.py; problem.py; reservation_views.py`. Evidence: Unknown fields/filter ordering/naive time/malformed JSON/endpoint-specific 404s.
Initial independent-closure classification: **UNPROVEN**.

### SAR-018 — Idempotent API mutations

Create/cancel/release require bounded Idempotency-Key. Same owner/token/action/key and canonical request replays stable status/body/correlation/safe Location; changed request conflicts. Matching expired record fails explicitly until operator cleanup. No duplicate reservation/audit.

Source: ADR0010; conversation PR13 repairs.

Inspect: `api/idempotency.py; api/models.py; api/migrations/`. Evidence: Real concurrent identical/different requests; expiry; safe header replay.
Initial independent-closure classification: **UNPROVEN**.

### SAR-019 — Advisory private availability

Shared availability clips, merges and complements blocking reservations and active blackout ranges under current policy/window. It is advisory, not a hold. Others expose only unavailable time, not identity/email/purpose/reason/UUID.

Source: ADRs 0008,0011; docs/architecture.md §4.

Inspect: `web/availability.py; api/reservation_views.py`. Evidence: Cancelled/released/confirmed clipping, adjacency, blackout merge and privacy.
Initial independent-closure classification: **UNPROVEN**.

### SAR-020 — Blackout integrity

Active maintenance blackouts block overlapping new bookings authoritatively; deactivation preserves history. Confirmation of affected reservations is explicit; blackout creation does not automatically cancel/release them. Validate half-open bounds and audit atomically.

Source: ADR0011; conversation WO0007.

Inspect: `reservations/models.py; services.py; management_ui/`. Evidence: Create-vs-blackout race and adjacent boundary; confirmation; rollback.
Initial independent-closure classification: **UNPROVEN**.

### SAR-021 — Bounded audit evidence

Audit is append-only at application/ORM/admin boundary, not tamper-proof against DB operators. Reject credential-like metadata recursively. Staff browsing/export is filtered, bounded, CSV-safe and privacy-minimized; export is not a raw forensic dump.

Source: ADRs 0007,0009,0011; docs/security-model.md.

Inspect: `audit/models.py; validators.py; management_ui/selectors.py; views.py`. Evidence: Bulk/reconstructed mutation; secret-key/value rejection; export filtering/escaping.
Initial independent-closure classification: **UNPROVEN**.

### SAR-022 — Reproducible monolith

Preserve Python3.13, Django5.2, DRF3.17, PostgreSQL17, uv.lock, Gunicorn, WhiteNoise, local Swagger sidecar and server-rendered views. Add no production dependency or alternate stack without ordered justification/accepted decision.

Source: AGENTS.md accepted baseline; pyproject.toml.

Inspect: `pyproject.toml; uv.lock; Dockerfile`. Evidence: Locked install, lint/type/build/schema tests; no opportunistic upgrades.
Initial independent-closure classification: **UNPROVEN**.

### SAR-023 — Production fail closed

Production requires nonplaceholder distinct secrets/pepper, DB, hosts and validated security settings. Secure cookies/private docs default; HSTS explicit opt-in. Local/test values do not authorize real deployment.

Source: ADR0012; conversation WO0008.

Inspect: `config/env.py; config/settings/production.py; accounts/tokens.py`. Evidence: Subprocess negative settings matrix, ASGI/WSGI fail closed.
Initial independent-closure classification: **UNPROVEN**.

### SAR-024 — Topology and exposure

Target is HTTPS proxy to non-root app to private PostgreSQL. Dev/rehearsal bindings stay loopback. Preserve UID:GID 10001:10001 and local static/bootstrap assets. No production DNS/TLS/host changes or public exposure under a development order.

Source: ADR0012; docs/deployment.md.

Inspect: `compose*.yaml; Dockerfile; deploy/`. Evidence: Rendered config plus actual sockets/image paths; explicit exposure gate.
Initial independent-closure classification: **UNPROVEN**.

### SAR-025 — Health and diagnostics

Liveness has no DB dependency; readiness safely checks DB/migrations. operational_check covers DB/migrations/static/bootstrap/cleanup registration. pilot_readiness_check remains aggregate-only/read-only and not a release certificate.

Source: WO0008,0013; observed pilot_readiness_check source.

Inspect: `config/views.py; operational.py; api/management/commands/`. Evidence: Real CLI disconnected/unmigrated/failure paths and no-write evidence.
Initial independent-closure classification: **UNPROVEN**.

### SAR-026 — Safe logs

Production structured logs contain safe method/path/status/duration/correlation data, never credential headers, cookies, passwords, bodies, purposes, private locators or cancellation reasons. Error logging must not leak via inner exception locals.

Source: ADR0012; docs/security-model.md.

Inspect: `config/logging.py; middleware.py; token exception protections`. Evidence: Hostile sentinels through real log entry points; no raw report leakage.
Initial independent-closure classification: **UNPROVEN**.

### SAR-027 — Recovery tooling

Backup/restore wrap PostgreSQL-native tools and default to validation/dry-run; apply needs explicit authorized isolated target. Idempotency purge defaults dry-run and deletes only expired records with apply. No installed scheduler or proven restore drill is implied by wrappers.

Source: ADR0012; runbooks.

Inspect: `api/management/commands/backup_database.py; restore_database.py; purge_expired_idempotency_records.py`. Evidence: Refusal tests plus isolated real dump/restore round trip before recovery claim.
Initial independent-closure classification: **UNPROVEN**.

### SAR-028 — Synthetic migration boundary

Legacy import accepts only its strict synthetic contract and local paths, rejects URL schemes/private fields/unknown statuses/duplicate IDs/bad times. No scraping, real export processing, credential reuse, user autocreation or inferred physical mapping.

Source: ADR0013; conversation WO0009.

Inspect: `legacy_import/parser.py; mapping.py; management/commands/`. Evidence: URL/path/schema/DST/privacy negatives; unmapped user/asset classifications.
Initial independent-closure classification: **UNPROVEN**.

### SAR-029 — Migration plan is not authority

Dry-run creates no reservation/audit mutation. Explicit apply revalidates current mapped user/asset/policy/blackout/reservation/import-record state transactionally. Source+legacy ID idempotency, changed-input detection, final-result reports, safe audit and full rollback remain required.

Source: ADR0013; conversation PR19 repair.

Inspect: `legacy_import/planner.py; importer.py; models.py`. Evidence: Stale plan mutations, duplicate/changed records, apply report, audit rollback.
Initial independent-closure classification: **UNPROVEN**.

### SAR-030 — Historical import exception

Past completed synthetic records may use only the documented migration exception; future confirmed records obey current policies/exclusivity/blackouts. Cancelled/no-show handling must follow ADR0013 rather than invent blocking history.

Source: ADR0013; source report history.

Inspect: `legacy_import/importer.py; planner.py`. Evidence: Past vs future vs skipped status tests; original interval retained.
Initial independent-closure classification: **UNPROVEN**.

### SAR-031 — Resource ownership in rehearsal

Rehearsal may use only owned disposable files/containers/volumes/ports with no unsafe adoption/deletion of existing env/secrets/resources. Preserve one selected loopback app port and explicit failure cleanup.

Source: WO0011 scope; deploy/rehearse_internal_alpha_deployment.sh.

Inspect: `deploy/rehearse_internal_alpha_deployment.sh; tests/test_operational_hardening.py`. Evidence: Existing files/symlinks/project collision/partial startup; actual Compose merge.
Initial independent-closure classification: **UNPROVEN**.

### SAR-032 — Evidence before readiness

Full/focused/browser/concurrency/operational results name actual revision and commands; CI quality,test,security,container at exact head are required. Prior 419-test report is historical, not proof for new code. Mocked boundaries and row counts alone are limited evidence.

Source: AGENTS.md testing; WO0010; CI source.

Inspect: `tests/; .github/workflows/ci.yml`. Evidence: Real PostgreSQL, real entry-point smoke, negative tests, accurate skipped/blocked statuses.
Initial independent-closure classification: **UNPROVEN**.

### SAR-033 — Preserve existing project

Workflow conversion preserves application bytes, data migrations, Git history, legacy PR/issues and accepted product exclusions. Do not regenerate the app, reopen merged PR27, fabricate old OAP reports or reset numbering/history.

Source: Current human request; live main/CI.

Inspect: `entire tracked application and history`. Evidence: Pre/post manifest diff allowlist; history ancestry; no product writes at bootstrap.
Initial independent-closure classification: **UNPROVEN**.

### SAR-034 — Codex-only role separation

Bootstrap, coding, strategic and ICA have distinct scopes. Operational root is tiny router; both development roles use separately configured Codex homes. No operational CLAUDE.md or Claude launcher; preserved methodology snapshots remain historical.

Source: Current human request; attached generator §§5,12.

Inspect: `AGENTS.md; oap/; strategic home`. Evidence: Instruction inheritance/role-conflict tests; no implicit role switch or fallback.
Initial independent-closure classification: **UNPROVEN**.

### SAR-035 — Private infrastructure boundary

Never access real lab machines/Neumann, private exports, production DBs, long-lived credentials, DNS/TLS or deployment targets to test this conversion. Development model calls and Git publication require separately configured authority; product runtime uses no LLM.

Source: Human separation of gateway; generator authority rules.

Inspect: `runtime constraints; private activation record`. Evidence: Safe fixture-only bootstrap tests; network/resource allowlist; no secret copying.
Initial independent-closure classification: **UNPROVEN**.

### SAR-036 — Deferred product scope stays visible

OIDC/password reset/notifications, projects/memberships/resource restrictions, token/management admin APIs, automatic physical allocation, monitoring stack, scheduler, real migration/cutover and gateway remain deferred. No assistant suggestion or draft silently authorizes them.

Source: Accepted later work orders; docs/roadmap.md; current human preservation request.

Inspect: `PLAN.md deferred scope; source roadmap`. Evidence: Architecture-to-scope matrix; no new surfaces during conversion.
Initial independent-closure classification: **UNPROVEN**.

### SAR-037 — Canonical governance and projection

Maintain canonical PLAN/ARCHITECTURE and preserved prior sources; compact coding projections are coverage-mapped and hash-bound, not independent law. Preserve security/reporting constraints while changing process authority deliberately.

Source: Generator §§4–6; current human request.

Inspect: `oap/governance/; ARCHITECTURE-for-agents.md`. Evidence: Semantic comparison and mechanical drift tests, measured read set.
Initial independent-closure classification: **UNPROVEN**.

### SAR-038 — Human target and ICA

Strategic development merge never means release, deployment, physical-resource entitlement beyond product rules or human milestone acceptance. ICA derives from full architecture and exact merged revision with independent context and applicable DHA gates.

Source: Generator §§7,8,14.

Inspect: `CRITICAL.md; oap/audit/; docs/READINESS.md`. Evidence: Attribution/ICA freshness/target gate tests; no self-certification.
Initial independent-closure classification: **UNPROVEN**.
