<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "054-b",
  "order_path": "oap/orders/054-b-calendar-review-closure.md",
  "order_sha256": "001c7dc480e01828047dad67774204d0dd52b3fdf247c3aa08d74a78e2e6a2c2",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 111,
  "pr_number": 112,
  "branch": "codex/111-oap-054-a-asset-reservation-calendar",
  "implementation_head": "869089f014c7d71fd1e1223a372555e131dacc18",
  "base_sha": "1e469af959ef69e3624390ec591929b84f6c6774",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "869089f014c7d71fd1e1223a372555e131dacc18",
    "runs": [
      {
        "run_id": 39518206416,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "security": "success",
          "container": "success",
          "test": "success"
        }
      },
      {
        "run_id": 39518206426,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ],
    "test_job_summary": "1300 passed, 1 warning in 613.53s (0:10:13)",
    "warning": "tests/test_product_entry.py:568 UserWarning: Overriding setting DATABASES can lead to unexpected behavior (pre-existing, intentional DB-unavailable negative test, unrelated)",
    "oap_harness_summary": "job success at 2026-10-20T23:57:09Z"
  },
  "prior_054a_implementation_head_ci": {
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
    "security_failure_root_cause": "CI log: 'Found 1 known vulnerability in 1 package / certifi 2026.6.17 PYSEC-2026-4320 2026.10.19' on the unchanged 054-a lockfile"
  },
  "prior_054a_report_head_ci": {
    "observed_head": "820455f333690d8e4c35fbfa4cdd905a331c30d4",
    "runs": [
      {
        "run_id": 39510521516,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "security": "failure",
          "container": "success",
          "test": "success"
        }
      },
      {
        "run_id": 39510521492,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ]
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 054-b — execution report: close calendar review and security gate

Implementation head SHA: 869089f014c7d71fd1e1223a372555e131dacc18
Report publication commit: SELF

## Identity and result

COMPLETE for order 054-b (D0, `Decision: NONE`) as the AMEND round on the
SAME issue #111 / PR #112 / branch
`codex/111-oap-054-a-asset-reservation-calendar` as frozen 054-a, base main
`1e469af959ef69e3624390ec591929b84f6c6774` (verified equal to `origin/main`
before editing; all 8 order `source_hashes` verified as SHA-256 of the
frozen 054-a HEAD blobs: ARCHITECTURE.md, PLAN.md,
ARCHITECTURE-for-agents.md, management_ui views.py,
reservation_calendar.html, test_reservation_calendar.py, uv.lock,
docs/authorization.md; governance revision
`14fc20b1ff52788974fd3f282322afc9d71362f9` present in history; frozen 054-a
implementation `026aea744f0a134d2516a2a5bd1728b3a244adc2` and prior
immutable PARTIAL report `820455f333690d8e4c35fbfa4cdd905a331c30d4`
confirmed as remote branch head and PR #112 head before editing). One
implementation commit `869089f014c7d71fd1e1223a372555e131dacc18` (first
parent the 054-a report commit `820455f333690d8e4c35fbfa4cdd905a331c30d4`)
contains exactly the three calendar corrections, the docs/authorization.md
owner-name and fallback-history correction, the certifi-only uv.lock
upgrade, the order bytes
(`oap/orders/054-b-calendar-review-closure.md`, state FINAL, SHA-256
`001c7dc480e01828047dad67774204d0dd52b3fdf247c3aa08d74a78e2e6a2c2`) and the
`oap/active` pointer (exact `054-b` + LF, 6 bytes, verified with `od -c`).
PR #112 (open, base main, same branch) was amended: its description now
documents the 054-b corrective change set below the 054-a body. No new
issue/PR, no merge, self-approval or auto-merge.

The prior 054-a report-head checks were observed and recorded before any
edit (see metadata `prior_054a_report_head_ci`): quality/test/container
success, oap-harness success, security FAILURE — the red security job is a
failure, not waived; its root cause (certifi 2026.6.17,
PYSEC-2026-4320, fixed in 2026.10.19) is reproduced from the CI job log in
metadata `prior_054a_implementation_head_ci`.

## Numbered acceptance evidence

### 1. Local calendar week label is correct across DST — PASSED

`src/slaif_reservation/management_ui/views.py`: the displayed last day is
now the local date `monday + timedelta(days=7 * weeks - 1)`
(`window_end_date`, already used for the grid), replacing
`(window_end - timedelta(days=1)).astimezone(zone)`. The 24-hour UTC
subtraction mislabelled the spring-forward week: Europe/Ljubljana week
starting Monday 2027-03-22 has a half-open end of 2027-03-29 00:00 CEST
(= 2027-03-28 22:00 UTC); subtracting 24 UTC hours gives 2027-03-27 23:00
CET and the old label "Sat 27 Mar 2027" instead of "Sun 28 Mar 2027".
Query endpoints are unchanged: `window_start`/`window_end` remain aware
instants interpreted from local midnights with fold=0; only the displayed
label uses local date arithmetic. New regression tests (both one-week and
four-week, both DST directions):
`test_window_label_uses_local_date_arithmetic_across_spring_forward`
(one week `Mon 22 Mar 2027 - Sun 28 Mar 2027`; four weeks from 2027-03-08
ending `Sun 04 Apr 2027`, not Friday 2027-04-03) and
`test_window_label_fall_back_week_local_dates` (23-hour fall-back week
`Mon 19 Oct 2026 - Sun 25 Oct 2026`; four weeks ending `Sun 01 Nov 2026`).
Command: `uv run --env-file .env pytest
--ds=slaif_reservation.config.settings.test
tests/test_reservation_calendar.py --no-cov` — PASSED (43 passed, including
these).

### 2. Clipped interval continuation is honest — PASSED

`_calendar_interval_days` now keeps the interval's TRUE last covered local
day (`true_last_day`, with the existing midnight half-open adjustment: a
local-midnight end belongs to the previous day) and computes
`ends_on_day` from it, never from the day clipped to the display window;
when `true_last_day > window_end` the final visible chip renders the
explicit continuation label `All day ->` instead of `-> HH:MM` with the
later end clock time. A day inside the window still gets the true end label
where the end falls (including `-> 00:00` for a true local-midnight end
exactly at the window end, unchanged). New regression tests:
`test_interval_continuing_past_window_shows_continuation` (pre-window start
Sun 2026-11-01 22:00, true end Fri 2026-11-13 06:00: one-week view shows
`All day` Mon–Sat and `All day ->` on Sun 08 Nov with no apparent end time;
four-week view labels the true end `-> 06:00` on Fri 13 Nov and plain
`All day` on Sun 08 Nov);
`test_interval_starting_in_window_and_continuing_past_it` (Fri 06 Nov 10:00
→ Sun 15 Nov 18:00: `10:00 ->` / `All day` / `All day ->` in the one-week
view, true end `-> 18:00` on Sun 15 Nov in the four-week view);
`test_released_consumed_midnight_end_past_window_continues` (released,
consumed until local Tue 2026-11-10 00:00: one-week view ends in
`All day ->`; four-week view shows `-> 00:00` on Mon 09 Nov and NOTHING on
Tue 10 Nov, preserving half-open semantics for the released consumed end).
The confirmed/released/cancelled selector, owner display-name rendering,
detail links and owner privacy are unchanged (existing permission-matrix
tests re-ran green in the same command as item 1 — PASSED, 43 passed).

### 3. Overflow fallback is complete and labelled correctly — PASSED

The capped-window fallback link is now
`/manage/reservations/?asset=<uuid>` — the existing All reservations list
filtered to the exact asset with NO from/to date filters. The old link's
`from`/`to` parameters select by reservation START
(`reservation_queryset`: `start_at__gte` / `start_at__lt`), so a booking
that started before the window and still occupies it was unreachable,
while the wording promised "the complete window". The template now says
"All reservations list for this asset … for the complete asset history,
including intervals that started before this window." (the old "filtered
All reservations list … complete window" text is gone; asserted in the
test). `docs/authorization.md` now states the calendar shows the booking
OWNER's display name (the code renders `owner.display_name or
owner.email`), not "the viewer's display name", and describes the fallback
as the unfiltered asset history; the permission matrix, route inventory
and upgrade instructions are untouched (diff shows only the targeted
paragraph). New regression
`test_output_cap_falls_back_to_complete_asset_history` (replacing
`test_output_cap_is_stated_plainly_with_history_link`): 101 capped released
intervals plus a confirmed pre-window booking (Sun 2026-11-01 23:30 →
Mon 2026-11-02 00:30, one chip on Monday) — the fallback link carries
`asset=` and NEITHER `from=` NOR `to=`; the warning text asserts "complete
asset history" present and "complete window" absent; the fallback page
shows "Page 1 of 3" (102 rows at 50 per page) and the pre-window booking's
UUID is present on the final page, i.e. reachable through the fallback
despite the cap. Command: same focused calendar command as item 1 —
PASSED (43 passed).

### 4. Mandatory security CI repair — PASSED

`uv lock --upgrade-package certifi` (uv 0.12.5 locked resolver, network to
pypi.org) moved certifi 2026.6.17 → 2026.10.19, exactly the PyPA
PYSEC-2026-4320 fix version (official advisory
https://github.com/pypa/advisory-database/blob/main/vulns/certifi/PYSEC-2026-4320.yaml).
`git diff --stat uv.lock`: 3 insertions / 3 deletions — ONLY the certifi
`version`, sdist and wheel entries (new artifacts uploaded
2026-10-20T02:24Z); no other package, no lockfile format change
(version = 1, revision = 3 unchanged), no `pyproject.toml` change.
`uv sync --locked --all-groups`: PASSED (replaced certifi 2026.6.17 with
2026.10.19 in the venv). `uv run pip-audit`: PASSED — "No known
vulnerabilities found", no advisory ignore or waiver. No substantive
resolver side effect (the diff itself is the proof; `requests 2.34.2`'s
unversioned certifi dependency is the only dependent and is unchanged).
CI security job at the new implementation head 869089f: SUCCESS
(2026-10-20T23:56:41Z, CI run 39518206416); container job SUCCESS
(2026-10-20T23:57:01Z).

### 5. Exact evidence and UX — PASSED

Focused Django: `uv run --env-file .env pytest
--ds=slaif_reservation.config.settings.test
tests/test_reservation_calendar.py --no-cov` — PASSED: 43 passed
(37 test functions: the 32 pre-existing 054-a functions, 5 new — 2 DST
window-label and 3 continuation — plus the corrected/renamed
cap-fallback function; parametrized cases included).
Focused Chromium (real HTTP, real PostgreSQL 17, owned disposable
instance at 127.0.0.1:54330): `uv run --env-file .env pytest
--ds=slaif_reservation.config.settings.test --browser chromium
tests/browser/test_reservation_calendar_browser.py --no-cov` — PASSED: 3
passed (desktop 1440 one/four-week flow, mobile 390 vertical layout,
privacy denials). Exactly four privacy-safe screenshots retained in the
owned private path `test-results/` (gitignored):
`reservation-calendar-1440-1week.png`, `reservation-calendar-1440-4week.png`,
`reservation-calendar-390-1week.png`, `reservation-calendar-390-4week.png`;
visually inspected in batches of two (desktop pair, then mobile pair):
window labels correct ("Mon 19 Oct 2026 - Sun 25 Oct 2026" one-week;
"Mon 19 Oct 2026 - Sun 15 Nov 2026" four-week), confirmed/released chips
with owner display name and RELEASED badge, legend, navigation, vertical
mobile day layout without horizontal overflow, SLAIF branding only, no
owner email, no framework text, no credentials/CSRF/tokens visible.
Existing 054-a tests and relevant management/asset checks remain green
inside the full suite below.
Quality battery (all at the implementation tree): `uv run ruff check .`
PASSED ("All checks passed!"); `uv run ruff format --check .` PASSED (242
files formatted); `uv run mypy src` PASSED ("Success: no issues found in
141 source files"); `uv run --env-file .env python manage.py check`
PASSED ("System check identified no issues (0 silenced)");
`uv run --env-file .env python manage.py makemigrations --check --dry-run`
PASSED ("No changes detected"); `git diff --check` PASSED (clean).
Full local suite (owned PG17, sequential): `env -u OAP_ROLE uv run
--env-file .env pytest --ds=slaif_reservation.config.settings.test` —
PASSED: 1291 passed, 9 skipped, 1 warning in 680.51s, exit 0. The 1
warning is the pre-existing intentional DB-unavailable negative-test
UserWarning (tests/test_product_entry.py:568), identical to prior
reports. Two first-run local failures were environmental and are documented
in "Uncertainty and limits" (restored by installing the routine test tool
and by the CI environment respectively); the final clean full run above is
the local record.
CI at the exact implementation head 869089f014c7d71fd1e1223a372555e131dacc18
(observed before authoring this report): quality SUCCESS, security
SUCCESS, container SUCCESS, test SUCCESS (1300 passed, 1 warning in
613.53s), oap-harness SUCCESS (see metadata
`observed_implementation_ci`). CI at this report head is NOT YET OBSERVED
AT AUTHORING and is not claimed; no future check success is asserted.

## Uncertainty and limits

- First local full-suite run (before tooling fix) recorded 1286 passed,
  5 failed, 9 skipped. Both failure groups are environmental, not caused
  by this change: (a) 4× tests/test_restore_drill.py failed with "pg_dump
  is required on PATH" — the host lacked the PostgreSQL client tools that
  the CI test job installs (postgresql-client-17); after installing
  postgresql-client-17 17.11 from the PGDG repository (routine test tool,
  documented here), all 14 restore-drill tests PASS locally; (b)
  1× tests/oap/test_ba38_39_tmux_config.py::test_ba39_strategic_same_prerequisites
  failed because this CODING wrapper's ambient OAP_ROLE=CODING is refused
  as a role conflict by the strategic-launch harness under test — with
  OAP_ROLE unset, all 12 BA-38/39 tests PASS locally, and the test belongs
  to the CI oap-harness job's path-gated domain, which is green at the
  implementation head. The final clean local run (1291 passed, 9 skipped,
  0 failed) supersedes the first run.
- The local host is Ubuntu 26.04; the pinned playwright 1.60.0 (lock
  authoritative) requires chromium revision 1223 (Chrome for Testing
  148.0.7778.96) and its distro map does not cover ubuntu26.04, so
  `playwright install chromium` refuses locally. The official CFT builds
  for that exact revision were installed manually into
  ~/.cache/ms-playwright (chromium-1223 and chromium_headless_shell-1223)
  for the local browser evidence only; CI installs via
  `playwright install --with-deps chromium` on its supported runner and is
  green. No repository dependency or constraint changed.
- Local full-suite counts (1300 total) match the CI test job collection
  (1300 passed on CI; 1291 passed + 9 environment-skipped locally, e.g.
  host-dependent paths), so no test was dropped.
- Report-head CI is unobserved at authoring; publication verification
  results belong to the private execution receipt. The 054-a PARTIAL
  report remains immutable and unrevised. SAR-048..SAR-053 remain
  UNPROVEN until a fresh independent ICA at the exact merged revision;
  nothing here is a release, deployment or ICA claim.

## Privacy, dependencies and DHA

No credentials, tokens, pepper/verifiers, passwords, Authorization/cookie
material, CSRF tokens, raw request bodies, private exports, physical
locators, auth homes, traces or sidecar artifacts appear in the diff, this
report or the retained screenshots (synthetic test identities only:
"Browser Calendar Owner" / "Cal Owner" fixture users, no secrets). The
test database is the owned disposable PostgreSQL 17 container from the
054-a round (127.0.0.1:54330); no foreign Docker resources, production
DB, DNS/TLS/firewall, deployment target or lab/Neumann resource was
touched; no destructive cleanup of unknown volumes. Dependency change is
exactly certifi 2026.6.17 → 2026.10.19 in uv.lock (PYSEC-2026-4320 fix);
pyproject.toml unchanged. DHA: the order declares `Decision: NONE`; no
CRITICAL entry was appended and none was needed.
