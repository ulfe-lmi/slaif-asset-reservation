<!-- OAP-META
{
 "kind": "report",
 "id": "021-a",
 "order_path": "oap/orders/021-a-integrated-pilot-path.md",
 "order_sha256": "c9269db0594a1d8c224dd228362b8b1c4b6fb6b9224b94a7a50f2defbe2b222e",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "issue_number": 41,
 "pr_number": 42,
 "branch": "codex/41-oap-021-a-integrated-pilot-path",
 "implementation_head": "9781ed6c7229aea283b759ce863cb13608312d1c",
 "base_sha": "57d445e6752633665137c1001f47b7392549c431",
 "result": "COMPLETE",
 "observed_implementation_ci": {
  "observed_head": "9781ed6c7229aea283b759ce863cb13608312d1c",
  "runs": [
   {"run_id": 34808196031, "workflow": "CI", "jobs": {"quality": "success", "test": "success", "security": "success", "container": "success"}},
   {"run_id": 34808196033, "workflow": "oap", "jobs": {"oap-harness": "success"}}
  ]
 },
 "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 021-a report — integrated pilot path through the actual adapters

Order digest: c9269db0594a1d8c224dd228362b8b1c4b6fb6b9224b94a7a50f2defbe2b222e
(committed `oap/orders/021-a-integrated-pilot-path.md`; byte-identical to the
materialized `.FINAL` source — `sha256sum` of both files:
c9269db0594a1d8c224dd228362b8b1c4b6fb6b9224b94a7a50f2defbe2b222e).

Implementation head SHA: 9781ed6c7229aea283b759ce863cb13608312d1c

Report publication commit: SELF

**Result: COMPLETE** — the integrated pilot journey exists in exactly the
two allowed new test files and passes against the current product code on
real PostgreSQL (local 17 container; CI PostgreSQL 17 service) and real
Chromium, with shared reservation state across the member browser, the
agent bearer API, and the staff management surface. No numbered check
exposed a genuine baseline defect, so the defect-repair gate (Scope item R)
was not triggered. No product code was changed and no test was weakened.

## Reconciliation at start (C-05/C-06/CP-03)

- Ordered reads: root router → `oap/coding-instructions/AGENTS.md` →
  `ARCHITECTURE-for-agents.md` → `OAP-COMMUNICATION-coding-agent.md` →
  exact active order → `SECURITY-CORE.md`/`TESTING-CORE.md` → ordered
  subtree excerpts only: `tests/browser/test_human_mvp_browser.py` (in
  full), `tests/test_api_v1_reservations.py` (bearer + idempotency
  patterns), `tests/test_management_ui.py` (blackout + audit + CSRF
  patterns), `tests/conftest.py` + `tests/browser/conftest.py`, the web
  token views/templates (one-time display), `web/views.py`,
  `web/forms.py`, `web/availability.py`, `web/selectors.py`, web
  availability/reservation/asset templates, the API Bearer
  authenticator, `api/reservation_views.py`, `api/problem.py`,
  `api/serializers.py` (representations), `api/urls.py`,
  `reservations/services.py` (create/cancel/release, blackout
  create/deactivate, overlap helpers), `reservations/models.py` (fields,
  exclusion constraint, `derive_lifecycle`), `accounts/services.py` +
  `accounts/tokens.py` (token issuance/one-time value), `audit/models.py`,
  `management_ui/views.py` + `forms.py` + `selectors.py` + audit/blackout
  templates, `config/urls.py` + `web/urls.py` + `api/urls.py`,
  `pyproject.toml`, test/base settings, `.github/workflows/ci.yml`.
- `oap/active` = exactly `021-a` + LF (6 bytes). Wrapper had already
  consumed the control OK; not consumed again.
- Local main = remote `origin/main` =
  57d445e6752633665137c1001f47b7392549c431 (= the order's `base_sha`;
  020-a quiescent on top of merged PR #40). Worktree clean except the
  materialized order (untracked
  `oap/orders/021-a-integrated-pilot-path.FINAL.md`) and the pointer
  (untracked `oap/active`). Fresh round: no local/remote branch, no PR for
  issue #41 (`git ls-remote` + `gh` before creation);
  `pr_mode=CREATE_OR_RESUME` resolved to CREATE. PR #42
  (GitHub-assigned number) on the order's exact branch, base `main`.
- Order hash check: committed order file sha256
  c9269db0594a1d8c224dd228362b8b1c4b6fb6b9224b94a7a50f2defbe2b222e matches
  the `.FINAL` source. DHA declaration: `- Decision: NONE` (no APPEND, no
  CRITICAL change this round).

## Pre-change state (acceptance criterion 1)

Existing per-surface coverage (what is already proven, so the new journey
duplicates none of it):

- `tests/browser/test_human_mvp_browser.py`:
  `test_browser_login_profile_asset_filter_and_post_logout`,
  `test_browser_successful_reservation_creation_and_own_detail`,
  `test_browser_conflict_feedback_preserves_input`,
  `test_browser_cancel_release_and_other_user_denial`,
  `test_browser_api_token_create_once_revoke_and_owner_boundary`,
  `test_browser_keyboard_navigation_smoke`.
- `tests/test_web_human_mvp.py`: login/service-account denial and safe
  next, disallowed-session termination, POST-only logout, profile
  timezone handling (including fail-closed invalid stored zones),
  chronological owner-bounded lists, bounded database pages, member asset
  browsing privacy, staff-only asset API, availability clipping/merging
  and privacy (including exact busy/free rules and policy boundaries),
  DST nonexistent/ambiguous form rejection, create-via-domain-service
  with preserved conflict input, duplicate form submission, owner
  non-disclosure, cancel/release through authoritative services,
  audit-on-create, CSRF on state-changing forms, GET non-mutation,
  UTC markup with local visible text.
- `tests/test_api_v1_reservations.py`: bearer scope matrix, staff-only
  asset API, availability privacy and interval semantics, blackout
  inclusion without reason/identity, invalid-parameter problem details,
  idempotent create with replay and single success audit, expired-record
  failure without mutation, same-key-different-body conflict, independent
  keys per token, concurrent create/conflict once, owner-scoped
  list/detail/cancel/release, endpoint-specific non-disclosing 404s,
  list filter validation, idempotency-key and aware-timestamp
  requirements.
- `tests/test_management_ui.py`: role matrix, member-route owner
  scoping, policy management with audit, blackout model/services and
  creation confirmation, blackout blocking of web/API creates and
  half-open boundary, blackout availability privacy and deactivation,
  blackout audit-rollback, staff cross-user management with CSRF, audit
  browsing/export privacy and bounded filters, management reservation
  filters, CSRF on all management mutations, GET non-mutation, policy
  audit rollback, admin delete boundaries.

Exact one-time token path used by the new journey: web `token_create`
view (`POST /tokens/new/` with CSRF, real `client.login`) →
`issue_api_token` service → rendered `web/token_created.html` whose HTML
carries the sole bearer value as `OneTimeBearerToken` with
`Cache-Control: no-store, private`, `Pragma: no-cache`,
`Referrer-Policy: no-referrer`. The one-time value is captured with the
regex `sar_[0-9a-f]{32}_[A-Za-z0-9_-]+` from the rendered response/page;
the `ApiToken` DB row is read only for non-secret fields
(`display_prefix`, `scopes`, `id` for the revoke call) and never for the
bearer value; the stored verifier is used only in absence assertions.

Release precondition that applied (read from `release_reservation`):
`status == confirmed` **and** `start_at < now < effective_end_at` (strict);
release then sets `status=released`, `released_at=now`,
`effective_end_at=now` while `end_at` stays immutable. Cancellation
requires `status == confirmed`, `start_at > now`, and
`now <= start_at - cancellation_cutoff_minutes`. Therefore a freshly
created future reservation is UPCOMING and the only lifecycle action the
service permits for it is cancellation; the web detail page renders the
cancel form only for the UPCOMING lifecycle and the release form only for
the ACTIVE lifecycle. That is why scope item 1b exercises CANCELLATION
(via the real browser form) and why the journey's release leg uses a
separately created ACTIVE reservation (start in the past) released via
the member browser (chosen over the agent API for that leg, recorded here
per the order).

Blackout-confirmation trigger conditions observed in the services:
`create_blackout` computes `overlapping_blocking_reservations` (status
confirmed/released, half-open overlap with `[start_at, end_at)`) and
raises `BLACKOUT_CONFLICT` iff overlaps exist and
`confirmed_overlap` is not `True`; the management view, on POST, re-renders
the form with the error "Confirm creation because reservations overlap
this blackout." plus the "Overlapping reservations" list (reservation
UUID + owner display name) and creates no blackout row until the
`confirm_overlaps` checkbox is submitted. Confirmation does not
auto-cancel or auto-release affected reservations (the journey's agent
reservation stayed `confirmed` after the blackout was created over it).

## New integrated tests (acceptance criterion 2)

Two NEW test files only; no pre-existing test file was touched.

1. `tests/browser/test_pilot_path_browser.py` (2 tests,
   `@pytest.mark.django_db(transaction=True)`, Playwright live_server,
   real form login/CSRF, fixture conventions of
   `test_human_mvp_browser.py` — member with `Europe/Ljubljana`,
   non-reservable parent machine, reservable `verification_required` GPU
   child, exact-asset policy 30..240 min / 30 d horizon / 0 lead /
   0 cutoff / 10 upcoming / 3 concurrent / purpose not required):
   - `test_pilot_browser_member_books_and_sees_own_reservation` — scope
     1a: login; asset list shows the GPU child; the non-reservable
     parent's detail page has no "Reserve this asset" link and shows
     "This asset is not reservable."; GPU availability section (no busy
     intervals, free intervals listed); two reservations created with
     local time values in future policy-valid windows; own list shows
     both under Upcoming with the earlier reservation before the later
     one (soonest-first); the detail page shows the correct local
     (Europe/Ljubljana) start/end display.
   - `test_pilot_browser_member_cancels_upcoming_via_real_form` — scope
     1b: created reservation detail shows the UPCOMING lifecycle with
     exactly one "Cancel reservation" button and zero "Release
     reservation" buttons (the permitted action for the created
     reservation, per the precondition above); cancellation through the
     real form succeeds, shows "Reservation cancelled" and the cancelled
     state, and the window no longer blocks availability.

2. `tests/test_pilot_path.py` (1 test, one sequential
   `transaction=True` journey over one shared asset, driving all three
   real entry points; `page` + `live_server` for the browser surface,
   Django `Client` with real `client.login` + CSRF for staff/agent/other
   web flows, plain `Client` with real Bearer for the API surface — no
   `force_authenticate` anywhere, no service-layer bypass of the
   boundary under test):
   `test_integrated_pilot_path_shared_state_across_surfaces` covers, in
   order:
   - (2a) agent token via the real one-time-display path; `GET
     /api/v1/me/` returns 200 with the principal id and no email /
     verifier / pepper / admin fields; the member then books through the
     real browser form (shared state for the later checks).
   - (2b) agent availability view for the same asset: the member's
     window is exactly the busy interval with label "Unavailable" and
     `reservation_id: null`; no member email/display name/purpose/UUID
     in the body (SAR-019).
   - (2c) agent `POST /api/v1/reservations/` for a non-overlapping future
     window with `Idempotency-Key` → 201 + `Location`; exact replay →
     201 with `X-Idempotent-Replay: true`, identical body/Location,
     exactly one success audit; changed body same key → 409
     `idempotency_conflict`; DB holds exactly 2 reservations on the
     asset.
   - (2d) cross-surface exclusivity (SAR-001): the member's browser
     availability (the item-1 session) shows the agent's window busy
     with no agent identity/purpose leakage; a member browser create on
     that exact window gets "That time is no longer available" with the
     input preserved and no second reservation (DB count still 2).
   - (2e) staff journey (real `client.login`, CSRF on mutations):
     blackout over the next free window of the same asset, overlapping
     the agent's confirmed reservation — the first POST re-renders the
     form with the "Overlapping reservations" list (reservation UUID +
     owner display name) and the confirmation error, creating nothing;
     the explicit confirm creates the blackout with
     `overlapping_reservations: 1` audit metadata and no auto-cancel;
     the member browser availability clips the blackout window without
     revealing the reason; member browser create on the window is
     rejected ("That time is unavailable for maintenance."); agent API
     create on the window is 409 `blackout_conflict` with no reason
     leakage; staff deactivates (POST + CSRF); then BOTH the member
     browser and the agent API book (parts of) the window again.
   - (2f) cross-surface lifecycle (SAR-006): the agent cancels via the
     API — the idempotent replay returns the original accepted response
     (`X-Idempotent-Replay: true`, identical body, exactly one
     cancellation audit) — and the cancelled window is free again on the
     member's availability (its end becomes a free-interval boundary and
     its start no longer appears as a busy boundary). A reservation in
     ACTIVE state (start in the past, created directly for setup) is
     released via the member browser (real form); after release the
     consumed prefix `[start_at, effective_end_at)` still blocks (a
     service-level create overlapping the prefix under a consistent
     pre-release clock raises the domain conflict; the availability still
     shows the prefix) while the remainder is bookable through the real
     browser form.
   - (2g) audit trail (staff session, bounded `occurred_from` window):
     exactly the 10 expected events with correct action/source/actor —
     `api_token.created` (web, agent), `reservation.created` ×3 (web,
     member), `reservation.created` ×2 (api, agent),
     `reservation.cancelled` (api, agent), `reservation.released` (web,
     member), `maintenance_blackout.created` +
     `maintenance_blackout.deactivated` (admin, staff); every target is
     visible in the list; the API-created reservation's audit event
     carries the request correlation id and the browser-created one is
     browsable with its correlation shown; the CSV export contains no
     one-time token value, no verifier, no password, no
     `Authorization`/`pepper`, and honors the bounded filter
     (`occurred_to` at the blackout-creation instant includes
     `maintenance_blackout.created` and excludes
     `maintenance_blackout.deactivated`).
   - (2h) integrated negatives: revoked agent token (real web revoke
     flow) → 401 generic problem detail `invalid_token` with no
     disclosure of the token value, token id, owner email, or verifier;
     another member's API view of the agent's reservation detail → 404
     `reservation_not_found` with no purpose/identity leakage, and the
     same member's browser view (fresh context, real form login) → HTTP
     404 without leakage; service-account login to the member UI is
     rejected ("Enter a valid email address and password", stays on
     `/login/`).
   - Final shared-asset state asserted: 6 reservation rows, 1 (now
     inactive) blackout.

Pre-existing-test byte-identity (proven by diff):
`git diff 57d445e6752633665137c1001f47b7392549c431 9781ed6c7229aea283b759ce863cb13608312d1c --stat -- tests/`
shows only the two new files (`tests/browser/test_pilot_path_browser.py`
+241, `tests/test_pilot_path.py` +772; 1013 insertions, 0 deletions);
`git show --stat 9781ed6c…` for the whole commit shows exactly 4 files —
the two new tests, `oap/active` (+1), `oap/orders/021-a-integrated-
pilot-path.md` (+249) — 1263 insertions, 0 deletions. No `src/`, no docs,
no dependency or governance change.

## Defect-repair gate R (acceptance criterion 3)

Not triggered. Every numbered check held against the current product
code on the first green run of the focused files (after test-side
corrections only, documented below); no baseline defect was observed, so
no product repair was made and no `src/slaif_reservation` byte changed.

Test-side corrections during development (all inside the two new files,
none weakening an assertion — each made a check more precise):

- Staff/agent/other web-flow POSTs needed the CSRF cookie primed by
  rendering the form page first (matching the existing
  `test_management_ui.py` pattern); added a form GET and fresh
  `HTTP_X_CSRFTOKEN` reads before each mutation.
- The "cancelled window is free again" check was corrected to compare
  free-interval boundaries (the availability renders interval endpoints,
  not interior points): the cancelled window's end is now a free-interval
  boundary and its start no longer appears as a busy boundary.
- The consumed-prefix probe window was corrected to start after the
  probe clock (a start before the probe clock raises
  `RESERVATION_IN_PAST` first) while still overlapping the consumed
  prefix, so the domain overlap check is what rejects it.

## Gates (acceptance criterion 4)

Local, at implementation head 9781ed6c7229aea283b759ce863cb13608312d1c
(disposable `postgres:17` container `slaif-oap-021a-testpg`, loopback
127.0.0.1:54330 only, throwaway volume `slaif-oap-021a-testpg-data`;
migrations, bootstrap import and
`purge_expired_idempotency_records` applied to the disposable DB before
gates; working tree identical to the committed tree at that head):

- Focused: `uv run --env-file .env pytest
  --ds=slaif_reservation.config.settings.test
  tests/browser/test_pilot_path_browser.py tests/test_pilot_path.py` →
  **3 passed** (2 browser + 1 journey), PASSED; repeated 3 times
  consecutively (3 passed each time).
- Full: `env -u OAP_ROLE uv run --env-file .env pytest
  --ds=slaif_reservation.config.settings.test` → **605 passed**
  (0 failed, 0 skipped) in 184.58s = 602 baseline at the 020-a head + 3
  new tests, PASSED (see Local-environment notes for `OAP_ROLE`).
- `uv sync --locked --all-groups` PASSED (71 packages resolved, 68
  checked).
- `uv run ruff check .` PASSED; `uv run ruff format --check .` PASSED
  (183 files already formatted).
- `uv run mypy src` PASSED (119 source files, strict).
- `uv run --env-file .env python manage.py check` PASSED (0 issues).
- `uv run --env-file .env python manage.py makemigrations --check
  --dry-run` PASSED (no changes).
- `uv run --env-file .env python manage.py spectacular --validate
  --fail-on-warn` PASSED (rc=0).
- `uv run --env-file .env python manage.py operational_check` PASSED
  (database/migrations/static/bootstrap/idempotency_cleanup_command/
  operational all ok).
- `uv run pip-audit` PASSED (no known vulnerabilities).
- `git diff --check` PASSED.

CI at the exact implementation head 9781ed6c7229aea283b759ce863cb13608312d1c
(observed after publication of the implementation commit, before this
report was written):

- CI run 34808196031: quality **success**, test **success** (log line
  `605 passed in 120.36s` = 602 baseline + 3 new tests, real PostgreSQL
  17 service), security **success**, container **success**.
- oap run 34808196033: oap-harness **success**.
- Report-head CI: NOT YET OBSERVED AT AUTHORING (the report commit lands
  after this report's content was frozen).

## SAR → check → test → actual revision (evidence matrix)

Actual revision for every row: 9781ed6c7229aea283b759ce863cb13608312d1c.
"Journey" = `test_integrated_pilot_path_shared_state_across_surfaces` in
`tests/test_pilot_path.py`; "Browser" = the two tests in
`tests/browser/test_pilot_path_browser.py`.

| SAR | Check | Test |
| --- | --- | --- |
| SAR-001 | 2d cross-surface exclusivity; DB count exact | Journey |
| SAR-005 | Local form input and local display (Europe/Ljubljana) | Browser (both), Journey (2d/2e/2f clips) |
| SAR-006 | 2f release: consumed prefix blocks (service conflict + availability clip), remainder bookable, `end_at` immutable | Journey |
| SAR-008 | All journey windows policy-valid (30..240 min, 30 d, lead/cutoff/upcoming/concurrent) | Browser, Journey |
| SAR-009 | 2g every mutation has its audit event with source/actor/correlation | Journey |
| SAR-011 | 2h service-account login rejected; staff session via real login; CSRF on staff mutations | Journey |
| SAR-012 | 2h other-member browser/API 404 non-disclosing | Journey |
| SAR-014 | 2a token issue + one-time display; 2h revoked token → 401 | Journey |
| SAR-015 | 2a no-store/private/no-referrer; verifier absent from page and CSV; one-time value never read from DB | Journey |
| SAR-016 | 2a `me/`; 2b availability scope; 2c/2d/2e/2f scoped reservation endpoints | Journey |
| SAR-017 | 2c/2d/2e/2f/2h problem details (`idempotency_conflict`, `blackout_conflict`, `reservation_not_found`, `invalid_token`), UTC representations, no leakage | Journey |
| SAR-018 | 2c create idempotency (201 + Location, replay, changed-body conflict); 2f cancel replay | Journey |
| SAR-019 | 2b/2d availability privacy; 2e blackout clip without reason | Journey |
| SAR-020 | 2e blackout blocks both surfaces, confirmation path, no auto-cancel, deactivation restores bookability | Journey |
| SAR-021 | 2g bounded audit window, correlation, credential-free CSV, bounded filters honored | Journey |
| SAR-032 | Full evidence at the exact head (this report + observed CI) | — |

## Acceptance criteria verdict

1. **MET** — pre-change state recorded above: existing per-surface test
   names, exact one-time token path, the release/cancel preconditions
   that applied (and why item 1b exercises cancellation and the release
   leg uses an ACTIVE reservation via the member browser), and the
   blackout-confirmation trigger conditions observed in the services.
2. **MET** — the new integrated tests exist in exactly the two allowed
   new test files and pass against the current product code (no gate-R
   repair was needed); the full suite is green (605 passed locally;
   605 passed in CI at the exact head); every pre-existing test file is
   byte-identical (diff evidence above).
3. **MET (N/A in substance)** — no gate-R repair was made; the stop
   condition was not triggered and no service locking/interval/policy
   semantics were touched.
4. **MET** — all normal CI-equivalent gates green at the exact
   implementation head: full pytest (both new files included; real
   PostgreSQL 17; Playwright/Chromium), ruff check, ruff format --check,
   mypy, makemigrations --check --dry-run, manage.py check,
   operational_check, spectacular --validate --fail-on-warn, pip-audit,
   git diff --check; CI quality/test/security/container and oap-harness
   all success at head 9781ed6c7229aea283b759ce863cb13608312d1c.
5. **MET (N/A in substance)** — no check failed against product code;
   no PARTIAL/FAILED stop was required; no product change beyond gate R
   (none made).
6. **MET** — the diff touches only allowed_paths: the two new test files
   plus `oap/active` and `oap/orders/021-a-integrated-pilot-path.md`
   (report lands as the separate report-only commit).

## Local-environment notes (evidence index, not defects)

- The full-suite local run used `env -u OAP_ROLE`: this coding session's
  launcher exports `OAP_ROLE=CODING`, and
  `tests/oap/test_ba38_39_tmux_config.py::test_ba39_strategic_same_
  prerequisites` refuses a conflicting role by design (same documented
  artifact as round 020-a). CI sets no such variable; with it unset the
  whole suite — including the OAP harness tests — passes.
- With the untracked strategy-side `.FINAL` source present locally,
  `tests/oap/test_ba51_52_continuity.py::test_ba52_real_reports_orders_
  history_untouched` still PASSED this round because the published
  order copy is not committed until the implementation commit, so the
  pointer bound exactly one order file at collection time.
- No other local failures: 605 passed / 0 failed / 0 skipped.

## Uncertainty, privacy, dependencies, limits

- The journey test is one long sequential transaction; a mid-journey
  failure stops later checks (they are intentionally ordered because
  each check builds on the shared state). Focused re-runs (3 consecutive
  green runs locally plus the CI run) show no timing flakiness on this
  host; the timing-sensitive parts (release point vs. minute-floored
  form values, prefix probe clock) have explicit margin by construction.
- Availability-render assertions compare interval boundary text (local
  time strings), which is what the surfaces actually display; DB-level
  facts are asserted directly (counts, statuses, timestamps, audit
  rows) wherever precise.
- No credentials, tokens, pepper, or private data appear in this report,
  the tests, or the diff; test users/passwords are synthetic sentinels
  matching the suite's existing convention. Disposable infrastructure:
  container `slaif-oap-021a-testpg`, volume `slaif-oap-021a-testpg-data`,
  port 127.0.0.1:54330 (loopback only), all owned by this round and
  slated for cleanup; no production/lab/Neumann/real-export contact.
- DHA: `- Decision: NONE` — no CRITICAL append, no human adjudication,
  no gate clearance performed by coding.
- Limits: this round proves the integrated pilot path across the three
  real entry points only; legacy-import-vs-booking concurrency remains
  explicitly deferred per the order. Development merge is strategy's
  delegated act after review; coding has not merged, approved, or
  enabled auto-merge. This report is not a release, deployment, or
  milestone certificate.
