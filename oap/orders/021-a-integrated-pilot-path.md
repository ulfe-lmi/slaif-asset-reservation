<!-- OAP-META
{
 "id": "021-a",
 "round": "a",
 "base_sha": "57d445e6752633665137c1001f47b7392549c431",
 "issue_number": 41,
 "branch": "codex/41-oap-021-a-integrated-pilot-path",
 "pr_mode": "CREATE_OR_RESUME",
 "previous_round": null,
 "allowed_paths": [
  "tests/test_pilot_path.py",
  "tests/browser/test_pilot_path_browser.py",
  "src/slaif_reservation (defect-repair gate R only — see Scope and forbidden_resources)",
  "oap/orders/021-a-integrated-pilot-path.md",
  "oap/active",
  "oap/reports/021-a-integrated-pilot-path.md"
 ],
 "forbidden_resources": [
  "any change under src/slaif_reservation outside the Scope item R defect-repair gate (no new features, endpoints, models, fields, migrations, settings, dependencies)",
  "any change to tests other than the two named new test files (all existing test files byte-identical)",
  "any weakening, skipping, or loosening of an assertion to make a check pass",
  "any change under docs/, deploy/, data/, .github/, oap/ helpers or workflows (no OAP expansion)",
  "new dependencies or removed dependencies",
  "deployment of any kind; real/production databases; real lab/Neumann machines; real SmartScheduling data",
  "credentials, auth files, sessions, tokens, auth homes",
  "DNS/TLS/firewall changes, public exposure, repository visibility or branch-protection changes",
  "any mutating GitHub operation except pushing this branch and opening this objective's PR",
  "merging or auto-merging any PR (merge is strategy's delegated act after review)",
  "ICA activity, milestone completion claims, canary work, or work from other drafts/objectives (legacy-import-vs-booking concurrency remains explicitly deferred)",
  "model provider endpoints other than the configured qwen-neumann role profile"
 ]
}
-->

# 021-a — Prove the integrated pilot path through the actual adapters
# (member browser, agent bearer API, staff management) with shared state

## Goal

Per-surface behavior of the three entry points is already tested in
isolation (browser MVP, web views, API v1, management UI). What is unproven
is the INTEGRATED pilot path: that one asset's reservation state is shared
consistently across all three real entry points for a realistic pilot
journey — member books in the browser, agent books against the same asset
over the bearer API, staff applies maintenance to the same asset, and
cancellation/release flow back into every surface's view. This round adds
that integrated journey with synthetic principals and fresh isolated
resources, through real adapters only (Playwright live_server with real
form login/CSRF; Django/DRF test client with a real Bearer token issued via
the real one-time-display path; staff session via real client.login). No
force_authenticate anywhere, no service-layer bypass of the boundary under
test. If a numbered check exposes a genuine baseline defect, the
defect-repair gate (Scope item R) applies; otherwise the round is
evidence-only.

## Durable provenance and requirements

- H: in-session human principal instruction 2026-09-14 — continue the
  autonomous strategy -> coding -> review -> merge loop; prefer the
  smallest product PR that materially advances a genuinely usable internal
  MVP/pilot; no canary work, no OAP expansion, no ICA (M-CONVERSION ICA
  DEFERRED by human); bootstrap drafts are not a mandatory queue.
- E: origin/main = local main = 57d445e6752633665137c1001f47b7392549c431
  (020-a quiescent, INACTIVE, CI 5/5 green at report head
  7a408278b7c632f5963fc8106fba806e36cc6538 and merge commit 4f8f144). 602 tests passed at the
  020-a implementation head. Existing per-surface coverage:
  tests/browser/test_human_mvp_browser.py (login/profile/asset filter,
  reservation create + own detail, conflict feedback, cancel/release +
  other-user denial, token create-once/revoke/owner boundary, keyboard
  smoke), tests/test_web_human_mvp.py (availability privacy/clipping,
  DST, CSRF, audit-on-create), tests/test_api_v1_reservations.py (bearer
  scope matrix, availability privacy, idempotent create/replay/conflict/
  expiry, owner-scoped lifecycle, problem details),
  tests/test_management_ui.py (role matrix, policy, blackout create/
  confirm/deactivate, cross-user management, audit list/export).
- A: SAR-001 (one reservation authority across all surfaces), SAR-005
  (UTC/DST display), SAR-006 (half-open effective-end/release), SAR-008
  (policy enforcement), SAR-009 (atomic audited lifecycle, correct
  source/actor), SAR-011 (human session boundary), SAR-012 (member
  ownership), SAR-014 (token secrecy/lifecycle), SAR-015 (one-time secret
  handling), SAR-016 (scoped API adapters), SAR-017 (strict API contract),
  SAR-018 (idempotent API mutations), SAR-019 (advisory private
  availability), SAR-020 (blackout integrity), SAR-021 (bounded audit
  evidence), SAR-032 (evidence before readiness).
- C: S-12 (one proof-sized objective), S-15 (report boundary), S-19 (real
  entry-point evidence), S-16/S-17 (exact-head review, delegated merge).
- Reconciliation: the strategic-home draft
  020-a-pilot-path-actual-adapters.md (DRAFT UNTIL STRATEGIC
  RECONCILIATION; bootstrap-era numbering) is retired as a queue item and
  reconciled into this objective. Its draft number does not imply queue
  position; the objective ID is new (021-a). Its evidence-matrix
  obligation is satisfied inside the report as a
  SAR -> check -> test -> actual-revision table (no repo doc change).

## Current reconciled state and prerequisites

- Base main (local and remote): 57d445e6752633665137c1001f47b7392549c431.
  Worktree must be clean on main before starting; `oap/active` absent
  (INACTIVE).
- Fresh round: no local/remote branch codex/41-oap-021-a-integrated-pilot-
  path, no PR for issue #41 (verify with git ls-remote and gh before
  creation); pr_mode CREATE_OR_RESUME resolves to CREATE. The PR number is
  GitHub-assigned; record it truthfully.
- Known facts (verify, do not assume): the browser fixture conventions in
  tests/browser/test_human_mvp_browser.py (member_user/other_user/
  service_account/machine/asset `browser-gpu` reservable +
  verification_required/policy 30..240 min, horizon 30 d, lead 0, cutoff
  0, 10 upcoming, 3 concurrent, purpose not required; `_login` via
  get_by_label Email/Password + button "Log in"; live_server;
  django_db(transaction=True)); the API mutation header is `Idempotency-
  Key`; the Bearer authenticator is exercised by the existing API tests'
  client fixture pattern; the web token one-time display is proven by
  test_browser_api_token_create_once_revoke_and_owner_boundary; release
  preconditions and the blackout affected-reservation confirmation
  trigger are defined in the services (read them; the 020-a report
  documents create_reservation/create_blackout/deactivate_blackout lock
  sequences).

## Ordered read set

Standard compact read set, plus: tests/browser/test_human_mvp_browser.py
(in full), tests/test_api_v1_reservations.py (bearer + idempotency
patterns), tests/test_management_ui.py (blackout + audit patterns), the
web token views (one-time display), the API Bearer authenticator and
reservation views, reservations/services.py (create/cancel/release,
blackout create/deactivate, availability), the audit model/export view,
and the web availability view.

## Scope and allowed paths

Two NEW test files only (existing test files stay byte-identical), plus
the defect-repair gate R:

1. tests/browser/test_pilot_path_browser.py — Playwright journey (real
   form login, real CSRF, live_server, transaction=True, reuse the
   existing fixture conventions):
   a. Member logs in, browses assets (reservable GPU child visible;
      non-reservable parent not bookable), opens availability for the GPU,
      creates a reservation in a future policy-valid window with local
      time values, sees it in the own list (soonest-first) and on the
      detail page with correct local display.
   b. The member then releases or cancels per available lifecycle state —
      whichever state the service permits for the created reservation is
      exercised through the real form (record which one and why in the
      report).
2. tests/test_pilot_path.py — Django/DRF client journey over the same
   asset, sharing state with item 1's reservation where the checks say so:
   a. Agent token issued via the REAL one-time-display path (drive the
      member token flow through the real view/service and capture the
      one-time value; never read the token value from the DB row); real
      Bearer on /api/v1/me/ (safe context, no verifier/pepper/admin
      fields).
   b. GET availability for the same asset: the member's reservation window
      busy, no owner identity/purpose leakage (SAR-019).
   c. POST /api/v1/reservations/ for a second non-overlapping future
      window with Idempotency-Key -> 201 + Location; exact replay ->
      original response, exactly one success audit; changed body same key
      -> idempotency_conflict.
   d. Cross-surface exclusivity (SAR-001): the member's browser
      availability (from item 1's session, second browser context or new
      page) now shows the agent's window busy; a member browser create
      attempt on that exact window gets conflict feedback (form
      re-displayed, input preserved) and NO second reservation; DB holds
      exactly the expected reservation count on the asset.
   e. Staff journey (real staff session via client.login with password;
      CSRF on mutations): create a blackout over the next free window of
      the same asset — if an existing confirmed reservation is overlapped
      the affected-reservation confirmation path must be exercised (list
      shown, explicit confirm, no auto-cancel); then member browser
      availability clips the blackout window WITHOUT revealing the
      reason; member browser create on the window rejected; agent API
      create on the window rejected with a blackout-related problem
      detail and no reason leakage; staff deactivates; BOTH the member
      browser and the agent API can then book the window again.
   f. Cross-surface lifecycle (SAR-006): agent cancels via API (idempotent
      replay returns the original accepted response); the cancelled window
      is free again on the member's availability. A reservation in
      ACTIVE state (start in the past) is released via the member browser
      (or agent API, record which); after release the consumed prefix
      [start_at, effective_end_at) still blocks a new create while the
      remainder is bookable.
   g. Audit trail (staff session, bounded window): the audit list shows
      create (source web, actor member), create (source api), cancel
      (api), release (web), blackout create + deactivate (management,
      staff actor) with correlation; CSV export contains no token values
      and no raw credentials and honors the bounded filters.
   h. Integrated negatives: revoked agent token -> 401 generic problem
      detail (no disclosure); another member's browser/API view of the
      agent's reservation detail -> non-disclosing 404 with endpoint code;
      service-account login to the member UI rejected.
3. R — Defect-repair gate. If any check above fails against the current
   product code and the root cause is a genuine baseline defect inside
   src/slaif_reservation that can be fixed minimally and
   semantics-preservingly (no new endpoints/models/fields/migrations/
   dependencies/settings; no lock-ordering, interval, or policy-semantics
   change unless the defect IS such a semantics violation and the fix
   restores the documented semantics in ARCHITECTURE.md): implement the
   minimal fix in the same PR with a failing->passing regression test,
   and document per acceptance criterion 3. If the defect cannot be fixed
   truthfully inside this gate (needs new semantics, a feature, a
   migration, or touches another product surface): STOP, publish a
   truthful PARTIAL/FAILED report naming the exact failing check,
   observed vs expected, minimal reproduction, and the affected surface —
   no weakened assertions, no out-of-scope repair. Strategy decides the
   repair round.

Non-negotiable: a test must never be weakened, skipped, or loosened to
make a check pass.

## Non-goals

- No new features, endpoints, models, fields, migrations, or dependencies;
  no docs/ changes (evidence lives in the report only).
- No OAP/governance/helper changes, no canary work, no ICA, no milestone
  claim, no readiness-review expansion.
- No legacy-import-vs-booking concurrency work (explicitly deferred).
- No deployment, no real data, no lab/Neumann contact, no visibility or
  branch-protection change.
- No merge, auto-merge, approval or settings change.

## Numbered acceptance criteria

1. The report records the pre-change state: the existing per-surface test
   names (what is already proven, so nothing is duplicated), the exact
   one-time token path used, the release precondition that applied, and
   the blackout-confirmation trigger conditions observed in the services.
2. The new integrated tests exist in exactly the two allowed new test
   files and pass against the current product code (or after gate-R
   repairs); the full suite is green and every pre-existing test file is
   byte-identical (prove by diff in the report).
3. If any gate-R repair was made, the report names for each: the exact
   failing check, observed vs expected, the minimal diff, the
   semantics-preservation rationale, and the failing->passing evidence;
   any repair touching service locking/interval/policy semantics is
   explicitly flagged as such.
4. All normal CI-equivalent gates green at the exact implementation head:
   full pytest (both new files included; real PostgreSQL 17; Playwright),
   ruff check, ruff format --check, mypy, makemigrations --check
   --dry-run, manage.py check, operational_check, spectacular --validate
   --fail-on-warn; and the CI container + security (pip-audit) jobs
   passing at the report head.
5. If a check cannot hold truthfully and the defect is outside gate R:
   PARTIAL/FAILED with the exact failing boundary and minimal repro; no
   weakened assertions; no product change beyond gate R.
6. The diff touches only allowed_paths.

## Deferred human adjudication

- Decision: NONE
