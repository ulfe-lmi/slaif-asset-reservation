# Independent Closure Audit Report — M-LOCAL-PILOT-EVIDENCE (post-remediation re-audit)

## Identity and scope

**Milestone:** M-LOCAL-PILOT-EVIDENCE — first controlled internal-alpha deployment target,
through the documented Docker/Compose path (per docs/audit/ICA-PROTOCOL.md: includes all
applicable product boundaries, full live ARCHITECTURE.md SAR index SAR-001..SAR-038, approved
deferrals recorded out-of-target).

**Nature of this audit:** POST-REMEDIATION PROTOCOL RE-AUDIT. Per ICA-PROTOCOL.md: "After
remediation, rerun the architecture-to-current-main matrix, not just closed finding IDs. Changed
relevant source/head requires freshness assessment." This report is that full matrix re-run at the
new exact head, not a verification of closed finding IDs alone.

**Human scope (verbatim, attributable in-session human instruction 2026-09-17; re-asserted
unchanged by the human on 2026-09-22 as this re-audit's target):**
> Objective: "We now want to determine whether SLAIF Asset Reservation is genuinely ready for its
> first controlled internal-alpha deployment. The service MUST be deployable through the
> documented Docker/Compose path."
> Exclusions: "Do not interpret this instruction as authorization to perform a real deployment,
> create/rotate real secrets, configure real DNS/TLS, expose a host, touch production/private
> data, or cross any other D2 boundary."

Human milestone acceptance and release/deployment authority remain separate from this audit.
This audit does not approve deployment, release, CRITICAL disposition, or any D2 action.

**Repository:** ulfe-lmi/slaif-asset-reservation (private)

**Exact audited product revision:** `a9c3133d3da36c34bd66ff4dba264d0b10bae9e0`
(028-a quiescent; quiescent state after merge of PR #56, which merged 028-a, whose implementation
corrected post-027 documentation drift. This is the current merged main as of the re-audit date
2026-09-22; the merge activity itself occurred 2026-09-17.)

**Prior ICA relationship (INPUT, NOT PROOF):** the prior ICA (2026-09-17) audited product revision
`21f6204d5f03c304991d4cd5c45a74aecdcb686a` (37 IMPLEMENTED / 1 PARTIAL / 0 ABSENT / 0 UNPROVEN;
report committed at `docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-21f6204.md`, present in this
worktree). Its findings F-001/F-002 were remediated by ordered work 027-a (PR #54, merge 55937a6,
quiesced cb2045c); work 028-a (PR #56, merge 9238e0c, quiesced a9c3133) corrected current-state
documentation lines. Prior report rows are inputs; every row below is re-substantiated at
a9c3133, with prior evidence cited as reusable only where product-runtime byte identity is
independently verified (see Freshness assessment).

**Main-identity note:** fresh detached worktree created exclusively for this audit at
/tmp/ica-a9c3133. At start and after all audit activity:
- `git rev-parse HEAD` = `a9c3133d3da36c34bd66ff4dba264d0b10bae9e0` (equals the audited revision exactly)
- `git status --porcelain` = empty (0 lines) at audit start and after all read-only audit
  activity; after the permitted report artifact was written (the last action), the only
  difference from the audited revision is that single untracked report file; no branch created,
  no commit, no push
All product/governance bytes audited are those of a9c3133.

**Canonical identities at audited revision (sha256sum, re-derived live in the worktree):**
- ARCHITECTURE.md: `8483a070026f382bb9b698e9346f3cb33f7dea44f8190b231431585986ebb17d`
  — MATCHES the 64-hex expected value supplied in the re-audit order.
- PLAN.md: `d03eb29713cfbdb7e227413618396e6bb2a7a08749225979c3055dacfd461d06`
  — MATCHES the 64-hex expected value supplied in the re-audit order (unchanged since 21f6204).
No input digest error was repeated: both supplied digests were full 64-hex and both match the
live re-derivation. (The prior audit's F-003 input-order defect is re-examined under Finding F-006.)

**Auditor identity (honest record):**
- auditor = Codex sub-agent context freshly spawned by the strategy role on 2026-09-22
  (actual start 2026-09-21T22:16:37Z UTC, the moment the detached worktree was created as the
  first audit action; host timezone Europe/Ljubljana).
- model = qwen3.8-27b — SAME model family as the development roles. This is fresh isolation,
  NOT an independent human auditor; recorded exactly as such per the mandate.
- session origin = spawned fresh with no forked/inherited context; no prior involvement in any
  OAP round (015-a..028-a or earlier), in the prior ICA, or in this repository.
- mandate = read-only with report-artifact write only (this file). No implementation, no merge,
  no CRITICAL disposition, no release approval, no D2 boundary crossed. No real deployment,
  real secrets, DNS/TLS, host exposure, or real lab/Neumann/production contact. Audit-local
  disposable resources were created and removed (see Evidence appendix C/F): local PG role
  `ica2` (CREATEDB, dropped), scratch databases `ica2audit`/`ica2ops`/`ica2scratch` (dropped),
  out-of-worktree venv at /tmp/ica-tools/venv (uv, committed lockfile), local docker image
  `slaif-ica-reaudit:a9c3133` (deleted after inspection), temporary rehearsal synthetic env
  files (removed by the script itself).

**Excluded systems/data:** real lab machines/Neumann, private SmartScheduling exports,
production databases, real secrets/identity providers, DNS/TLS, any deployment target.
**Evaluated runtime:** audit host (Ubuntu 24.04; PostgreSQL 16.15 server at 127.0.0.1:5432 with
17.11 client tools — the same host and versions as the prior audit; uv 0.12.5 with venv
Python 3.13.15; Docker 29.1.3; gh 2.45.0; Playwright chromium cached).
CI runtime: ubuntu-24.04 with postgres:17 service (CI test job).

**Audit date:** 2026-09-22 (local CEST) / 2026-09-21 (UTC) — re-audit at the human's
2026-09-22 re-asserted target.

## Freshness assessment

**Changed paths since the prior audited product revision (actual command output):**
```text
$ git diff --name-status 21f6204d5f03c304991d4cd5c45a74aecdcb686a..a9c3133d3da36c34bd66ff4dba264d0b10bae9e0
M  ARCHITECTURE-for-agents.md
M  ARCHITECTURE.md
M  README.md
A  docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-21f6204.md
D  docs/audit/requests/local-pilot.DRAFT.md
A  docs/audit/requests/local-pilot.md
M  docs/roadmap.md
A  oap/orders/026-a-ica-request-local-pilot.md
A  oap/orders/027-a-ica-finding-doc-drift-fix.md
A  oap/orders/028-a-doc-truth-post-027.md
A  oap/reports/026-a-ica-request-local-pilot.md
A  oap/reports/027-a-ica-finding-doc-drift-fix.md
A  oap/reports/028-a-doc-truth-post-027.md
```
Exactly 13 paths, matching the freshness input supplied to this audit. Top-level distribution:
1 ARCHITECTURE-for-agents.md, 1 ARCHITECTURE.md, 1 README.md, 4 docs/, 6 oap/.

**Classification: ZERO product-runtime paths changed.** Explicit verification:
```text
$ git diff --name-only 21f6204d5f03c304991d4cd5c45a74aecdcb686a..a9c3133d3da36c34bd66ff4dba264d0b10bae9e0 \
    -- src/ config/ tests/ manage.py Dockerfile compose.yaml compose.production.example.yaml \
       deploy/ pyproject.toml uv.lock data/ .github/ oap/bin oap/governance \
       oap/runtime.env.example oap/strategic-instructions oap/coding-instructions oaplib
(no output — exit 0)
```
All 13 changed files are architecture/governance/documentation/OAP:
- ARCHITECTURE.md — F-002 remediation ONLY (header line 5: preserved-snapshot path corrected from
  `sources/repository/docs-architecture.md` to `docs/bootstrap/1/previous/docs-architecture.md`;
  single-line diff, verified).
- ARCHITECTURE-for-agents.md — F-001 remediation ONLY (SAR-022 projection row: DRF3.16 → DRF3.17;
  single-line diff, verified).
- README.md, docs/roadmap.md — 028-a current-state corrections ONLY (the three stale
  current-state lines named in the 028-a order; historical/labeled docs untouched).
- docs/audit/requests/local-pilot.DRAFT.md (deleted) + local-pilot.md (added) — 026-a
  materialization of the ICA request (revision-bound artifact).
- docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-21f6204.md (added) — the prior ICA report itself.
- oap/orders|reports 026-a/027-a/028-a (6 files) — OAP round bytes.

**Remediation verification at a9c3133 (this audit's own commands, not the 027-a report's claims):**
- F-001: `grep` of ARCHITECTURE-for-agents.md SAR-022 row shows "DRF3.17"; uv.lock pins
  djangorestframework 3.17.2; canonical SAR-022 row says "DRF3.17". Scripted line-by-line
  comparison of ALL 38 projection SAR rows vs the canonical A-14 index (title + body, exact
  string match after whitespace normalization): **0 mismatches, 38/38 rows present in both**.
  The projection's "Existing baseline: … DRF3.16 …" line (line 7) was intentionally left by 027-a
  and is historically accurate, not drift: at baseline `1fcc2c91…` the lockfile pinned
  djangorestframework 3.16.1 (`>=3.16,<3.17` in pyproject); ordered round 016-a (commit 7bb4536)
  raised it to 3.17.2. The baseline line describes the pre-016-a baseline.
- F-002: ARCHITECTURE.md header line 5 now cites `docs/bootstrap/1/previous/docs-architecture.md`;
  `git ls-tree a9c3133… -- docs/bootstrap/1/previous/docs-architecture.md` = blob
  `246870a7771452ce3878c228b9ad7ffd8e71eda0` (preserved snapshot byte-identical);
  docs/architecture.md is the compatibility pointer (12 lines, verified) referencing the same
  path and blob.

**Ancestry and state:**
- `git merge-base --is-ancestor 21f6204… a9c3133…` = true.
- Commit chain 21f6204..a9c3133: 12 commits — 026-a (fad0489/d0ad4b8/41d811c/2df7018), ICA report
  commit a7b89d2, 027-a (15c28f3/2f1ca0a/148ef68/55937a6/cb2045c), 028-a (dd7801f/bc2428c/
  9238e0c/a9c3133). Every one is a governance/ICA/documentation byte; the only product-adjacent
  commits in the window (025-a/b/c at ccd11d1/d963cb4/23e9d42) predate 21f6204.
- OAP active pointer: `oap/active` is ABSENT at a9c3133 (quiesced by the 028-a quiescent commit),
  absent at 21f6204 and 2df7018, and present only at the merge commits (55937a6 → "027-a",
  9238e0c → "028-a"). This matches the repo's quiescent convention (pointer file removed, not
  emptied); an empty file would be corruption per the strategic constitution, and none exists.
  There is no active objective at the audited revision.

**Prior evidence reusability at a9c3133, per category (with what THIS audit re-verified):**

| Prior evidence category (at 21f6204) | Reusable at a9c3133? | Why | Re-verified by this audit |
|---|---|---|---|
| Full test suite (local 610/611 + CI 611 passed) | YES | Product bytes (src/, tests/, config/, settings) byte-identical: the path-restricted diff above is empty, so the prior suite exercised the same code under the same test definitions | NEW exact-head CI at a9c3133 (run 35193886320, all four jobs success; test job log line `611 passed in 129.10s` on postgres:17 — log retrieved live via gh API) + NEW local full-suite execution at a9c3133 (609 passed / 2 failed, both failures root-caused non-product, see F-005/F-006-class notes and appendix C) |
| Container/image build + inspection (local docker build, USER 10001:10001, static/bootstrap file checks; CI container job) | YES | Dockerfile + entire build context byte-identical (no changed path under any build-input directory) | NEW local `docker build` from the a9c3133 worktree (success; image User `10001:10001`; all 5 named static/bootstrap files present in image; image deleted after inspection) + CI container job green at the exact head a9c3133 |
| Production-shaped rehearsal (workflow_dispatch run 35182574499 at 21f6204, disposable CI runner, full script) | YES | deploy/rehearse_internal_alpha_deployment.sh, compose.production.example.yaml, compose.yaml, and all product bytes byte-identical; the rehearsal exercises only owned disposable loopback resources with synthetic values | No NEW full rehearsal was run at a9c3133 (none has occurred: the single historical rehearsal run remains 35182574499 at 21f6204, verified live). Instead this audit ran the script's documented `--config-only` mode at a9c3133 (rendered production compose with synthetic env, `config-only=ok`, worktree left pristine) and re-inspected the script's refusal/ownership logic in source. Full-rehearsal execution evidence at the current head therefore rests on byte identity + the 21f6204 runner execution + exact-head CI; that composition is stated explicitly, not concealed |
| Migration/operational checks (local CLI on disposable DB: migrate, operational_check, purge, bootstrap dry-run, makemigrations --check; suite coverage) | YES | Same command code and migration bytes | NEW local execution at a9c3133 on a fresh disposable DB: `migrate --noinput` (all OK), `import_bootstrap_assets` dry-run (excluded=1, conflicted=0, unchanged=0), `operational_check` (all six checks ok), `purge_expired_idempotency_records` (expired=0 deleted=0 remaining_expired=0), `pilot_readiness_check` (aggregate-only; strict gates correctly FAIL on an empty scratch DB — expected negative), `makemigrations --check --dry-run` (No changes detected), `manage.py check` (0 issues) + all migration/operational tests green in both local and exact-head CI suites |

**Freshness verdict:** product-runtime bytes are UNCHANGED since 21f6204.
Verifying command: `git diff --name-only 21f6204d5f03c304991d4cd5c45a74aecdcb686a..a9c3133d3da36c34bd66ff4dba264d0b10bae9e0 -- src/ config/ tests/ manage.py Dockerfile compose.yaml compose.production.example.yaml deploy/ pyproject.toml uv.lock data/ .github/ oap/bin oap/governance oap/runtime.env.example oap/strategic-instructions oap/coding-instructions oaplib`
Output: EMPTY (zero paths). The only changes in the window are the 13 governance/audit/OAP paths
listed above, each individually inspected.

## Requirement assessment

Method: for every SAR row I (a) read the enforcing source at a9c3133 (full ARCHITECTURE.md first,
per protocol input order: human target scope → full ARCHITECTURE.md + digest → canonical
requirement map (A-14) → exact revision → enforcing source/runtime/tests/negative evidence),
(b) located and read the named tests, (c) executed the full pytest suite locally at a9c3133
(609/611 passed; both failures root-caused as non-product — see Findings and appendix C/D),
(d) verified real CI execution at the exact head a9c3133 via the GitHub API (run logs retrieved,
not run metadata alone), and (e) re-ran targeted read-only operational checks (documented CLI
steps on a disposable DB, rehearsal --config-only, docker build + image inspection). Prior-audit
evidence is cited as reusable ONLY on the strength of the verified byte identity in the Freshness
assessment. All rows started UNPROVEN and are substantiated below or kept at a lower result.

Legend: audited revision = `a9c3133…` (= a9c3133d3da36c34bd66ff4dba264d0b10bae9e0) for every row.
"Local" = this audit's execution on the audit host (PG 16.15 server / 17.11 client tools; full
suite 609 passed / 2 env-boundary fails in 225.82s). "CI@a9c3133" = CI run 35193886320 (all four
jobs success; test job: 611 passed in 129.10s on postgres:17, CPython 3.13.14, pytest 9.1.1).
"CI@21f6204" = prior audit's exact-head run 35182282171 (611 passed in 128.39s) — reusable per
byte identity.

| SAR | Scope/deferral | Enforcing path / actual boundary | Actual test/command/evidence | Named negative path — verified | Result | Limits | Audited revision | Confidence | Required remediation |
|---|---|---|---|---|---|---|---|---|---|
| SAR-001 One reservation authority | in-target | src/slaif_reservation/reservations/services.py (create/cancel/release/policy/blackout services, each wrapped in transaction.atomic — verified at lines 239-597); adapters web/views.py, api/reservation_views.py, management_ui, legacy_import/importer.py route through these services; no parallel booking logic found in source | Local full suite incl. tests/test_reservations_services.py and tests/test_pilot_path.py::test_integrated_pilot_path_shared_state_across_surfaces (web+API+management on shared records; the single-test re-run at a9c3133 passed 9.27s after a midnight-boundary full-suite occurrence — F-005); CI@a9c3133 611 passed; prior local/CI evidence reusable (byte identity) | An adapter-only or parallel create/cancel/release bypassing service enforcement: not found — every adapter routes through the shared services; service tests assert policy/exclusivity enforcement; no second write path in source | IMPLEMENTED | Concurrency proof relies on PG17 CI + local PG16 threads (both green at both audited heads) | a9c3133… | high | none |
| SAR-002 Entitlement is not execution | in-target | config/urls.py, api/urls.py, wsgi/asgi imports; product src/ grep for subprocess/paramiko/ssh: none outside management commands (pg tool wrappers only — re-verified at a9c3133) | Local: source inspection of all urlconf/imports at a9c3133 (identical bytes to 21f6204); no execution side effects in any route | Any route/import activating jobs/SSH/inference/containers/GPU enforcement/power: none exist in product code; gateway explicitly out of product per A-01/A-02 | IMPLEMENTED | Absence verified by source inspection + greps, not by an executable negative (nothing to invoke) | a9c3133… | high | none |
| SAR-003 Stable resource identity | in-target | assets/models.py (UUID pk, legacy pair constraints), assets/bootstrap.py (idempotent apply, conflict fail-closed), data/bootstrap/assets.yaml (neumanngpu4→neumann-gpu-0 explicit, ordinal unverified) | Local: tests/test_bootstrap_assets.py (8 tests) green in both local and CI@a9c3133 suites; live `import_bootstrap_assets` dry-run at a9c3133: excluded=1, conflicted=0, unchanged=0; prior evidence (byte identity) | Re-import changing UUID/slug: second apply idempotent; conflicting mapping fails closed (test_import_conflict_fails_closed_and_leaves_database_unchanged); no CUDA/GPU-UUID/hostname/readiness inference (ordinal kept unverified) | IMPLEMENTED | — | a9c3133… | high | none |
| SAR-004 Asset verification | in-target | assets/bootstrap.py (verification_required preserved, dry-run default), assets/selectors.py (safe read selectors) | Local: tests/test_bootstrap_assets.py green at a9c3133 incl. test_import_does_not_invent_private_or_verified_hardware_identity, test_import_excludes_chatgptpro_and_preserves_disabled_askljof; live dry-run excluded=1 | Verification flags overwritten / unknown locator erased / chatgptpro made reservable: all negated by passing tests + assets.yaml content (verification_required retained; chatgptpro excluded with decision reason) | IMPLEMENTED | — | a9c3133… | high | none |
| SAR-005 UTC and DST | in-target | reservations/time_utils.py (require_aware_utc, explicit fold candidate handling — re-verified at a9c3133), accounts/validators.py, web/forms.py | Local: tests/test_reservations_time.py (6 tests) green at a9c3133 (spring gap, autumn fold, aware-local rejected, malformed/overlong/NUL zone); DST boundary service tests green | Naive instant accepted / silent DST guess: rejected — require_aware_utc raises InstantError; ambiguous wall time requires explicit fold; no candidate → LocalTimeError | IMPLEMENTED | — | a9c3133… | high | none |
| SAR-006 Half-open effective-end history | in-target | reservations/models.py (check constraints; exclusion over [start, effective_end)), migrations/0001_initial.py | Local: tests/test_reservations_models.py green at a9c3133 incl. adjacent-ranges, released-prefix-only, cancelled-does-not-block; service tests keep end_at immutable on cancel/release | Historical consumed interval erased (end/effective drift): service never mutates end_at; DB constraints enforce released: effective_end==released_at; cancelled row blocks nothing | IMPLEMENTED | — | a9c3133… | high | none |
| SAR-007 PostgreSQL exclusivity | in-target | reservations/migrations/0001_initial.py (BtreeGistExtension line 24; ExclusionConstraint name="reservation_no_overlap_per_asset" line 173-186 — re-verified at a9c3133), services.py named-constraint translation | CI@a9c3133: real PG17; test job log shows actual `ERROR: conflicting key value violates exclusion constraint "reservation_no_overlap_per_asset"` entries from concurrency tests (log retrieved live); tests/test_reservations_concurrency.py one-conflicts tests green locally (PG16) and in CI; prior CI@21f6204 evidence reusable (byte identity) | Two concurrent overlapping commits: negated (one-conflicts + repeated race tests); unrelated integrity failure: test_unrelated_integrity_error_is_reraised green (not reclassified as conflict) | IMPLEMENTED | Local concurrency ran on PG16; PG17 evidence is CI@a9c3133 (exact head) | a9c3133… | high | none |
| SAR-008 Policies and counters | in-target | services.py `_resolve_effective_policy` (exact→parent→global, fail closed), `_enforce_policy` (duration/lead/horizon/purpose/upcoming/concurrent) | Local: tests/test_reservations_services.py green at a9c3133: missing/ambiguous policy fail-closed, boundary-inclusive tests, upcoming/concurrent limits, start==now-is-active test, concurrent upcoming-limit test | Fail-open on missing/ambiguous/inactive policy: negated (POLICY_NOT_CONFIGURED/POLICY_AMBIGUOUS raised); counter raced past limit: negated (real concurrent test) | IMPLEMENTED | — | a9c3133… | high | none |
| SAR-009 Atomic audited lifecycle | in-target | services.py (transaction.atomic around domain+audit — verified at a9c3133), accounts/services.py (token issue/revoke atomic), legacy_import/importer.py (apply transaction) | Local: fault-injection rollback tests green at a9c3133 for create/cancel/release/policy/token/blackout/imported-reservation (test_audit_failure_rolls_back_*); lock-order wait test green | Audit row rolled back while domain row persisted (or vice versa): negated by fault-injection tests asserting both rows absent and audit count unchanged; inconsistent lock ordering: consistent principal→asset→policy order in all write paths; no deadlock in concurrency suite | IMPLEMENTED | Fault injection is monkeypatched service failure (realistic, not DB-crash level); cross-adapter deadlock not exhaustively exercised under all interleavings | a9c3133… | high | none |
| SAR-010 Reducing entitlement remains possible | in-target | services.py release_reservation (no policy resolution; no asset re-validation), cancel_reservation (cutoff via active policy) | Local: test_staff_can_release_another_users_reservation_after_asset_deactivation, test_release_succeeds_after_policy_deactivation, cancellation cutoff/ownership transition tests all green at a9c3133 | Release rejected after asset/policy deactivation: negated (both tests pass; release path never consults policy); cutoff/ownership violations: negated by transition tests | IMPLEMENTED | Boundary observation (carried from prior audit): cancellation computes its cutoff from the CURRENT active policy; with no active policy, cancel fails closed (POLICY_NOT_CONFIGURED). Outside the named negative, fail-safe, untested territory noted for completeness — not a defect | a9c3133… | high | none (optional doc note, as in prior audit) |
| SAR-011 Human session boundary | in-target | web/auth.py (is_active_human = authenticated+active+non-service-account — re-verified at a9c3133), web/views.py decorators | Local: tests/test_web_human_mvp.py matrix green at a9c3133 (active-human requirement, disallowed-session termination, POST-only logout, CSRF on mutations, GET non-mutation, service-account login denial) | Inactive/service-account session entering member routes: negated; CSRF-less POST or mutating GET: negated | IMPLEMENTED | — | a9c3133… | high | none |
| SAR-012 Member ownership | in-target | web/selectors.py + web/views.py `_owned_or_404`, api/reservation_views.py owner filtering | Local: cross-user detail/mutation tests green at a9c3133 (web staff-on-member-routes, API owner-scoped list/detail/cancel/release, endpoint-specific non-disclosing 404s) | Other-owner/guessed ID disclosing existence: negated — non-disclosing 404 with endpoint-specific codes through real web and API adapters | IMPLEMENTED | — | a9c3133… | high | none |
| SAR-013 Management authority | in-target | management_ui/auth.py (management_required: active + staff + non-service-account — re-verified at a9c3133), views.py/forms.py call audited services; reservations/admin.py read-only | Local: management role matrix, CSRF/GET-non-mutation, admin read-only, cross-user management + audit tests all green at a9c3133 | Non-staff/service-account performing /manage/ mutation: negated (role matrix, 403); management mutation without audit event: negated (audit written via services; rollback tests green) | IMPLEMENTED | — | a9c3133… | high | none |
| SAR-014 Token secrecy and lifecycle | in-target | accounts/tokens.py (hmac; TOKEN_SECRET_BYTES=32 → 256 random bits; pepper min 32 bytes — re-verified at a9c3133), api/authentication.py (revocation/expiry/owner checks, redaction, constant-time compare) | Local: tests/test_api_tokens.py green at a9c3133: failure matrix (malformed/revoked/expired/exact-boundary), compare_digest usage, scope normalization, lifetime bounds, failed-auth-no-last-use, verifier-not-plaintext | Revoked/expired token authenticating: negated (exact expiry boundary test); plaintext persistence: negated; scope beyond allowlist honored: negated; failed auth mutating last-use: negated | IMPLEMENTED | — | a9c3133… | high | none |
| SAR-015 One-time secret handling | in-target | web/views.py token_create (no-store/private/no-referrer one-time display), accounts/tokens.py sensitive handling, config/logging.py redaction | Local: one-time display + redaction tests green at a9c3133 (token web lifecycle, ExceptionReporter redaction, recursive audit rejection); browser suite (8 tests) green in CI@a9c3133 | Secret reappearing in History Back/URL/session/message/log/audit/report/trace: negated by no-store+no-referrer on the one-time response, prefix-only listing, redacted repr/exception frames, recursive audit metadata rejection | IMPLEMENTED | Real-browser History-Back behavior exercised within the Playwright suite (green at exact head), not as a separate isolated test | a9c3133… | medium-high | none |
| SAR-016 Scoped API adapters | in-target | api/urls.py, api/permissions.py (HasApiTokenScope per-action), assets/api.py (SessionAuthentication + staff only) | Local: bearer scope matrix, staff-asset-session-only, bearer-no-staff-access, no-token-lifecycle-routes tests all green at a9c3133 | Valid token alone reaching staff-session asset list/detail or admin surface: negated (asset API has no bearer authenticator; 403/401 tests); action beyond token scopes: negated (scope matrix) | IMPLEMENTED | — | a9c3133… | high | none |
| SAR-017 Strict API contract | in-target | api/serializers.py (bounded fields, aware instants), api/problem.py (safe problem details), reservation_views.py | Local: idempotency-key/aware-timestamp validation, unknown-filter rejection, endpoint-specific 404s, problem-detail assertions green at a9c3133 | Error leaking SQL/constraint/ORM text/other-user identity: negated (problem.py maps domain errors to safe codes; no ORM/SQL strings in serializers/views source); unknown fields/naive instants accepted: negated (400 + problem detail) | IMPLEMENTED | — | a9c3133… | high | none |
| SAR-018 Idempotent API mutations | in-target | api/idempotency.py (canonical_request_hash, replay/conflict/expired semantics — re-verified at a9c3133), api/models.py (unique owner/token/action/key, TTL) | Local: idempotent replay (no duplicate audit), conflict on same-key-different-request, expired-record explicit failure, different-token independence, REAL concurrent identical/different tests all green at a9c3133; CI log shows real unique-constraint behavior under concurrent conflict | Duplicate reservation/audit from concurrent identical-key replays: negated (one mutation, one audit; DB unique constraint final arbiter); changed request treated as replay: negated (idempotency_conflict); expired record auto-resolving: negated (idempotency_expired, no new write) | IMPLEMENTED | Safe replay header allowlist is Location-only (by design) | a9c3133… | high | none |
| SAR-019 Advisory private availability | in-target | web/availability.py (clip/merge/complement, lead/horizon, "Unavailable" labels, reservation_id None by default — re-verified at a9c3133), api availability view | Local: availability clipping/merging/privacy tests green at a9c3133 (busy/free exact rules, local day boundaries, blackout reasons/identity never emitted) | Other user's identity/email/purpose/reason/UUID exposed: negated (foreign intervals labeled "Unavailable", reservation_id None; blackout reason never emitted); cancelled/released reported beyond valid bounds: negated | IMPLEMENTED | Advisory nature (no hold) is by design, not a gap. The midnight-boundary full-suite occurrence (F-005) showed the product CORRECTLY rendering the clipped prefix for the window actually requested — a test-side expectation issue, not a product privacy/clipping defect | a9c3133… | high | none |
| SAR-020 Blackout integrity | in-target | services.py create_blackout (locked, explicit confirmation of affected reservations), `_raise_if_blackout_overlap` in create path, models.py blackout constraints | Local: blackout blocks web+API creation (half-open boundary), confirmation behavior, audit-failure rollback, REAL reservation-vs-blackout and deactivation-vs-booking race tests green at a9c3133 | New booking over active blackout succeeding: negated (locked-transaction check + repeated real-transaction races); auto-cancel/release on blackout creation: negated (overlapping reservations reported, explicit confirm flag, no lifecycle writes); missing audit/rollback coupling: negated | IMPLEMENTED | Final arbiter for blackout-vs-reservation ordering is the locked-transaction application check (A-06 explicitly notes PG exclusion does not cover blackout ordering); races covered by repeated real-transaction tests | a9c3133… | high | none |
| SAR-021 Bounded audit evidence | in-target | audit/models.py (append-only manager/queryset), audit/validators.py (FORBIDDEN_METADATA_KEYS recursive, 4096-byte cap — re-verified at a9c3133), management_ui export (filtered, CSV-safe) | Local: append-only/admin read-only, ordinary overwrite/update/delete blocked, bulk-entry block, nested forbidden-key + oversized rejection, export filter/escaping tests all green at a9c3133 | Bulk/admin silently rewriting/removing audit rows: negated; credential-like metadata accepted: negated (recursive key + plaintext-token rejection incl. nested); unfiltered raw-forensic export: negated (allowlisted filters, bounded windows, CSV escaping) | IMPLEMENTED | Application/ORM boundary only — not tamper-proof vs privileged DB operator (explicitly acknowledged in A-05/security-model; hardening is an approved deferral, out-of-target) | a9c3133… | high | none (deferral recorded out-of-target) |
| SAR-022 Reproducible monolith | in-target | pyproject.toml (Python >=3.13,<3.14; Django >=5.2,<5.3; DRF >=3.16,<3.18), uv.lock (djangorestframework 3.17.2 — re-verified at a9c3133), Dockerfile (python:3.13-slim, uv sync --locked, USER 10001:10001) | Local: full venv from the committed lockfile (Django 5.2.17, DRF 3.17.2) used for all runs; NEW `docker build` from the a9c3133 worktree succeeded; CI quality job (ruff/mypy/git diff --check) + container job success at exact head a9c3133; prior evidence reusable (byte identity) | Drifted lockfile/pyproject (new production dep or bump without decision): negated for the window — product bytes unchanged since 21f6204, where the only dependency change vs baseline was the ordered 016-a pip-audit remediation (7bb4536); CI `uv sync --locked` enforces lockfile integrity at the exact head | IMPLEMENTED | Prior F-001 (projection DRF label) is REMEDIATED at this head — the 38-row scripted comparison shows 0 mismatches; no residual drift found | a9c3133… | high | none |
| SAR-023 Production fail closed | in-target | config/env.py (env_required, UNSAFE_SECRET_KEYS, min-length checks — re-verified at a9c3133), settings/production.py (ImproperlyConfigured; DEBUG forced off; secure cookies; private docs; HSTS opt-in), accounts/tokens.py pepper validation | Local: tests/test_settings.py full negative matrix green at a9c3133 (placeholder/short/committed secrets, hosts/CSRF origins, ASGI fail-closed, HSTS bounds); CI security job (live subprocess import of production settings that MUST fail without env) success at exact head a9c3133 | Production booting with placeholder/missing secrets/pepper/DB/hosts: negated (settings raise at import; live subprocess negative at exact head); local/test values authorizing deployment: negated (UNSAFE sets reject committed local/test values) | IMPLEMENTED | — | a9c3133… | high | none |
| SAR-024 Topology and exposure | in-target | compose.yaml (dev: 127.0.0.1-only binds — re-verified at a9c3133), compose.production.example.yaml (app 127.0.0.1:${SLAIF_APP_HOST_PORT:-8000}:8000 only; db service has NO published ports; user 10001:10001; healthcheck — re-verified at a9c3133), Dockerfile (USER 10001:10001 — re-verified) | NEW local docker build at a9c3133: image Config.User = 10001:10001; all 5 named static/bootstrap files present in the built image (web/site.css, admin base.css, swagger-ui bundle, data/bootstrap/assets.yaml + assets.schema.json); NEW rehearsal --config-only at a9c3133 rendered the production compose with synthetic env (ok, clean); CI container job green at exact head; prior local build evidence reusable (byte identity) | Binding beyond loopback / db published / root image / missing static-bootstrap assets: all negated (compose source + live image inspection + rendered-config guard). No DNS/TLS/host changes made by any development order | IMPLEMENTED | Real reverse-proxy/TLS is operator-owned (D2 boundary; Caddyfile.example provided); live-socket exposure only observed at loopback in dev/rehearsal shapes | a9c3133… | high | none |
| SAR-025 Health and diagnostics | in-target | config/views.py (health_live no DB; health_ready safe-fail — re-verified at a9c3133), config/operational.py, management commands (operational_check, pilot_readiness_check, purge_*) | NEW local at a9c3133 on fresh disposable DB: operational_check → database/migrations/static/bootstrap/idempotency_cleanup/operational_check all ok; pilot_readiness_check → aggregate-only output, strict gates correctly FAIL on empty scratch DB (expected negative), no identifiers, no mutation; purge → expired=0 deleted=0; tests/test_health.py + pilot_readiness_check suite (14 tests incl. read-only proof, hard gates on DB/migration failure) green locally and in CI@a9c3133 | Liveness depending on DB: negated (test + source: no DB call in health_live); readiness crashing: negated (exception→safe path tested); pilot_readiness_check writing or being a release certificate: negated (read-only test asserts zero row changes; aggregate-only observed live) | IMPLEMENTED | — | a9c3133… | high | none |
| SAR-026 Safe logs | in-target | config/logging.py (JsonLogFormatter safe fields, recursive redaction, AUTHORIZATION_RE, FORBIDDEN_FIELD_NAMES — re-verified at a9c3133), config/middleware.py (method/path/status/duration/request_id only) | Local: formatter redaction, middleware safe-fields, production JSON config load, authentication log secret tests all green at a9c3133 | Hostile sentinel (credential header/cookie/password/purpose/private locator/cancellation reason) in structured logs directly or via inner exception locals: negated (FORBIDDEN_FIELD_NAMES redaction incl. purpose/cancellation_reason; exception text scrubbed; middleware emits no headers/body) | IMPLEMENTED | Sentinel exercise is via formatter/middleware unit paths (real log entry points), not a full A/B of every view's log lines | a9c3133… | high | none |
| SAR-027 Recovery tooling | in-target | management commands backup_database.py, restore_database.py, restore_drill.py, purge_expired_idempotency_records.py, _postgres_tools.py | Local at a9c3133: refusal/dry-run/missing-URL/password-redaction tests (test_operational_hardening.py) green; CI@a9c3133: tests/test_restore_drill.py 9/9 green on postgres:17 (real dump/restore round-trip, log verified live); prior local PG17-blocked observation reproduced identically here (see F-006-class note: pg_restore 17.11 `SET transaction_timeout` rejected by PG16.15 server — manually reproduced at a9c3133 audit time, exact error captured) | Apply without explicit authorized isolated target: negated (dry-run default; --apply required; operator-named isolated target); purge deleting non-expired: negated (expired=0/deleted=0 semantics); drill not cleaning up: negated (own-target cleanup in tests) | IMPLEMENTED | Local re-execution of the PG17 round-trip is environment-blocked on this host (PG16.15 server; same limitation as prior F-004, re-confirmed with a fresh manual repro); the real round-trip evidence at the exact head is CI@a9c3133 on postgres:17. Drill is specified for PG17 (matches the compose-deployed image) | a9c3133… | medium-high | none (informational: prior F-004 persists as an environment note) |
| SAR-028 Synthetic migration boundary | in-target | legacy_import/parser.py (URL scheme, private-field, unknown-status, duplicate-ID, DST-time rejection), mapping.py (explicit maps only) | Local: tests/test_legacy_import.py parser/mapping suites green at a9c3133 (URL schemes refused, private fields, duplicate IDs, nonexistent/ambiguous local times, unmapped user/asset classifications) | Parser accepting URL schemes/private fields/unknown statuses/duplicate IDs: negated (failing-fixture tests); user autocreation or inferred physical mapping: negated (no user-creation code path; mapping requires explicit maps) | IMPLEMENTED | — | a9c3133… | high | none |
| SAR-029 Migration plan is not authority | in-target | legacy_import/planner.py (read-only plan), importer.py apply revalidation (locked revalidation of user/asset/policy/blackout/reservation/import-record) | Local: dry-run-writes-nothing, apply-revalidates (new blackout/new reservation conflict/asset state/user state/missing future policy/existing import record), changed-record-reported, audit-failure rollback, legacy-import concurrency tests all green at a9c3133 | Dry-run creating rows: negated (zero reservation/audit count assertions); apply on stale plan without revalidation: negated (each revalidation test injects post-plan state change and asserts classification/rollback); missing rollback: negated | IMPLEMENTED | — | a9c3133… | high | none |
| SAR-030 Historical import exception | in-target | legacy_import/importer.py + planner.py (past-completed migration exception; future records obey current policy/exclusivity/blackouts) | Local: status/asset/policy classification tests, future-import-uses-current-policy test, past/future/skipped apply handling green at a9c3133 | Future confirmed record bypassing current policies/exclusivity/blackouts: negated (future records go through _enforce_policy + blackout/overlap revalidation); cancelled/no-show inventing blocking history: negated (per ADR0013) | IMPLEMENTED | Real SmartScheduling cutover remains an approved deferral (synthetic fixtures only) — out-of-target, not a pass gap | a9c3133… | high | none |
| SAR-031 Resource ownership in rehearsal | in-target | deploy/rehearse_internal_alpha_deployment.sh (owned project prefix `slaif-alpha-rehearsal-` line 72; refuses pre-existing deploy/env.production + secrets lines 318-319; residue refusal line 235; root refusal line 309 — re-verified at a9c3133), tests/test_operational_hardening.py | NEW local at a9c3133: `--config-only` ran clean (synthetic env created+removed, `config-only=ok`, worktree pristine); hardening tests green locally and in CI@a9c3133; historical FULL rehearsal execution: CI run 35182574499 at 21f6204 (workflow_dispatch, disposable runner, success — verified live; the only rehearsal run ever recorded) | Adopting/deleting pre-existing env/containers/volumes: negated (refusal + label-scoped ownership, script unchanged); existing or non-loopback port binding: negated (precheck tests + 127.0.0.1-only compose shape); residue after failed startup: negated (trap cleanup + owned-residue handling) | IMPLEMENTED | No NEW full rehearsal was executed at a9c3133 by this audit; full-rehearsal evidence at the current head rests on (a) byte-identical script/app/compose vs the 21f6204 runner execution, (b) this audit's fresh --config-only render at the exact head, (c) exact-head CI. Stated explicitly as the evidence composition | a9c3133… | high | none |
| SAR-032 Evidence before readiness | in-target | tests/ (611 tests at this revision), .github/workflows/ci.yml (quality/test/security/container with postgres:17), deployment-rehearsal.yml, oap.yml | CI@a9c3133 run 35193886320: quality/test/security/container ALL success (verified via gh API + test-job log: `611 passed in 129.10s` on real postgres:17, CPython 3.13.14, pytest 9.1.1, named command output, real exclusion-constraint violations logged); oap run 35193886316 success at exact head; deployment-rehearsal run 35182574499 success at 21f6204 (byte-identical product); Local: same suite re-executed at a9c3133 (609/611, both fails root-caused non-product) | Readiness claim resting on mocked boundaries/stale counts/unnamed revisions: negated — this audit re-derived from source at a9c3133; the historical 419-test figure is labeled historical in PLAN.md and not used as proof; all four required CI jobs green at the exact head | IMPLEMENTED | Historical 419 count superseded by current 611-test exact-head evidence. The one failed CI run in the window (35193878477 at merge commit 9238e0c) is the OAP-harness timing flake, verified as exactly one failed test on byte-identical harness, and is explicitly OUT of target per the human's 2026-09-22 instruction | a9c3133… | high | none |
| SAR-033 Preserve existing project | in-target | entire tracked application and Git history | Local at a9c3133: `git merge-base --is-ancestor 1fcc2c91…(baseline) a9c3133…` = true; product-path diff baseline..a9c3133 maps exclusively to ordered, PR-tracked rounds (WO0014 190f9b3, 015-a 12ef602, 016-a 7bb4536, 017-a 8f83dcb, 018-a b83d8a5, 019-a 71ad4d9, 020-a fd1a2a4, 021-a 9781ed6, 022-a f20e4d2, 024-a 14ccae1, 025-a ccd11d1, 025-b d963cb4, 025-c 23e9d42 — commit log verified); 21f6204..a9c3133 delta is exactly the 13 governance/audit/OAP paths (zero product paths); OAP orders/reports 015-a..028-a present and sequentially numbered with matching implementation heads | Out-of-allowlist application-byte changes by the conversion: negated (every product diff maps to an ordered round with PR ancestry; the re-audit window added ZERO product bytes); reset numbering/history: negated (linear PR-merge ancestry from baseline, verified); fabricated OAP reports: negated (round↔PR↔head consistency spot-checked across the window) | IMPLEMENTED | Full byte-level diff of the whole window verified at commit granularity (git log per path), not per file hunk | a9c3133… | high | none |
| SAR-034 Codex-only role separation | in-target | AGENTS.md (role router), oap/bin launchers → oap_launch.py, oap/strategic-instructions/ + oap/coding-instructions/ (separate homes/read sets) | Local at a9c3133: `find` → zero CLAUDE.md files; all "claude" occurrences in oap/ and AGENTS.md are negative statements ("No operational CLAUDE.md or Claude launcher"); oap harness (incl. role-conflict/inheritance tests ba10/11) green in oap CI run 35193886316 at exact head; prior evidence reusable (byte identity of oap/ harness) | Operational CLAUDE.md/Claude launcher on discovery path: negated; implicit role switch by cd/source inspection: negated (router requires explicit launcher/human assignment) | IMPLEMENTED | Private role-home state (STRATEGIC_HOME) is outside the repo by design; verified only the repo-side router/launchers | a9c3133… | high | none |
| SAR-035 Private infrastructure boundary | in-target | runtime constraints (oap/runtime.env.example: no keys/tokens stored; Codex-only clients), product code (no LLM/ssh/network egress), private activation record (out-of-repo by design) | Local at a9c3133: product src/ contains no LLM/ssh/paramiko imports (the two case-insensitive "llm" grep hits are the regex names `fullmatch` — false positives, verified); no deployment targets/hosts in code; runtime.env.example forbids credential storage; this audit itself performed no real-infrastructure contact (loopback-local only + GitHub API reads of own repo's runs) | Development test/rehearsal touching real lab machine/Neumann/private export/production DB/long-lived credential/DNS-TLS/deployment target: negated in-repo (no such endpoints or fixtures; rehearsal uses synthetic values + owned disposable resources); no secret copying (oaplib secret-line guard + policy) | IMPLEMENTED | "Private activation record" lives outside the repo (by design) — repo-side constraints verified only | a9c3133… | medium-high | none |
| SAR-036 Deferred product scope stays visible | in-target | PLAN.md P-04 (deferral list — re-read at a9c3133, digest-matched), docs/roadmap.md, INSTALL.md §12 (9 known alpha limitations), docs/security-model.md §6, ARCHITECTURE.md A-04/A-10 | Local at a9c3133: source inspection — no OIDC/membership/notifications/monitoring/scheduler/gateway/management-REST implementation present (urlconf/OpenAPI surface is exactly the A-08 interface map; no token-lifecycle/admin REST routes); the 7 approved deferrals remain recorded out-of-target with authority in docs/audit/requests/local-pilot.md (lines 96-124, verified) | New deferred-scope surface appearing without accepted decision: negated (no new surfaces since 21f6204 — zero product bytes changed; OpenAPI negative test green at exact head); draft silently authorizing deferred scope: negated (request records all 7 deferrals out-of-target with authority; 028-a roadmap correction describes completed work truthfully and does not authorize the next deployment — it explicitly states "a real deployment has not yet been evidenced") | IMPLEMENTED | The 7 approved deferrals are OUT-OF-TARGET with recorded authority — neither passes nor omissions (list in Outcome section) | a9c3133… | high | none |
| SAR-037 Canonical governance and projection | in-target | oap/governance/ (HUMAN-AUTHORITY.example.json), ARCHITECTURE-for-agents.md (executor projection), root ARCHITECTURE.md/PLAN.md canonical | THIS AUDIT: scripted line-by-line comparison of all 38 projection SAR rows vs the canonical A-14 index at a9c3133 (exact title+body string match): 0 mismatches, 38/38 rows in both; F-001's single drift (SAR-022 DRF label) is remediated in-tree (line-level diff verified); the "Existing baseline" DRF3.16 line is historically accurate for baseline 1fcc2c91 (lockfile 3.16.1 at that commit, verified via git show); projection header hash-binds to the INITIAL architecture (9e7c60e4…) and declares "Not independent architecture or approval"; preserved prior snapshot blob intact (246870a7…); F-002's header path is corrected in-tree and blob-verified | Projection drifting from canonical source while treated as independent law: NEGATIVE NOW SATISFIED — zero semantic drift across all 38 rows at this head; the prior PARTIAL (single version label) no longer exists. Canonical precedence + explicit non-law header + coverage mapping (38/38) verified | IMPLEMENTED | The projection header's hash binding is to the INITIAL canonical edition (by its stated design: "initial SHA-256"); current-edition sync is established by this audit's scripted 38-row comparison (0 mismatches), not by header hash. If strategy wants the header itself re-bound to the current canonical digest with a delta note, that is an optional future governance-doc round, not a defect at this head | a9c3133… | high | none (optional re-binding noted) |
| SAR-038 Human target and ICA | in-target | CRITICAL.md (register state at a9c3133), oap/audit references, docs/READINESS.md, OAP runtime template merge flag | THIS AUDIT: CRITICAL.md at a9c3133 contains zero CRIT entries ("No CRIT entries at initialization", no dispositions — grep count 0; register byte-identical in substance to 21f6204); this report is a fresh isolated context bound to the exact merged revision (identity section); oap/runtime.env.example ships OAP_DEVELOPMENT_MERGE_ENABLED=false (merge disabled absent attributable activation — re-verified); oap/active pointer correctly quiesced (absent) at the audited head; oap CI (harness incl. ba46/47/48 ICA-protocol tests) green at exact head (run 35193886316) | Strategic development merge treated as release/deployment/milestone acceptance: negated (no such claim in any 026-a/027-a/028-a round byte — 028-a's roadmap correction explicitly says "a real deployment has not yet been evidenced"; merge disabled by default; this audit makes no acceptance claim); ICA without fresh independent context bound to exact revision: negated (fresh context, a9c3133-bound, same-model-family limitation recorded honestly) | IMPLEMENTED | Auditor is same model family as development roles (fresh isolation, not an independent human) — recorded as a limitation, not a defect | a9c3133… | high | none |

**Classification counts (38 rows):** IMPLEMENTED = 38, PARTIAL = 0, ABSENT = 0, UNPROVEN = 0.

## Findings and contrary evidence

**F-005 — Local-midnight boundary sensitivity in one integrated browser test (INFORMATIONAL,
test-harness, NOT an in-target product defect; OUT of target for remediation in this audit)**
- Provenance: this audit's local full-suite run at a9c3133 (225.82s) produced exactly one
  non-environmental failure:
  `tests/test_pilot_path.py::test_integrated_pilot_path_shared_state_across_surfaces[chromium]` —
  `AssertionError: assert '2026-09-21 23:56' in 'Your reservation 2026-09-22 00:00 -
  2026-09-22 00:26\n…'`. The suite's `now` was captured at 21:56:55 UTC = 23:56:55 local CEST,
  i.e., ~4 minutes before the local date rollover.
- Root cause (source-verified): the test computes expected display labels from its captured
  `now`, while the availability page's default date is resolved AT RENDER TIME
  (src/slaif_reservation/web/views.py `_availability_from_request`:
  `timezone.now().astimezone(ZoneInfo(tz)).date()` when no `date` param is given). When the local
  date rolled over between `now` capture and page render, the expected 09-21 labels fall outside
  the rendered 09-22 window. The rendered output itself was CORRECT product behavior: the
  "2026-09-22 00:00 - 00:26" interval is the consumed prefix clipped to the window actually
  requested (minute-truncated, seconds dropped) — clipping/privacy behavior per A-09 is intact.
- Evidence this is a test-boundary flake, not a product defect: (1) isolated re-run of the exact
  test at a9c3133 at 00:31 local PASSES in 9.27s; (2) CI@21f6204 and CI@a9c3133 (both run at
  ~09:18 local) are green with the same bytes; (3) prior audit's local run (07:19 local) was
  green with the same bytes.
- Impact: none on product behavior; a latent flake window of a few minutes around local midnight
  for this one test on local (non-CI) runs.
- Disposition: OUT of target for this audit (the human's scope targets product deployability;
  a test-robustness fix would be a bounded test-only round if strategy orders one). Recorded here
  for honesty because it occurred in THIS audit's local evidence and would otherwise look like
  an unexplained red. No in-target blocker follows from it.

**F-006 — Prior ICA report's recorded "live-computed" ARCHITECTURE.md digest was a corrupted
(record-hygiene) string (INFORMATIONAL, prior record; no product impact)**
- Provenance: the prior report (M-LOCAL-PILOT-EVIDENCE-21f6204.md) records, in its Identity
  section and Evidence appendix A, a 51-hex-char value
  `182d9cf924931e846bc7965a762af807196ca0b87f8dffdf863` as the "live-computed digest" of
  ARCHITECTURE.md at 21f6204. A sha256sum output is always 64 hex chars; this value is not one.
- This audit's re-derivation from the git object:
  `git show 21f6204d5f03c304991d4cd5c45a74aecdcb686a:ARCHITECTURE.md | sha256sum`
  → `182d9cf924931e846bc7965a079482b6753de762af807196ca0b87f8dffdf863` (64 hex). The true digest
  is exactly the 64-hex value already recorded in the materialized request
  (docs/audit/requests/local-pilot.md line 37). The prior report's string equals the true digest
  with 13 middle hex chars (`079482b6753de`) omitted.
- Consequence: F-003's substantive conclusion (the transient input-order digest was malformed and
  the audit proceeded on computed digests) stands and was the correct handling; but the prior
  report's own digest RECORD is a transcription corruption, and its "worktree == revision blob"
  check (which compared the worktree against the revision blob, both then recorded with the same
  corrupted string) is not re-establishable from the record alone. This re-audit instead
  establishes identity directly from git objects at both revisions (appendix A).
- Impact: none on product/governance bytes or on any prior row's substantive evidence (test
  executions, CI runs, docker inspections are unaffected). Recorded so the prior report is not
  silently trusted on digest citations.
- Repair: none in-target. Note for strategy publication hygiene: digest citations in audit
  records must be re-verified as 64-hex before acceptance.

**Historical context verified (NOT current-state evidence; explicitly OUT of target):**
CI run 35193878477 (workflow CI, merge commit 9238e0c, 2026-09-17T07:18:27Z) completed/FAILURE
with exactly one failed job (test) and exactly one failed test:
`tests/oap/test_ba26_27_40_41_wrapper.py::Ba26ZeroIdle::test_ba26_consumption_journalized`
(AssertionError: 'invoked' not found in ['control_consumption']); summary `1 failed, 610 passed in
131.63s`; quality/security/container all success. This run's tree differs from a9c3133 only by
the oap/active pointer byte (9238e0c is the 028-a merge; a9c3133 its quiesce), i.e., byte-
identical harness. The same bytes are GREEN at a9c3133 (611/611, run 35193886320) — this audit
has therefore observed the OAP-harness consumption-journal test fail at 9238e0c and pass at
a9c3133 on identical bytes, independently confirming its non-deterministic (timing) character.
Per the human's 2026-09-22 instruction, OAP-harness remediation is explicitly OUT of target for
this audit; it is not proposed as an in-target blocker.

**Observation (SAR-010 boundary, carried from prior audit, not a finding):** cancellation
resolves the cutoff from the CURRENT active policy; with no active policy, cancellation of a
confirmed future reservation fails closed (POLICY_NOT_CONFIGURED). Release is unaffected. Fail-
safe behavior outside the named negative; re-confirmed present at a9c3133 (byte-identical).

## Judgment and boundary register

- **CRITICAL register:** CRITICAL.md at a9c3133 contains zero CRIT entries ("No CRIT entries at
  initialization") and no human dispositions (verified: grep for entry headers = 0). There are
  therefore NO open DHA gates for this milestone, and none were created by this audit.
- **D2 boundaries:** none crossed. Real deployment, real secrets, DNS/TLS, host exposure,
  production/private data, lab/Neumann contact: all excluded by the human scope and untouched.
  Operator-owned items (real SECRET_KEY/pepper, TLS proxy, host/firewall/backup storage) remain
  human/operator prerequisites for an actual deployment — prerequisites, not code blockers.
- **Human dispositions:** none applicable (no CRIT entries). Human milestone acceptance for
  M-LOCAL-PILOT-EVIDENCE and any release/deployment decision remain separate, attributable human
  judgments not made here.
- **Combined risk:** the 38 IMPLEMENTED classifications rest on a common evidence base (exact-
  head CI at a9c3133 verified live + byte-identity-verified reuse of 21f6204 evidence + this
  audit's own local re-executions and re-builds). The shared limitations are: (a) auditor is the
  same model family as development (fresh isolation, not human independence), (b) structural
  validators (oap/bin/check_ica.py etc.) prove form, not correctness, (c) live exposure (TLS
  proxy, real secrets, real host) is unexercised by design, (d) one full-rehearsal execution at
  the current head rests on byte-identity + the 21f6204 runner execution + this audit's fresh
  config-only render (stated composition, not concealment). None converts into a product defect
  at a9c3133.
- **Residual uncertainty:** real-world deployment characteristics (operator proxy behavior, real
  secret handling, backup storage, host hardening) can only be evidenced at actual controlled
  deployment time, which this audit neither performs nor approves.

## Blockers — first controlled internal-alpha Docker deployment (in-target only)

**No in-target code/evidence blockers were found** for the service being deployable through the
documented Docker/Compose path at a9c3133:
- Image builds reproducibly from the exact revision (THIS audit's local rebuild + CI container
  job at the exact head); non-root 10001:10001; all five named static/bootstrap assets present
  in the built image.
- Documented compose shapes are loopback-only and fail-closed (dev + production example,
  re-inspected at a9c3133; production db service publishes no ports); production settings refuse
  to boot without real distinct secrets/hosts/pepper (live subprocess negative in CI security
  job at the exact head).
- Production-shaped rehearsal: full-run evidence at 21f6204 (disposable CI runner, workflow-
  dispatch, success — verified live) remains valid by byte identity; this audit added a fresh
  `--config-only` render at the exact head (clean) and re-verified the script's refusal/ownership
  logic in source.
- The 611-test exact-head suite (real PG17, browser, concurrency, operational, real restore
  drill) is green at a9c3133 (run log retrieved and read); this audit's independent local
  re-execution matches (609/611; both failures root-caused non-product: F-005 midnight-boundary
  test timing — isolated re-run green; PG16 environment limitation on the PG17-specified drill —
  manual repro captured, drill green on PG17 in CI).
- Both prior findings (F-001 projection DRF label, F-002 snapshot path) are remediated in-tree
  at a9c3133 and independently re-verified; the 38-row scripted projection comparison shows zero
  residual drift.

**Out-of-target deferrals (NOT blockers, recorded with authority — a deferral is not a pass):**
1. Institutional OIDC / password reset / email workflow (SAR-036; roadmap deferred; INSTALL.md
   §12 known alpha limitations)
2. Projects / memberships / resource restrictions (SAR-036; security-model §6 — broad
   authenticated-human authorization acceptable only under a constrained trusted pilot; the
   exposure boundary is an explicit human-gate input)
3. Execution gateway / automatic physical allocation (SAR-036; SAR-002 boundary; INSTALL.md §12)
4. Notification system (SAR-036; INSTALL.md §12)
5. Monitoring stack (SAR-036 Phase 4; INSTALL.md §12)
6. SmartScheduling production cutover (SAR-030 scope / ADR0013; synthetic fixtures only)
7. Database role separation + backup hardening (security-model §6 "operational work";
   exposure-scope dependent — an input to the human gate)

Additionally out of target per the human's 2026-09-22 instruction: OAP-harness timing flake
remediation (see Historical context above).

**Human/operator prerequisites for an actual deployment (separate from this audit):** real
operator secrets (SECRET_KEY, API_TOKEN_PEPPER, POSTGRES password), real host/firewall/TLS
reverse-proxy (operator-owned per A-03/SAR-024), backup storage, and the explicit human
milestone-acceptance + deployment authorization. These are D2/human steps by the stated scope.

## Closure recommendation

Assessed ONLY at the exact audited revision a9c3133d3da36c34bd66ff4dba264d0b10bae9e0: the
M-LOCAL-PILOT-EVIDENCE requirement matrix (SAR-001..SAR-038) substantiates ALL 38 rows as
IMPLEMENTED; no ABSENT, PARTIAL or UNPROVEN rows remain. The prior audit's single PARTIAL row
(SAR-037) is resolved at this head by the in-tree F-001/F-002 remediations, independently
re-verified by this audit (line-level diffs + scripted 38-row comparison = 0 mismatches). The
Docker/Compose deployability target remains evidence-backed at this revision (fresh exact-head
build, fail-closed settings, loopback-only topology, rehearsal composition, recovery tooling,
exact-head CI verified from run logs). Product-runtime bytes are unchanged since the prior
audited revision, so every prior substantive row carries over under verified byte identity, and
each row above states its own fresh or reused evidence. This is a structural/evidentiary
assessment of a protocol re-audit; it makes no milestone-acceptance claim.

Any further action (e.g., an optional test-robustness round for the F-005 midnight boundary, an
optional projection header re-binding, or the out-of-target OAP-harness flake) requires a
separately ordered H/A/E/I/C-linked round and, if it changes relevant source, another
architecture-to-current-main re-audit at the new exact revision. Deployment, exposure, release,
and final human milestone acceptance are NOT granted by this report.

## Evidence appendix

### A. Revision and digest verification (this audit's own commands)
```text
$ git rev-parse HEAD                       # a9c3133d3da36c34bd66ff4dba264d0b10bae9e0
$ git status --porcelain                   # (empty, 0 lines, at start; after report write: only the untracked report file)
$ git log --oneline -1                     # a9c3133 028-a: quiescent — reconcile active pointer after merge of PR #56
$ sha256sum ARCHITECTURE.md
8483a070026f382bb9b698e9346f3cb33f7dea44f8190b231431585986ebb17d  ARCHITECTURE.md   # == expected 64-hex
$ sha256sum PLAN.md
d03eb29713cfbdb7e227413618396e6bb2a7a08749225979c3055dacfd461d06  PLAN.md           # == expected 64-hex
$ git show 21f6204d5f03c304991d4cd5c45a74aecdcb686a:ARCHITECTURE.md | sha256sum
182d9cf924931e846bc7965a079482b6753de762af807196ca0b87f8dffdf863  -   # TRUE prior digest (64-hex; see F-006)
$ git show 21f6204d5f03c304991d4cd5c45a74aecdcb686a:PLAN.md | sha256sum
d03eb29713cfbdb7e227413618396e6bb2a7a08749225979c3055dacfd461d06  -   # PLAN unchanged in window
$ git diff --name-status 21f6204…..a9c3133…    # exactly 13 paths (all governance/audit/OAP; see Freshness)
$ git diff --name-only 21f6204…..a9c3133… -- src/ config/ tests/ manage.py Dockerfile \
    compose.yaml compose.production.example.yaml deploy/ pyproject.toml uv.lock data/ .github/ \
    oap/bin oap/governance oap/runtime.env.example oap/strategic-instructions oap/coding-instructions oaplib
# (no output — ZERO product-runtime paths changed)
$ git merge-base --is-ancestor 21f6204… a9c3133…    # true
$ git ls-tree a9c3133… -- docs/bootstrap/1/previous/docs-architecture.md
100644 blob 246870a7771452ce3878c228b9ad7ffd8e71eda0  docs/bootstrap/1/previous/docs-architecture.md
$ git show 1fcc2c91…:pyproject.toml | grep djangorestframework   # ">=3.16,<3.17" (baseline)
$ git show 1fcc2c91…:uv.lock | grep -A1 'name = "djangorestframework"'   # version = "3.16.1" (baseline)
$ git show a9c3133…:uv.lock | grep -A1 'name = "djangorestframework"'    # version = "3.17.2" (current)
```

### B. CI runs verified at the exact audited head (GitHub API via gh 2.45.0, repo ulfe-lmi/slaif-asset-reservation)
```text
run 35193886320  CI   headSha=a9c3133d3da36c34bd66ff4dba264d0b10bae9e0  event=push  branch=main
                 status=completed  conclusion=success  (createdAt 2026-09-17T07:18:34Z, updated 07:22:01Z)
  jobs (gh run view --json jobs): quality=success  test=success  security=success  container=success
  test job (dbId 105112451594), log retrieved live (gh api …/jobs/105112451594/logs, 115,612 bytes):
    "Using CPython 3.13.14"; "platform linux -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0"
    service: postgres:17@sha256:d13db94ae661d517c5ed57c509a578d5ea64aae639871ba25294f4f42d83de28
    "======================= 611 passed in 129.10s (0:02:09) ========================"
    "tests/test_restore_drill.py ........." (9/9 incl. real PG17 dump/restore round-trip)
    "tests/browser/test_human_mvp_browser.py ......"; "tests/browser/test_pilot_path_browser.py .."
    real exclusions logged, e.g. 2026-09-17 07:20:58.972 UTC "ERROR:  conflicting key value
    violates exclusion constraint \"reservation_no_overlap_per_asset\""
run 35193886316  oap  headSha=a9c3133…  status=completed  conclusion=success  (2026-09-17T07:18:34Z)
deployment-rehearsal (workflow list): single historical run 35182574499 at 21f6204,
                 event=workflow_dispatch, conclusion=success (2026-09-17T04:36:47Z); no run at a9c3133
historical context (verified live, NOT current-state evidence):
run 35193878477  CI   headSha=9238e0c… (028-a merge commit)  conclusion=failure (2026-09-17T07:18:27Z)
  jobs: test=FAILURE, quality/security/container=success
  test job (dbId 105112425717) log: "================== 1 failed, 610 passed in 131.63s (0:02:11) ===="
  "FAILED tests/oap/test_ba26_27_40_41_wrapper.py::Ba26ZeroIdle::test_ba26_consumption_journalized
   - AssertionError: 'invoked' not found in ['control_consumption']"
  (byte-identical harness is green at a9c3133 → non-deterministic OAP-harness timing flake; OUT of target)
```

### C. Local executions (this audit; audit host as described in Identity)
Environment: PostgreSQL 16.15 server @ 127.0.0.1:5432 (17.11 client tools), disposable role
`ica2` (CREATEDB, password in no record here — dropped after audit), venv at /tmp/ica-tools/venv
(uv 0.12.5, Python 3.13.15, installed from the committed uv.lock: Django 5.2.17, DRF 3.17.2,
psycopg 3.2.13, pytest 9.1.1, Playwright chromium cached), Docker 29.1.3.
```text
$ TEST_DATABASE_URL=postgres://ica2:…@127.0.0.1:5432/ica2audit DATABASE_URL=… python -m pytest -q -p no:cacheprovider
2 failed, 609 passed in 225.82s (0:03:45)
  FAILED tests/test_pilot_path.py::test_integrated_pilot_path_shared_state_across_surfaces[chromium]
    (midnight-boundary test timing — F-005; root cause and green isolated re-run below)
  FAILED tests/test_restore_drill.py::RestoreDrillRoundTrip::test_real_round_trip_verifies_and_cleans_up
    (PG16 server vs PG17-specified drill; same environment limitation as prior F-004)
$ pytest "tests/test_pilot_path.py::test_integrated_pilot_path_shared_state_across_surfaces[chromium]" -q --no-cov
1 passed in 9.27s    (re-run at 00:31 local, away from the boundary)
Manual drill-boundary repro (disposable scratch DB, same client/server versions as CI's inverse):
  pg_dump -Fc (17.11) → pg_restore --clean --if-exists (17.11) against PG16.15 server:
  "pg_restore: error: could not execute query: ERROR:  unrecognized configuration parameter
   \"transaction_timeout\"; Command was: SET transaction_timeout = 0;"  (exact prior-F-004 mechanism)
$ docker build --quiet --tag slaif-ica-reaudit:a9c3133 .        # success
$ docker image inspect slaif-ica-reaudit:a9c3133 --format '{{.Config.User}}'   # 10001:10001
$ docker run --rm --entrypoint test slaif-ica-reaudit:a9c3133 -f <path>   # OK for all 5:
  /app/staticfiles/web/site.css
  /app/staticfiles/admin/css/base.css
  /app/staticfiles/drf_spectacular_sidecar/swagger-ui-dist/swagger-ui-bundle.js
  /app/data/bootstrap/assets.yaml
  /app/data/bootstrap/assets.schema.json
$ docker image rm slaif-ica-reaudit:a9c3133                     # deleted after inspection
$ SLAIF_REHEARSAL_PORT=18101 bash deploy/rehearse_internal_alpha_deployment.sh --config-only
  rehearsal: rendering production Compose config with synthetic env
  rehearsal: config-only=ok    (synthetic env created and removed by the script; git tree pristine)
Operational CLI on a fresh disposable DB (ica2ops, dropped after use):
$ manage.py migrate --noinput                 # all migrations applied OK (… legacy_import.0001, sessions.0001)
$ manage.py import_bootstrap_assets --input data/bootstrap/assets.yaml
  (dry-run) unchanged=0  excluded=1  conflicted=0
$ manage.py operational_check
  database=ok migrations=ok static=ok bootstrap=ok idempotency_cleanup_command=ok operational_check=ok
$ manage.py pilot_readiness_check
  aggregate-only; strict gates FAIL as expected on empty DB (active_reservable_exclusive_asset,
  active_reservation_policy, active_staff_user); PASS assets_without_effective_policy,
  database_migration_ready, expired_idempotency_records; WARN ordinary_pilot_users,
  recent_audit_events, successful_blackout_exercise   (no identifiers emitted; no mutation)
$ manage.py purge_expired_idempotency_records   # expired=0 deleted=0 remaining_expired=0
$ manage.py makemigrations --check --dry-run    # No changes detected
$ manage.py check                             # System check identified no issues (0 silenced)
Scripted projection comparison (python3, this audit's script, 38/38 rows both files):
  canonical rows: 38  projection rows: 38  TOTAL ROWS WITH ANY MISMATCH: 0
Source greps at a9c3133 (all as cited in the matrix rows): exclusion constraint + BtreeGist
(0001_initial.py:24,173-186); transaction.atomic in every lifecycle service; no subprocess/
paramiko/ssh in product src outside management commands; tokens.py hmac/32-byte secret/pepper;
env.py UNSAFE_SECRET_KEYS/env_required; compose binds (dev 127.0.0.1 only; prod app loopback
only, db no published ports); Dockerfile USER 10001:10001; web/auth.py is_active_human;
management_ui/auth.py management_required; audit/validators.py 4096 cap + forbidden keys;
logging.py redaction sets; time_utils.py fold handling; idempotency.py canonical hash +
conflict/expired codes; rehearsal script ownership lines 72/235/309/318-319; zero CLAUDE.md
files; OAP_DEVELOPMENT_MERGE_ENABLED=false (oap/runtime.env.example line 10); CRITICAL.md entry
count 0.
```

### D. Not-run / blocked states (explicit)
- Full deployment rehearsal (script without --config-only): NOT run locally by this audit (not
  required; historical full-run evidence at 21f6204 recorded in B and remains valid by byte
  identity; local full-up on a shared host avoided as unnecessary). No full rehearsal has been
  executed at a9c3133 by anyone — stated explicitly.
- PG17 real restore-drill round-trip locally: NOT re-run successfully — BLOCKED by audit-host
  PG16.15 server (exact mechanism reproduced; see C). Exact-head PG17 evidence is CI@a9c3133 (B).
- No real deployment, no real secrets, no DNS/TLS, no lab/Neumann/production contact: by scope.

### E. Environment limitations
- Audit host PostgreSQL server is 16.15; product target is PostgreSQL 17 (drill spec + compose
  image + CI service). All other suites are PG-version-insensitive for this audit's purposes and
  were re-executed; the PG17-bound drill is evidenced at the exact head via CI.
- Auditor model family equals development model family (fresh isolation; not human independence).
- The prior ICA's digest record is corrupted (F-006); this audit re-derived digests from git
  objects directly and does not rely on the prior record for identity claims.
- The workflow_dispatch rehearsal actor (jpers1) on the 21f6204 run is an observed account
  identity; this audit does not independently attest it is the attributable human principal
  (attribution is a human/strategy record matter).

### F. Disposable resources created and removed by this audit
- PG role `ica2` (login, createdb) — dropped.
- PG databases `ica2audit`, `ica2ops`, `ica2scratch` — dropped; pytest-django's
  `test_ica2audit` was auto-dropped by the test runner (verified absent).
- /tmp/ica-tools/venv (out-of-worktree), /tmp/ica-tools/*.log + CI logs, /tmp/ica-tools/
  coverage_a9c3133.local (moved out of the worktree), /tmp/ica-tools/sar_compare.py — under /tmp
  only, outside the repository.
- Docker image `slaif-ica-reaudit:a9c3133` — built, inspected, deleted.
- Rehearsal synthetic env files — created and removed by the script itself (worktree verified
  pristine after).
- Worktree /tmp/ica-a9c3133: `git status --porcelain` = 0 lines after all audit activity except
  the single permitted report artifact (this file).

## Result statement

At the exact merged product revision a9c3133d3da36c34bd66ff4dba264d0b10bae9e0, the
M-LOCAL-PILOT-EVIDENCE requirement matrix (SAR-001..SAR-038) substantiates 38/38 rows as
IMPLEMENTED, 0 PARTIAL, 0 ABSENT, 0 UNPROVEN. The prior audit's single PARTIAL (SAR-037) is
resolved by the in-tree 027-a remediations, independently re-verified by this audit; both prior
LOW findings are closed at this head. Product-runtime bytes are unchanged since 21f6204 (verified
by explicit path-restricted diff: zero product paths), so prior substantive evidence carries over
under that verified identity, supplemented by this audit's fresh exact-head CI verification
(run logs read), local full-suite re-execution, local image rebuild + inspection, fresh
config-only rehearsal render, and documented operational CLI re-runs. No in-target blockers to
the service being deployable through the documented Docker/Compose path were found; the seven
approved deferrals remain out-of-target with recorded authority; the OAP-harness flake is
explicitly out of target per the human's 2026-09-22 instruction.

**This structural/audit finding set does NOT constitute deployment approval, release readiness,
or milestone acceptance.** The human decides target readiness, milestone acceptance, release and
deployment separately and with explicit attribution; this audit never substitutes for that
decision, and no real deployment was performed or authorized here.

## Independence and structural-validation disclaimer

- This audit ran in a fresh isolated Codex sub-agent context (spawned 2026-09-21T22:16:37Z UTC
  by the strategy role for the 2026-09-22 re-audit) with no forked/inherited development context
  and no prior involvement in the audited rounds (026-a/027-a/028-a or earlier) or in the prior
  ICA. The prior ICA report was used strictly as an input/index, never as proof; every row was
  re-substantiated from source, executed tests, or live-verified CI artifacts at the exact head.
- HONEST LIMITATION: the auditor model (qwen3.8-27b) is the SAME model family as the
  development roles. Fresh isolation reduces but does not eliminate common-mode bias; this is
  NOT an independent human audit. Structural validators (oap/bin/check_ica.py and similar) check
  form only; they cannot prove independence, correctness, or closure.
- Evidence is boundary-faithful: source bytes at a9c3133, tests executed locally by this audit,
  CI runs verified at the exact head via the GitHub API with run logs retrieved, and a local
  image rebuild from the audited tree. The one full-rehearsal execution (21f6204) is cited only
  under the verified byte-identity condition, and that condition is stated in the affected row
  rather than hidden.
