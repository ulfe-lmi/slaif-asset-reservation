<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "054-a",
  "order_path": "oap/orders/054-a-asset-reservation-calendar.md",
  "order_sha256": "85f59b045027ef6cc75c6de01a71c1c6e1279d49f8d4bd820048c047eef2b52f",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 111,
  "pr_number": 112,
  "branch": "codex/111-oap-054-a-asset-reservation-calendar",
  "implementation_head": "026aea744f0a134d2516a2a5bd1728b3a244adc2",
  "base_sha": "1e469af959ef69e3624390ec591929b84f6c6774",
  "result": "PARTIAL",
  "partial_reason": "All in-scope acceptance criteria passed with evidence; the exact-head security CI job is red solely on a pip-audit advisory (certifi 2026.6.17, PYSEC-2026-4320, fix 2026.10.19) in the UNCHANGED pre-existing uv.lock, which this order forbids changing (no dependency/lockfile changes). Base main 1e469af was green 2026-10-19T02:44Z (run 39191387100) before the advisory appeared in the advisory DB; the same advisory reproduces locally on the untouched lockfile.",
  "observed_implementation_ci": {
    "observed_head": "026aea744f0a134d2516a2a5bd1728b3a244adc2",
    "runs": [
      {
        "run_id": 39508342100,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "security": "failure",
          "container": "success",
          "test": "success"
        }
      },
      {
        "run_id": 39508342116,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ],
    "test_job_summary": "1295 passed, 1 warning in 616.77s (0:10:16)",
    "warning": "tests/test_product_entry.py:568 UserWarning: Overriding setting DATABASES can lead to unexpected behavior (pre-existing, intentional DB-unavailable negative test, unrelated)",
    "security_failure_detail": "pip-audit: certifi 2026.6.17 PYSEC-2026-4320 (Fix Versions 2026.10.19); uv.lock byte-identical to base (git diff empty); same finding reproduced locally at base-equivalent lock state",
    "oap_harness_summary": "job success (own path-gated job)"
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 054-a — execution report: read-only calendar for one asset

Implementation head SHA: 026aea744f0a134d2516a2a5bd1728b3a244adc2
Report publication commit: SELF

## Identity and result

PARTIAL for order 054-a (D0, `Decision: NONE`), a NEW objective after merged
053-b: issue #111, PR #112 (open, base main, `Closes #111`), branch
`codex/111-oap-054-a-asset-reservation-calendar`, base main
`1e469af959ef69e3624390ec591929b84f6c6774` (verified equal to
`origin/main` before editing; all seven order source hashes verified against
working-tree bytes; governance revision
`14fc20b1ff52788974fd3f282322afc9d71362f9` present in history; active
pointer exactly `054-a` + LF, 6 bytes). One implementation commit
`026aea744f0a134d2516a2a5bd1728b3a244adc2` (first parent the base) contains
exactly the ordered allowed-path changes plus the order bytes
(`oap/orders/054-a-asset-reservation-calendar.md`, state FINAL, SHA-256
`85f59b045027ef6cc75c6de01a71c1c6e1279d49f8d4bd820048c047eef2b52f`) and the
`oap/active` pointer. No merge, self-approval or auto-merge; no new
issue/PR beyond the ordered single PR.

PARTIAL, not COMPLETE, for one external reason only: at the exact
implementation head the four required CI jobs were quality=success,
test=success, container=success, **security=failure** (oap-harness=success
in its own run). The security job fails in 12s on `uv run pip-audit`:
`certifi 2026.6.17 PYSEC-2026-4320 (fix 2026.10.19)`. `uv.lock` is
byte-identical to the base (`git diff` empty) and this order forbids
dependency/lockfile changes, so the failure is not repairable within this
order's scope. It is time-external to this change: base main
`1e469af959ef69e3624390ec591929b84f6c6774` was fully green
(2026-10-19T02:44Z, CI run 39191387100) before the advisory appeared in the
advisory database, and the identical finding reproduces locally on the
untouched lockfile. The finding is handed to strategy with the evidence and
the obvious alternative (a separate small dependency-bump order or an
explicit risk disposition); CODING did not choose or admit it.

## Numbered acceptance evidence

### 1. Authorization and navigation — PASSED

New GET route `reservations/calendar/<uuid:asset_id>/`
(`management-ui:reservation-calendar`) under `/manage/reservations/`, guarded
by the same `management_required("view_all_reservations")` decorator as All
reservations (source: `src/slaif_reservation/management_ui/urls.py`,
`views.py`). Focused tests (`tests/test_reservation_calendar.py`), real
PostgreSQL:

- anonymous GET -> 302 to `/login/?next=...`; active member with only
  `book_assets` -> 403; active Staff-without-grant -> 403; staff with only
  the Administration `reservations.view_reservation` model View permission
  -> 403; service account holding the capability -> 403; inactive user with
  the capability -> 302 (Django demotes the session to anonymous before the
  decorator runs); all five denied responses contain no owner email, no
  owner name and no reservation UUID.
- admitted: active non-staff with `view_all_reservations` (individual grant)
  -> 200; same capability via an existing `auth.Group` (additive union) ->
  200; active human superuser (Django permission semantics) -> 200.
- denial occurs in the decorator BEFORE the view body, so no protected row
  lookup happens for denied principals (dedicated test plus source review of
  the decorator order).
- non-GET (POST) -> 405 with `Allow: GET`; no POST mutation surface exists.
- Calendar link appears in the All reservations browser only while a valid
  exact-asset filter is selected (test: absent without filter, present with
  `?asset=<id>`), and in the member asset detail only when the template tag
  `has_permission ... "view_all_reservations"` is true (test: absent for
  staff-without-grant, present for the viewer). The tag evaluates the same
  `accounts.authorization.has_reservation_permission` active-human
  predicate the server guard uses (presentation only).
- A read-only viewer has no cross-user mutation action on the page (no
  cancel/release form or link in the template; the detail page reached via a
  chip link is the existing protected detail, still gated, with mutation
  controls only for the corresponding capability).

### 2. Truthful calendar window — PASSED

- Exact asset required: unknown UUID -> 404; non-UUID path segment never
  resolves to the route.
- Bounded GET inputs: `week` missing -> current local week (Monday
  normalized from the viewer-timezone `now`); `week` accepted as any valid
  ISO date (incl. basic form) snapped to its Monday; `2026-13-40`,
  `2026/11/02`, `not-a-date`, datetime strings -> 400 plain message, no
  traceback; anchors beyond ±10 years (2037-01-05, 2016-01-04) -> 400.
  `weeks` exactly `1` or `4` (default 1); `0/2/5/abc/-4/1.5` -> 400.
- Window boundaries are interpreted local wall midnights through the
  existing `reservations.time_utils.interpret_local_wall_time` with
  `fold=0` (first occurrence on ambiguity); a boundary wall time that does
  not exist in the zone -> 400, never a silent fallback. An invalid stored
  profile timezone fails closed to the profile page with a message (test
  with `Not/AZone`), mirroring the member surfaces.
- Query is exactly the ordered half-open aware-time overlap on the exact
  asset: `status__in=[confirmed, released]`, `start_at < window_end`,
  `effective_end_at > window_start`
  (`selectors.reservation_calendar_query`). Focused boundary tests:
  - start exactly at window start -> rendered (inclusive);
  - end (effective) exactly at window end -> rendered only through the
    previous local day ("22:00 - 00:00"), never leaking onto the next
    week's Monday in the 4-week view (half-open end excluded);
  - start exactly at window end -> absent; effective end exactly at window
    start -> absent.
- Rendering: confirmed intervals and released consumed
  `[start_at, effective_end_at)` intervals only (a released row with
  original end 18:00 and effective end 12:00 renders "10:00 - 12:00" and
  never "18:00"); cancelled rows absent from the calendar while still
  present in the All reservations list (same test verifies the history
  list). Overnight "18:30 ->" / "-> 02:00", multi-day "All day" and
  cross-window intervals clipped to the first in-window day are tested.
- DST, viewer profile timezone (Europe/Ljubljana): fall-back week
  2026-10-19 (transition 2026-10-25 01:00 UTC) — an interval crossing the
  transition renders "23:30 ->" (Sat, CEST) and "-> 04:00" (Sun, CET); two
  distinct UTC instants inside the first/second pass of the repeated
  02:00-03:00 wall window render the same wall-clock label
  ("02:15 - 02:30" twice); spring-forward week 2027-03-22 (transition
  2027-03-28 01:00 UTC) — "23:00 ->" / "-> 04:00" and the skipped-wall
  interval "01:30 - 03:30" render correctly; all seven day headings render
  in both weeks. Day assignment follows the VIEWER's timezone: the same UTC
  interval 22:00-01:00 renders "22:00 ->"/"-> 01:00" for a UTC-profile
  viewer and "23:00 ->"/"-> 02:00" for a Europe/Ljubljana viewer. The
  "Times shown in <tz>." banner is present.
- Each chip shows the displayed viewer-timezone interval, the owner's
  display name (email fallback only when the display name is unset; the
  owner email is not disclosed otherwise) and the protected detail link
  (`management-ui:reservation-detail`); released chips carry an explicit
  "Released" badge distinct from confirmed styling, and a legend plus a
  concise calendar-vs-history explanation paragraph are rendered.

### 3. Bounded and usable layout — PASSED

- No new dependency (uv.lock byte-identical to base) and no client-side
  calendar framework: the calendar is a server-rendered Django template
  (`management_ui/reservation_calendar.html`) using only existing SLAIF CSS
  tokens in `web/static/web/site.css` (new `.calendar-*` rules only),
  semantic per-day `<h2>` headings, and plain keyboard-reachable `<a>`
  controls (Playwright asserts every control carries an `href`).
- Desktop: 7-column grid for one week (7 headings) and 4 rows x 7 for four
  weeks (28 headings) with correct window labels ("Mon 19 Oct 2026 -
  Sun 25 Oct 2026" / "Mon 19 Oct 2026 - Sun 15 Nov 2026"); previous/next
  advance the window by its full length and preserve asset + view length;
  "This week" returns to the current local week; switching 1<->4 weeks
  preserves the selected Monday (test: 7 -> 28 -> 7 headings, same chips,
  same first Monday).
- Mobile 390px: deliberate vertical day layout (the week grid collapses to
  block flow; Playwright asserts a single column with strictly increasing
  top offsets) and no document-width horizontal overflow in both views.
- Output cap: `CALENDAR_MAX_INTERVALS = 100`; with 101 qualifying rows the
  page renders exactly 100 chips, states the limit plainly, and links to
  the existing filtered All reservations list carrying `asset=<id>`,
  `from=<window start ISO>` and `to=<window end ISO>` (test follows the
  link and gets 200). All query/output work is limited to the fixed
  selected window and selected asset (single bounded query per request,
  `[:cap+1]` slice).

### 4. Evidence and documentation — PASSED

- Focused Django suite: `tests/test_reservation_calendar.py`, 38 tests,
  command `uv run --env-file .env pytest tests/test_reservation_calendar.py
  -q -p no:cacheprovider --no-cov` against the owned PostgreSQL 17.11
  instance — **38 passed** (matrix, active-human boundary, exact-asset
  isolation, one/four-week navigation/validation, cross-window and
  multi-day intervals, DST/profile timezone, half-open boundary,
  released/cancelled semantics, no POST mutation, bounded output, zero
  writes).
- Chromium: `tests/browser/test_reservation_calendar_browser.py`, 3 tests,
  `uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test
  --browser chromium tests/browser/test_reservation_calendar_browser.py`
  (real HTTP `live_server` + real PostgreSQL) — **3 passed**. Desktop
  1440px and 390px mobile one/four-week flows, asset-detail entry link,
  chip -> protected detail link, previous/next/this-week navigation,
  length switching, released/cancelled rendering, staff-without-grant and
  anonymous privacy denials (no link, 403/login redirect, no owner
  identity), no framework branding, no horizontal overflow.
- Four privacy-safe screenshots captured (synthetic fixture data only; no
  tokens/passwords/verifiers/CSRF/cookies/raw traces/private data):
  `reservation-calendar-1440-1week.png`, `reservation-calendar-1440-4week.png`,
  `reservation-calendar-390-1week.png`, `reservation-calendar-390-4week.png`.
  CODING visually inspected them in two batches of two images: desktop
  views show the 7/28-day grids, correct window labels, confirmed (solid)
  vs released (dashed + badge) chips with owner + times, today highlight,
  wrapped controls; mobile views show the stacked day layout without
  overflow. No visual defect found; no image bundle (each screenshot is a
  single small PNG well under any payload limit).
- Docs updated on the relevant read-only paths only:
  `docs/authorization.md` (new "read-only per-asset calendar" bullet stating
  the grant, GET-only 405, window/bounded-input semantics, confirmed +
  released-consumed rendering, cancelled absence, cap statement, entry
  points, staff-alone exclusion; route inventory now lists 18 `/manage/`
  routes including the calendar row) and `docs/human-ui.md` (Reservations
  bullet: calendar entry points, one/four-week Monday-Sunday weeks in the
  profile timezone, confirmed/release/cancelled meaning). No README ledger
  changes; existing cross-doc anchor
  `authorization.md#management-route-inventory-enforced` still resolves
  (section heading unchanged).

## Verification and negative paths (exact results)

Environment (documented local test tooling, all disposable/owned):
recreated a fresh owned PostgreSQL 17.11 container
(`slaif-054a-pg17`, 127.0.0.1:54330, btree_gist created) because the
pre-existing `.env` target was not running; rebuilt the git-ignored local
uv venv (the prior one was a broken cross-host artifact from a different
machine; git state untouched); bridged the cached Chromium 1243 build as
the revision directory expected by the lock-pinned Playwright 1.60
(`PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers-054a`), because Playwright 1.60
cannot install its own Chromium on this Ubuntu 26.04 host (CI installs its
browsers natively on ubuntu-24.04 and was unaffected).

Local at implementation head `026aea744f0a134d2516a2a5bd1728b3a244adc2`:

- `uv run ruff check .` — PASSED (clean); `uv run ruff format --check .` —
  PASSED.
- `uv run mypy src` (strict) — PASSED (141 source files, no issues).
- `uv run --env-file .env python manage.py check` — PASSED;
  `uv run --env-file .env python manage.py makemigrations --check
  --dry-run` — PASSED (No changes detected: NO new migrations).
- `git diff --check` — PASSED (clean).
- New focused suites: 38 + 3 — PASSED (commands above).
- Relevant existing suites at head:
  `tests/test_management_authorization.py`,
  `tests/test_management_ui.py`, `tests/test_web_human_mvp.py`,
  `tests/test_assets_web_api.py` — 95 PASSED.
- Full local product run (excluding `tests/oap`, which CI runs in its own
  path-gated job): `uv run --env-file .env pytest
  --ds=slaif_reservation.config.settings.test -q -p no:cacheprovider
  --no-cov --ignore=tests/oap` — 1122 passed, 9 skipped, 4 failed. The 9
  skips are the honest pinned-Caddy rehearsal skips (host has Caddy
  v2.11.7, rehearsal requires the pinned v2.11.6); the 4 failures are all
  in `tests/test_restore_drill.py` and are environmental: the host lacks
  `pg_dump`/`pg_restore`, and the identical 4 failures reproduce on
  PRISTINE main `1e469af959ef69e3624390ec591929b84f6c6774` in a temporary
  `git worktree` (worktree removed afterwards). All Caddy-dependent suites
  pass in CI (see below), so no product regression is indicated.
- `uv run pip-audit` — FAILED with exactly the same single finding CI
  reports: `certifi 2026.6.17 PYSEC-2026-4320 (fix 2026.10.19)` on the
  untouched lockfile (see Identity and result).

Remote CI at exact implementation head (observed, not predicted):

- CI run 39508342100 (head `026aea744f0a134d2516a2a5bd1728b3a244adc2`):
  `quality` success, `test` success ("1295 passed, 1 warning in 616.77s
  (0:10:16)" — 1254 prior product/oap count + 41 new tests; the single
  warning is the pre-existing intentional
  `tests/test_product_entry.py:568` DATABASES-override negative test),
  `container` success, `security` FAILURE (pip-audit certifi finding,
  log-verified).
- oap run 39508342116: `oap-harness` success.
- Source-level review performed: the route is GET-only and
  `view_all_reservations`-gated before any asset/reservation lookup; the
  temporal query is the ordered half-open aware-time overlap on the exact
  asset; no model, migration, policy/domain service, token scope/API,
  permission definition, auth, dependency, Docker/Compose/proxy/settings or
  deployment bytes changed (diff limited to the order's allowed paths); no
  unrelated UI redesign (only new `.calendar-*` CSS rules and the two
  ordered entry links).
- Markdown links: no new links introduced; the pre-existing
  `authorization.md#management-route-inventory-enforced` anchor referenced
  from `docs/human-ui.md` still resolves (heading unchanged).

## Uncertainty, dependencies, DHA, limits

- The `security` CI job at the exact head is red solely on the external
  certifi advisory in the unchanged lockfile (evidence above). This is the
  single item blocking an all-green exact-head CI and it is NOT safely
  repairable within this order (lockfile changes are forbidden). Strategy
  owns the next step: a separate bounded dependency-bump order, an explicit
  risk disposition, or a base-level fix before merging PR #112. No human
  adjudication was sought or recorded; the order's DHA section is
  `Decision: NONE` and remains unchanged.
- Report-head CI was not observed at authoring and is not claimed here; it
  is separate from the observed implementation-head CI.
- The 4 local restore-drill failures and 9 local skips are environmental to
  this host (missing pg_dump/pg_restore; Caddy version mismatch) and do not
  occur in CI (test job fully green there).
- Visual qualification used the four captured screenshots inspected in two
  batches of at most two images, per the order; no pixel-diff CI was added
  (not ordered, not stability-proven).
- No real deployment, exposure, DNS/TLS/firewall, private data, lab/Neumann
  or production resource was touched; all evidence is synthetic
  (disposable checkout/container/DB). No merge, auto-merge or
  self-approval was performed; strategy reviews exact head, full diff and
  current required CI, then conditionally merges under existing development
  authority. Real deployment and human milestone judgment remain separate.

## Deferred human adjudication
- Decision: NONE
