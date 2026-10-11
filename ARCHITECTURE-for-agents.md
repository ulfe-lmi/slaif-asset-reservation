# ARCHITECTURE-for-agents — executor projection

Source: root ARCHITECTURE.md, 2026-10-04 edition (A-01..A-15, SAR-001..SAR-047); current
full-source SHA-256 `2d300121b37b62eeeb0676764d5d82739adf006a13e70d35ff62b84c59f7eb43`. Initial projection source SHA-256
`9e7c60e4ef6cee99d5baf20ee5ef6afcff38b10aa2eaa74a5a27084ff515a0c4` is historical provenance.
Scope: preservation and bounded development of existing SLAIF Asset Reservation, including the
selected M-INTERNET-UX-PILOT development target (A-15); real Internet exposure remains human D2.
SAR-039..SAR-047 rows carry their executor-relevant conditions directly; root A-15 is reference
only (not a mandatory read). Not independent architecture or approval. Normal coding reads this
file, not the full source. A genuine gap goes to strategy for a bounded correction/excerpt.

Baseline (historical, 2026-09): private ulfe-lmi/slaif-asset-reservation; WO0001–0013 complete;
main at the original projection observed 1fcc2c91d793556a91711365abef562604b62f84, and at this
projection observed 3abe17d026d7ebfe402426afd89e30cdc6924f61 (merged PR62).
Python3.13/Django5.2/DRF (source >=3.16,<3.18; lock authoritative, resolves 3.17.2)/PostgreSQL17;
preserve uv.lock. SAR-001..SAR-038 are stable; SAR-039..SAR-047 are new A-15 facets, initially
UNPROVEN until a fresh ICA at the exact merged revision.

**SAR-001 / One reservation authority:** Humans and authenticated software agents share scheduling records and authoritative domain operations. Do not introduce parallel booking logic.

**SAR-002 / Entitlement is not execution:** The reservation monolith does not run jobs, SSH, model inference, containers on lab machines, GPU allocation enforcement or power control. A future deterministic gateway is a separate trust boundary.

**SAR-003 / Stable resource identity:** UUIDs identify public records. Preserve hierarchical machine/child assets, existing slugs and provenance. Never infer CUDA index, GPU UUID, hostname or readiness from legacy suffixes.

**SAR-004 / Asset verification:** Generic bootstrap is not a physical probe. Preserve verification flags, unknown locators and inactive/nonreservable rejection. Site-specific exclusions remain historical.

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
**SAR-039 / Internet HTTPS/proxy boundary:** Public HTTPS endpoint only; Linux amd64; operator Caddy-or-equivalent; private-loopback non-root app; private DB; Gunicorn and DB never direct-Internet. Trust configured proxy peers only; reject attacker-supplied forwarding; normalize client IP/TLS headers. Explicit hosts/CSRF trusted origins; secure cookies; SSL redirect; debug off; safe errors/headers; safe logs; safe health; docs/schema disabled by default, staff-only when enabled; fail-closed secrets; private DB/network. HSTS deliberate opt-in; administration on the same hardened boundary; extra operator restrictions configurable (no LAN assumption).

**SAR-040 / Shared authentication and API abuse control:** Bound ordinary AND administration login and unauthenticated/invalid-bearer and authenticated API traffic with generous legitimate-agent throughput; configurable rates coordinated across processes (no multiplied per-process in-memory bounds); trusted-client identity, expiry/cleanup, safe failure; no permanent account lockout; stable machine-readable API errors, owner privacy, CSRF, idempotency preserved; multi-process negative proof; proxy read/idle/body bounds.

**SAR-041 / Default fresh-install policy:** Run initialize_default_policy after migrate: atomic audited active global `default` (asset NULL; duration1..2880min; START horizon7d; no hours; lead/cutoff0; purpose optional; upcoming50/overlap8 per principal across assets/tokens; overlap counts intersecting blocking records). Fresh booking works; repeats/races unique; any existing policy including inactive/specific prevents writes/reactivation/audit. Empty-upgrade init explicit; no migration/startup grant or manual fresh-policy step. Caps visible/documented; staff mutations unchanged; audit rollback tested.

**SAR-042 / Public product entry:** Anonymous landing with product identity, obvious Login and Administration actions, no private data; Administration enters the administration login; role navigation without redirect loops; login excludes invalid/inactive/service-account identities.

**SAR-043 / Browser product identity:** Never visible Django/framework branding on browser surfaces - SLAIF Asset Reservation or SLAIF-branded Administration across titles, headings, breadcrumbs, admin login/index/header, footer and errors; technical imports/docs/dependency names may say Django. Customize administration structurally, not by CSS hiding; protected/read-only admin models stay protected with service-backed mutation explained.

**SAR-044 / Explained accessible forms:** Audit raw filters AND every editable field/non-obvious choice across member/staff/admin; nearby actually-rendered meaningful help with accessible label/aria associations; explain units/effects, horizon START semantics, lead/cutoff, resolution, purpose, DST occurrence relevance, human token scopes, high-impact actions, protected admin editing; no clutter, no weakened validation; humanized duration display, unchanged storage units.

**SAR-045 / Safe operator appearance overrides:** Self-contained defaults plus read-only Docker/no-rebuild branding: primary/compact logo where relevant, favicon where practical, selected images and CSS loaded after defaults; no source fork/image rebuild; no server-side template execution, remote JS, arbitrary file exposure or unsafe mount adoption; safe fallback; documented MIME/path/symlink/size/failure boundaries; default and custom fixtures Playwright tested.

**SAR-046 / SLAIF design and visual qualification:** Design from the CURRENT references slaif.si/doc.slaif.si/edu.slaif.si/trainings; coherent accessible responsive CSS-token system; local official assets where organizationally appropriate, no runtime-critical hotlinking, no unrelated HTML/framework copy. Surface inventory and view/iterate rules are stated in the Selected target qualification clause below.

**SAR-047 / Threaded Gunicorn responsiveness:** Deliberate threaded pool consistently (image/local/production/rehearsal); preserve any foreign fix found, else reproduce the old sync failure before changing configuration; real-server test holds six idle/slow clients while /health/live and login stay bounded; old-sync negative control fails or equivalent sensitivity proof; owned cleanup on failure; documented worker/thread/keepalive rationale; buffering/time-limited HTTPS proxy retained. Predecessor 031-a/PR62 independently reproduced and remediated the baseline on main; evidence indexed, not future work or a new ICA.

**Selected target qualification (A-15):** Real unit/integration tests, PostgreSQL concurrency/rollback, browser HTTP auth/CSRF/privacy, real Gunicorn positive plus old-sync negative, disposable Internet HTTPS proxy, shared abuse controls, production-settings negatives, container/Compose/health, fresh+upgrade policy init, default/custom branding; standard five exact-head checks plus links/pip audit; exact source/revision/evidence statuses, no mocked-boundary pass. Browser surfaces: anonymous landing/login/admin login; member dashboard/assets list+detail/availability/reservation create+list+detail/profile/token list+create; staff management/policy list+detail+form/blackout list+detail+form/reservations/audit list+detail+export controls; admin index/user list+change/asset list+change/relevant protected models. Real Playwright capture/view/iterate at ~1440/1024/768/390 desktop/mobile, default/custom, with STRATEGIC visual review mandatory; durable semantic assertions on overflow, actions, navigation, focus, labels, associated help, tables, forms, no framework text, no anonymous leak; privacy-safe screenshots (no tokens/passwords/verifiers/CSRF/cookies/raw traces/private data); no brittle pixel CI unless stability proven. Final fresh isolated full-architecture ICA over all SAR-001..SAR-047 at the exact merged revision runs AFTER implementation; the old internal audit is historical; findings require bounded repair then a FULL architecture-to-current-main re-audit, not closed-findings-only review. Human acceptance/release/D2 real resources remain separate. Product-first docs reconcile behavior without ledger or public-production claims.

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
/api/docs/ share private configuration, are disabled by default and staff-only when enabled; production never becomes public by convenience.

## Verification cautions

Source existence is not a pass. At the 2026-09 baseline the command executed count queries
before the DB-readiness guard and no full isolated restore proof was established; both
observations are historical, and current evidence belongs to exact reports/tests at the exact
revision. Rehearsal/tests use deployment paths and resource cleanup. Treat these as bounded
investigation candidates, not bootstrap feature authorization. Preserve ordinary no-past vs
documented synthetic historical migration exception; API replay vs legacy source idempotency are
separate contracts. Root full architecture records rationale, proof gaps and deferrals.
