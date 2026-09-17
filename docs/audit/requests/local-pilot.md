# ICA request — M-LOCAL-PILOT-EVIDENCE — materialized at merged main 21f6204

Status: REQUEST (not an audit result). Materialized 2026-09-17 at merged main
21f6204d5f03c304991d4cd5c45a74aecdcb686a (human target fixed 2026-09-17;
objective 025 rounds a+b+c merged at this revision). Supersedes and replaces
the stale pre-target draft docs/audit/requests/local-pilot.DRAFT.md (deleted
in the same round; the draft is a pre-target proposal, not an immutable
historical snapshot). Structural validation via
`python3 oap/bin/check_ica.py --repo . --file docs/audit/requests/local-pilot.md
--kind request`; structural validation is structural-only (final section) and
never proves independence, correctness, or closure.

Milestone: M-LOCAL-PILOT-EVIDENCE — first controlled internal-alpha Docker
deployment target, through the documented Docker/Compose path. Per
docs/audit/ICA-PROTOCOL.md, M-LOCAL-PILOT-EVIDENCE includes all applicable
product boundaries: the full live ARCHITECTURE.md SAR index, SAR-001 through
SAR-038, with approved deferrals recorded out-of-target below.

Human scope/provenance: attributable in-session human instruction, 2026-09-17
(deployment qualification and closure task), from the in-session human
principal. Objective, quoted: "We now want to determine whether SLAIF Asset
Reservation is genuinely ready for its first controlled internal-alpha
deployment. The service MUST be deployable through the documented
Docker/Compose path." Exclusions, verbatim: "Do not interpret this instruction
as authorization to perform a real deployment, create/rotate real secrets,
configure real DNS/TLS, expose a host, touch production/private data, or cross
any other D2 boundary." Human milestone acceptance and release/deployment
authority remain separate from ICA.

Repository: ulfe-lmi/slaif-asset-reservation

Merged product revision: 21f6204d5f03c304991d4cd5c45a74aecdcb686a

Canonical PLAN/ARCHITECTURE revisions and hashes: PLAN.md and ARCHITECTURE.md
as of the merged product revision above (merge of PR #50 plus quiesce, main
local and remote verified equal at materialization).
- ARCHITECTURE.md SHA-256: 182d9cf924931e846bc7965a079482b6753de762af807196ca0b87f8dffdf863
- PLAN.md SHA-256: d03eb29713cfbdb7e227413618396e6bb2a7a08749225979c3055dacfd461d06
Both digests were re-verified live by the coding round that materialized this
request (2026-09-17; sha256sum on the clean main worktree at the merged
revision) and are recorded in oap/reports/026-a-ica-request-local-pilot.md.

Requirement matrix: all 38 SARs of the live ARCHITECTURE.md SAR index (A-14,
SAR-001 through SAR-038), one row each, materialized from the live index at
the merged revision (not from memory). The "Enforcing source" column is the
row's Inspect line and the "Evidence index" column is the row's Evidence line,
transcribed verbatim — an evidence starting point and an index (test
paths/commands), not a claim of result. Every row carries the initial
classification UNPROVEN; the auditor substantiates or reclassifies each row.
Enforcing-source paths are relative to src/slaif_reservation/ unless the index
line itself places them at repository root or elsewhere (as transcribed).
Every live index row carries both an Inspect line and an Evidence line; no row
required a "missing field" recording.

| SAR | Title | Initial classification | Enforcing source (Inspect, verbatim) | Evidence index (Evidence, verbatim) | Named negative path (concrete falsifying check) |
|---|---|---|---|---|---|
| SAR-001 | One reservation authority | UNPROVEN | `src/slaif_reservation/reservations/services.py` | Web/API/management create-cancel-release parity; no adapter-only enforcement. | A create/cancel/release path (adapter-only or parallel booking logic) that bypasses service-layer policy/exclusivity enforcement yet succeeds. |
| SAR-002 | Entitlement is not execution | UNPROVEN | `config/urls.py; api/urls.py; application imports` | Inspect actual routes/imports; absence of execution side effects. | Any route or import whose activation runs jobs, SSH, inference, containers, GPU allocation enforcement or power control on lab machines. |
| SAR-003 | Stable resource identity | UNPROVEN | `assets/models.py; assets/bootstrap.py` | Idempotent import; neumanngpu4 mapping; no ordinal inference. | Re-import changing an existing asset UUID/slug, or any CUDA index/GPU UUID/hostname/readiness value inferred from a legacy suffix. |
| SAR-004 | Asset verification | UNPROVEN | `assets/bootstrap.py; assets/selectors.py` | Safe import conflict/dry-run/verification-field preservation tests. | Bootstrap import overwriting verification flags, erasing an explicit unknown locator, or making the excluded chatgptpro entry reservable. |
| SAR-005 | UTC and DST | UNPROVEN | `reservations/time_utils.py; accounts/validators.py; web/forms.py` | Spring gap, autumn fold, malformed/overlong/NUL zone, UTC arithmetic and visible zone. | A naive API instant accepted, or a spring-gap/autumn-fold time silently resolved to a guessed instant without an explicit supported occurrence. |
| SAR-006 | Half-open effective-end history | UNPROVEN | `reservations/models.py; migrations/0001_initial.py` | Adjacent intervals accepted; released prefix preserved; cancelled free. | A mutation erasing the historical consumed interval (end_at/effective_end_at drift after release) or a cancelled row still blocking overlap. |
| SAR-007 | PostgreSQL exclusivity | UNPROVEN | `reservations/migrations/; reservations/services.py` | Real concurrent transactions, named constraint inspection, unrelated error test. | Two real concurrent transactions both committing overlapping same-asset ranges (exclusion not applied), or an unrelated integrity failure translated to reservation_conflict. |
| SAR-008 | Policies and counters | UNPROVEN | `reservations/services.py; models.py` | Boundary and counter races; missing/ambiguous and inactive-policy tests. | A missing/ambiguous/inactive policy allowing a booking (fail-open), or a principal counter raced past its limit by concurrent bookings. |
| SAR-009 | Atomic audited lifecycle | UNPROVEN | `reservations/services.py; accounts/services.py; legacy_import/importer.py` | Fault injection, rollback of every affected row and audit count, deadlock/race tests. | Fault injection leaving the domain row persisted while the audit row rolls back (or vice versa), or inconsistent lock ordering deadlocking web/API/management/import paths. |
| SAR-010 | Reducing entitlement remains possible | UNPROVEN | `reservations/services.py; web/views.py; api/reservation_views.py` | Release after deactivation; cancelled/released retry and cutoff tests. | Release of an active reservation rejected after asset/policy deactivation, or cancellation violating the accepted cutoff/ownership rules. |
| SAR-011 | Human session boundary | UNPROVEN | `web/auth.py; web/views.py; accounts/models.py` | Anonymous/inactive/service-account/staff/member matrix; CSRF and method tests. | An inactive or service-account session entering member routes, or a CSRF-less POST mutation (or mutating GET) succeeding. |
| SAR-012 | Member ownership | UNPROVEN | `web/selectors.py; api/reservation_views.py` | Cross-user detail and mutation tests through real adapters. | An other-owner or guessed reservation ID returning a disclosing status (200 or error revealing existence) instead of a non-disclosing 404. |
| SAR-013 | Management authority | UNPROVEN | `management_ui/auth.py; views.py; reservations/admin.py` | Role matrix plus CSRF/GET on every mutation; admin bypass tests. | A non-staff or service-account session performing a /manage/ cross-user mutation, or a management mutation landing without its audit event. |
| SAR-014 | Token secrecy and lifecycle | UNPROVEN | `accounts/tokens.py; models.py; services.py; api/authentication.py` | Secret/pepper/expiry/revocation/owner/scope matrices; failed auth no last-use mutation. | A revoked or expired token authenticating, a token/secret persisted in plaintext, a scope beyond the allowlist honored, or last-use mutated by a failed auth. |
| SAR-015 | One-time secret handling | UNPROVEN | `web/token templates/static; accounts/tokens.py; config/logging.py` | History Back; inner exception reports; recursive audit rejection; output canaries. | The one-time token secret reappearing in History Back, URL, session, message, log, audit, report artifact or trace capture (including redacted repr/exception frames). |
| SAR-016 | Scoped API adapters | UNPROVEN | `api/urls.py; permissions.py; assets/api.py` | Authentication/scope/ownership matrix, missing surfaces and schema. | A valid token alone reaching staff-session-only asset list/detail or any admin surface, or an action beyond the token's canonical scopes succeeding. |
| SAR-017 | Strict API contract | UNPROVEN | `api/serializers.py; problem.py; reservation_views.py` | Unknown fields/filter ordering/naive time/malformed JSON/endpoint-specific 404s. | An error body leaking SQL, constraint/ORM text or other-user identity, or unknown fields/naive instants accepted silently instead of bounded problem details. |
| SAR-018 | Idempotent API mutations | UNPROVEN | `api/idempotency.py; api/models.py; api/migrations/` | Real concurrent identical/different requests; expiry; safe header replay. | Concurrent identical-key replays producing duplicate reservation/audit rows, a changed-request replay treated as a replay instead of a conflict, or a matching expired record auto-resolving. |
| SAR-019 | Advisory private availability | UNPROVEN | `web/availability.py; api/reservation_views.py` | Cancelled/released/confirmed clipping, adjacency, blackout merge and privacy. | Another user's identity/email/purpose/reason/UUID exposed in shared availability, or a cancelled/released interval still reported as unavailable beyond its valid bounds. |
| SAR-020 | Blackout integrity | UNPROVEN | `reservations/models.py; services.py; management_ui/` | Create-vs-blackout race and adjacent boundary; confirmation; rollback. | A new booking overlapping an active blackout succeeding, blackout creation auto-cancelling/releasing affected reservations, or a blackout mutation missing its audit/rollback coupling. |
| SAR-021 | Bounded audit evidence | UNPROVEN | `audit/models.py; validators.py; management_ui/selectors.py; views.py` | Bulk/reconstructed mutation; secret-key/value rejection; export filtering/escaping. | A bulk-update/delete/queryset or admin path silently rewriting/removing audit rows, credential-like metadata accepted into audit metadata, or an unfiltered raw-forensic export. |
| SAR-022 | Reproducible monolith | UNPROVEN | `pyproject.toml; uv.lock; Dockerfile` | Locked install, lint/type/build/schema tests; no opportunistic upgrades. | A drifted lockfile or pyproject (new production dependency, version bump) without ordered justification/accepted decision. |
| SAR-023 | Production fail closed | UNPROVEN | `config/env.py; config/settings/production.py; accounts/tokens.py` | Subprocess negative settings matrix, ASGI/WSGI fail closed. | Production settings booting with placeholder/missing distinct secrets/pepper, DB or hosts, or local/test values authorizing a real deployment (fail-open). |
| SAR-024 | Topology and exposure | UNPROVEN | `compose*.yaml; Dockerfile; deploy/` | Rendered config plus actual sockets/image paths; explicit exposure gate. | A dev/rehearsal binding or database port published beyond loopback, an image running as root (UID:GID not 10001:10001), or missing local static/bootstrap assets. |
| SAR-025 | Health and diagnostics | UNPROVEN | `config/views.py; operational.py; api/management/commands/` | Real CLI disconnected/unmigrated/failure paths and no-write evidence. | Liveness depending on the database, readiness crashing instead of failing safely, or pilot_readiness_check performing writes or being treated as a release certificate. |
| SAR-026 | Safe logs | UNPROVEN | `config/logging.py; middleware.py; token exception protections` | Hostile sentinels through real log entry points; no raw report leakage. | A hostile sentinel (credential header, cookie, password, purpose, private locator, cancellation reason) appearing in structured logs directly or via inner exception locals. |
| SAR-027 | Recovery tooling | UNPROVEN | `api/management/commands/backup_database.py; restore_database.py; purge_expired_idempotency_records.py` | Refusal tests plus isolated real dump/restore round trip before recovery claim. | An apply without an explicit authorized isolated target, a restore into a nonempty target proceeding, or the idempotency purge deleting non-expired records. |
| SAR-028 | Synthetic migration boundary | UNPROVEN | `legacy_import/parser.py; mapping.py; management/commands/` | URL/path/schema/DST/privacy negatives; unmapped user/asset classifications. | The parser accepting URL schemes, private fields, unknown statuses or duplicate IDs, or autocreating users / inferring physical mappings from legacy data. |
| SAR-029 | Migration plan is not authority | UNPROVEN | `legacy_import/planner.py; importer.py; models.py` | Stale plan mutations, duplicate/changed records, apply report, audit rollback. | A dry-run creating reservation/audit rows, or an apply proceeding on a stale plan without revalidating current mapped state, or missing rollback on failure. |
| SAR-030 | Historical import exception | UNPROVEN | `legacy_import/importer.py; planner.py` | Past vs future vs skipped status tests; original interval retained. | A future confirmed synthetic record bypassing current policies/exclusivity/blackouts, or cancelled/no-show records inventing blocking history beyond ADR0013. |
| SAR-031 | Resource ownership in rehearsal | UNPROVEN | `deploy/rehearse_internal_alpha_deployment.sh; tests/test_operational_hardening.py` | Existing files/symlinks/project collision/partial startup; actual Compose merge. | The rehearsal adopting or deleting pre-existing env/containers/volumes, binding an existing or non-loopback port, or leaving residue after a failed startup. |
| SAR-032 | Evidence before readiness | UNPROVEN | `tests/; .github/workflows/ci.yml` | Real PostgreSQL, real entry-point smoke, negative tests, accurate skipped/blocked statuses. | A readiness claim resting on mocked boundaries, stale counts (e.g. the historical 419-test report) or unnamed revision/commands, with quality/test/security/container not green at the exact head. |
| SAR-033 | Preserve existing project | UNPROVEN | `entire tracked application and history` | Pre/post manifest diff allowlist; history ancestry; no product writes at bootstrap. | A pre/post manifest diff showing out-of-allowlist application-byte changes, regenerated scaffold, reset numbering/history or fabricated OAP reports. |
| SAR-034 | Codex-only role separation | UNPROVEN | `AGENTS.md; oap/; strategic home` | Instruction inheritance/role-conflict tests; no implicit role switch or fallback. | An operational CLAUDE.md/Claude launcher on the discovery path, or an implicit role switch by cd/source inspection instead of explicit launcher/human assignment. |
| SAR-035 | Private infrastructure boundary | UNPROVEN | `runtime constraints; private activation record` | Safe fixture-only bootstrap tests; network/resource allowlist; no secret copying. | Any development test or rehearsal touching a real lab machine/Neumann, private export, production DB, long-lived credential, DNS/TLS or deployment target. |
| SAR-036 | Deferred product scope stays visible | UNPROVEN | `PLAN.md deferred scope; source roadmap` | Architecture-to-scope matrix; no new surfaces during conversion. | A new OIDC/membership/gateway/monitoring/scheduler/management-REST surface appearing without an accepted decision, or a draft silently authorizing deferred scope. |
| SAR-037 | Canonical governance and projection | UNPROVEN | `oap/governance/; ARCHITECTURE-for-agents.md` | Semantic comparison and mechanical drift tests, measured read set. | A compact projection drifting from its canonical source (hash-bound coverage map broken) while being treated as independent law. |
| SAR-038 | Human target and ICA | UNPROVEN | `CRITICAL.md; oap/audit/; docs/READINESS.md` | Attribution/ICA freshness/target gate tests; no self-certification. | A strategic development merge being treated as release/deployment/milestone acceptance, or an ICA produced without a fresh independent context bound to the exact merged revision. |

## Approved deferrals (out-of-target, with authority — a deferral is not a pass)

1. Institutional OIDC / password reset / email workflow — authority: SAR-036
   (deferred product scope); roadmap deferred; INSTALL.md section 12 known
   alpha limitations (accounts are administrator-created; lost credentials
   require administrator-level recovery).
2. Projects / memberships / resource restrictions — authority: SAR-036;
   current model is broad authenticated-human authorization
   (docs/security-model.md section 6; INSTALL.md section 12), acceptable only
   under a constrained trusted pilot; the exposure boundary is an explicit
   human-gate input.
3. Execution gateway / automatic physical allocation — authority: SAR-036
   (a future deterministic gateway is a separate trust boundary per SAR-002);
   INSTALL.md section 12 (no execution enforcement).
4. Notification system — authority: SAR-036; INSTALL.md section 12 (no
   reservation emails or reminders).
5. Monitoring stack — authority: SAR-036 (Phase 4); INSTALL.md section 12
   (operator owns proxy/health/database/backup monitoring; no alert routing).
6. SmartScheduling production cutover — authority: SAR-030 scope (synthetic-
   fixture only, human-supervised; ADR0013); INSTALL.md section 12 (no
   automatic SmartScheduling cutover).
7. Database role separation + backup hardening — authority:
   docs/security-model.md section 6 ("Retention, database-role separation,
   and backup hardening remain operational work"); exposure-scope dependent —
   an input to the human gate.

Each deferral is explicitly out-of-target for M-LOCAL-PILOT-EVIDENCE, recorded
with its authority per ICA-PROTOCOL.md: it is not a pass, and none is silently
omitted.

Auditor/context identity: PENDING — fresh isolated audit context to be
spawned by strategy per ICA-PROTOCOL.md after this request is merged;
concrete identity (model, session origin, spawn time) recorded in the audit
report.

Independence evidence: required independence statement for the upcoming audit
context (unverified stays unverified):
- fresh isolated audit context — not the coding role, not the strategic
  role's second pass, not the bootstrap generator's self-review;
- no prior involvement in this audit or in the rounds under audit;
- inputs limited to the attributable human scope + this request + the exact
  merged revision + full ARCHITECTURE.md + repository bytes at that revision;
  do not start from a strategist's completion verdict;
- read-only mandate: report-artifact write only; no implementation, merge,
  CRITICAL disposition or release approval;
- honestly recorded: the audit context is expected to run on the same model
  family as development (fresh isolation, not an independent human);
- structural validation (oap/bin/check_ica.py) can check declarations but
  cannot prove independence, correctness or closure;
- the human retains final milestone acceptance; release/exposure/deployment
  remain separate decisions that an independent audit never substitutes.

Audit method (per docs/audit/ICA-PROTOCOL.md): input order is attributable
human target scope; full current ARCHITECTURE.md and its exact digest;
canonical requirement map; exact current merged product/governance revision;
then enforcing source, runtime entry points, tests and negative evidence.
Reports, CI and test counts are evidence indexes, not proof alone; mocked
authority/routing/persistence/deployment cannot prove those boundaries, and a
passed helper test cannot establish product/real-client/runtime acceptance.
Classify every applicable row IMPLEMENTED/PARTIAL/ABSENT/UNPROVEN (rows start
UNPROVEN until substantiated); each row names SAR ID, scope/deferral,
enforcing path/actual boundary, actual test/command/evidence, negative paths,
result, limits, audited revision, confidence and required remediation.
Findings carry provenance and the strongest reason not to fix now; after
remediation the architecture-to-current-main matrix reruns on the new exact
revision, not just closed finding IDs. Applicable unresolved DHA and D2 gates
remain explicit. Audit output is read-only by default.

Deliverable: the audit report lands at docs/audit/reports/
M-LOCAL-PILOT-EVIDENCE-<revision-prefix>.md (revision-prefix derived from the
exact merged revision above), written by the independent audit context — not
by this round.

No pre-filled result: this request contains no "Result: PASS" or equivalent;
all classifications and results are produced only by the audit context at the
exact merged revision.

Structural-only disclaimer: the structural validation of this request
(oap/bin/check_ica.py --kind request) checks field presence, the architecture
digest binding, the exact-revision line, the matrix vocabulary and the
auditor-pending structure. It is structural-only: it never proves
independence, correctness, or milestone closure, and it cannot establish
auditor independence or target readiness.
