# ARCHITECTURE-for-agents — executor projection

Source: root ARCHITECTURE.md, initial SHA-256 `9e7c60e4ef6cee99d5baf20ee5ef6afcff38b10aa2eaa74a5a27084ff515a0c4`.
Scope: preservation and bounded development of existing SLAIF Asset Reservation. Not independent architecture or approval.
Normal coding reads this file, not the full source. A genuine gap goes to strategy for a bounded correction/excerpt.

Existing baseline: private ulfe-lmi/slaif-asset-reservation; main observed 1fcc2c91d793556a91711365abef562604b62f84; WO0001–0013 already complete. Python3.13/Django5.2/DRF3.16/PostgreSQL17; preserve uv.lock. Current conversion is governance only.

**SAR-001 / One reservation authority:** Humans and authenticated software agents share scheduling records and authoritative domain operations. Do not introduce parallel booking logic.

**SAR-002 / Entitlement is not execution:** The reservation monolith does not run jobs, SSH, model inference, containers on lab machines, GPU allocation enforcement or power control. A future deterministic gateway is a separate trust boundary.

**SAR-003 / Stable resource identity:** UUIDs identify public records. Preserve hierarchical machine/child assets, existing slugs and provenance. Never infer CUDA index, GPU UUID, hostname or readiness from legacy suffixes.

**SAR-004 / Asset verification:** Sanitized bootstrap inventory is not a physical probe or online inventory. Preserve verification flags, explicit unknown locators, inactive/nonreservable rejection and excluded chatgptpro entry.

**SAR-005 / UTC and DST:** Store/compare aware UTC instants; display explicit user timezone, default Europe/Ljubljana. Reject naive API instants and ambiguous/nonexistent local times unless an explicit supported occurrence is supplied; invalid stored zones require correction, not silent fallback.

**SAR-006 / Half-open effective-end history:** Original end_at is immutable; effective_end_at initially equals it. Confirmed/released block [start_at,effective_end_at); release records released_at=effective_end_at; cancelled rows do not block. Never erase the historical consumed interval.

**SAR-007 / PostgreSQL exclusivity:** PostgreSQL 17 and btree_gist enforce exclusive same-asset range overlap with reservation_no_overlap_per_asset. Application overlap checks are advisory. Translate only the exact named exclusion failure; unrelated integrity failures are not booking conflicts.

**SAR-008 / Policies and counters:** Resolve active exact-asset, parent-machine then global policy; missing/ambiguous policy fails closed. Ordinary future bookings enforce active human, active/reservable/exclusive asset, duration, lead, horizon, purpose and principal counters; start_at==now is active, not upcoming.

**SAR-009 / Atomic audited lifecycle:** Create/cancel/release and audited policy/token/blackout mutations couple persistence and audit transactionally. An audit failure must roll back its domain mutation. Preserve consistent lock ordering across web/API/management/import paths.

**SAR-010 / Reducing entitlement remains possible:** Owner or permitted active staff may release an active reservation even after asset or policy deactivation. Cancellation retains the accepted cutoff and ownership rules. No implicit cross-user member/API bypass.

**SAR-011 / Human session boundary:** Only active non-service-account users enter member routes. POST logout/mutations require CSRF; GET never mutates. Disallowed sessions terminate safely without redirect loops. Accounts remain administrator-created.

**SAR-012 / Member ownership:** Member and bearer reservation list/detail/cancel/release are owner-scoped, including staff acting on member/API routes. Other-owner and guessed IDs are non-disclosing 404s.

**SAR-013 / Management authority:** Separate /manage/ active-staff, non-service-account session routes allow audited cross-user lifecycle, policy and blackout operations; no delegated resource-manager role or management REST API is implied.

**SAR-014 / Token secrecy and lifecycle:** Tokens use sar_<uuidhex>_<CSPRNG secret>, at least 256 random bits, HMAC-SHA-256 over full token with a distinct server pepper, constant-time compare, mandatory exclusive expiry, revocation, canonical allowlisted scopes, and best-effort monotonic last use. No plaintext persistence or privileged issuance.

**SAR-015 / One-time secret handling:** One-time token display is no-store/private/no-referrer, never session/messages/URLs/storage. Preserve history scrubbing and redacted repr/exception frames. Verifiers/peppers/credentials never enter UI, API, audit, logs, report artifacts or trace captures.

**SAR-016 / Scoped API adapters:** Explicit bearer-only /me/, availability, and reservation endpoints use action scopes; authenticator is not global. Existing asset list/detail remain staff-session-only. A valid token alone does not grant admin or asset-discovery access.

**SAR-017 / Strict API contract:** API mutations accept bounded known fields and aware ISO instants, return UTC representations and safe problem details plus UUID correlation. No SQL, constraints, ORM text or other-user identity in errors. Keep v1 compatible.

**SAR-018 / Idempotent API mutations:** Create/cancel/release require bounded Idempotency-Key. Same owner/token/action/key and canonical request replays stable status/body/correlation/safe Location; changed request conflicts. Matching expired record fails explicitly until operator cleanup. No duplicate reservation/audit.

**SAR-019 / Advisory private availability:** Shared availability clips, merges and complements blocking reservations and active blackout ranges under current policy/window. It is advisory, not a hold. Others expose only unavailable time, not identity/email/purpose/reason/UUID.

**SAR-020 / Blackout integrity:** Active maintenance blackouts block overlapping new bookings authoritatively; deactivation preserves history. Confirmation of affected reservations is explicit; blackout creation does not automatically cancel/release them. Validate half-open bounds and audit atomically.

**SAR-021 / Bounded audit evidence:** Audit is append-only at application/ORM/admin boundary, not tamper-proof against DB operators. Reject credential-like metadata recursively. Staff browsing/export is filtered, bounded, CSV-safe and privacy-minimized; export is not a raw forensic dump.

**SAR-022 / Reproducible monolith:** Preserve Python3.13, Django5.2, DRF3.17, PostgreSQL17, uv.lock, Gunicorn, WhiteNoise, local Swagger sidecar and server-rendered views. Add no production dependency or alternate stack without ordered justification/accepted decision.

**SAR-023 / Production fail closed:** Production requires nonplaceholder distinct secrets/pepper, DB, hosts and validated security settings. Secure cookies/private docs default; HSTS explicit opt-in. Local/test values do not authorize real deployment.

**SAR-024 / Topology and exposure:** Target is HTTPS proxy to non-root app to private PostgreSQL. Dev/rehearsal bindings stay loopback. Preserve UID:GID 10001:10001 and local static/bootstrap assets. No production DNS/TLS/host changes or public exposure under a development order.

**SAR-025 / Health and diagnostics:** Liveness has no DB dependency; readiness safely checks DB/migrations. operational_check covers DB/migrations/static/bootstrap/cleanup registration. pilot_readiness_check remains aggregate-only/read-only and not a release certificate.

**SAR-026 / Safe logs:** Production structured logs contain safe method/path/status/duration/correlation data, never credential headers, cookies, passwords, bodies, purposes, private locators or cancellation reasons. Error logging must not leak via inner exception locals.

**SAR-027 / Recovery tooling:** Backup/restore wrap PostgreSQL-native tools and default to validation/dry-run; apply needs explicit authorized isolated target. Idempotency purge defaults dry-run and deletes only expired records with apply. No installed scheduler or proven restore drill is implied by wrappers.

**SAR-028 / Synthetic migration boundary:** Legacy import accepts only its strict synthetic contract and local paths, rejects URL schemes/private fields/unknown statuses/duplicate IDs/bad times. No scraping, real export processing, credential reuse, user autocreation or inferred physical mapping.

**SAR-029 / Migration plan is not authority:** Dry-run creates no reservation/audit mutation. Explicit apply revalidates current mapped user/asset/policy/blackout/reservation/import-record state transactionally. Source+legacy ID idempotency, changed-input detection, final-result reports, safe audit and full rollback remain required.

**SAR-030 / Historical import exception:** Past completed synthetic records may use only the documented migration exception; future confirmed records obey current policies/exclusivity/blackouts. Cancelled/no-show handling must follow ADR0013 rather than invent blocking history.

**SAR-031 / Resource ownership in rehearsal:** Rehearsal may use only owned disposable files/containers/volumes/ports with no unsafe adoption/deletion of existing env/secrets/resources. Preserve one selected loopback app port and explicit failure cleanup.

**SAR-032 / Evidence before readiness:** Full/focused/browser/concurrency/operational results name actual revision and commands; CI quality,test,security,container at exact head are required. Prior 419-test report is historical, not proof for new code. Mocked boundaries and row counts alone are limited evidence.

**SAR-033 / Preserve existing project:** Workflow conversion preserves application bytes, data migrations, Git history, legacy PR/issues and accepted product exclusions. Do not regenerate the app, reopen merged PR27, fabricate old OAP reports or reset numbering/history.

**SAR-034 / Codex-only role separation:** Bootstrap, coding, strategic and ICA have distinct scopes. Operational root is tiny router; both development roles use separately configured Codex homes. No operational CLAUDE.md or Claude launcher; preserved methodology snapshots remain historical.

**SAR-035 / Private infrastructure boundary:** Never access real lab machines/Neumann, private exports, production DBs, long-lived credentials, DNS/TLS or deployment targets to test this conversion. Development model calls and Git publication require separately configured authority; product runtime uses no LLM.

**SAR-036 / Deferred product scope stays visible:** OIDC/password reset/notifications, projects/memberships/resource restrictions, token/management admin APIs, automatic physical allocation, monitoring stack, scheduler, real migration/cutover and gateway remain deferred. No assistant suggestion or draft silently authorizes them.

**SAR-037 / Canonical governance and projection:** Maintain canonical PLAN/ARCHITECTURE and preserved prior sources; compact coding projections are coverage-mapped and hash-bound, not independent law. Preserve security/reporting constraints while changing process authority deliberately.

**SAR-038 / Human target and ICA:** Strategic development merge never means release, deployment, physical-resource entitlement beyond product rules or human milestone acceptance. ICA derives from full architecture and exact merged revision with independent context and applicable DHA gates.


## Component routing

accounts=user/token; assets=hierarchy/import/staff API; reservations=policy/reservation/blackout
models and services; audit=append/validators; web=member forms/templates/shared availability;
management_ui=separate staff views; api=bearer adapters/idempotency/problem/ops commands;
legacy_import=strict synthetic parser/mapper/planner/apply; config=settings/health/logging.
Code roots are src/slaif_reservation/. Never duplicate policy in views or grant access by UI hiding.

## Current API boundaries

Explicit bearer: /api/v1/me/; /api/v1/assets/{id}/availability/ with availability:read;
/api/v1/reservations/ GET/read or POST/create; /{id}/ GET/read; /{id}/cancel/ POST/cancel;
/{id}/release/ POST/release. Reservation scopes are reservations:<action>. Every mutation needs
Idempotency-Key; own/guessed/other-user 404 is non-disclosing. Existing /api/v1/assets/ list/detail
remain staff-session-only. No token-lifecycle/management/admin REST endpoints. /api/schema/ and
/api/docs/ share private configuration; production never becomes public by convenience.

## Verification cautions

Source existence is not a pass. Baseline command executes count queries before DB-readiness guard;
rehearsal/tests use deployment paths and resource cleanup; full isolated restore proof not established.
Treat these as bounded investigation candidates, not bootstrap feature authorization. Preserve
ordinary no-past vs documented synthetic historical migration exception; API replay vs legacy source
idempotency are separate contracts. Root full architecture records rationale, proof gaps and deferrals.
