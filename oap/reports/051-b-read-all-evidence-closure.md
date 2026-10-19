<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "051-b",
  "order_path": "oap/orders/051-b-read-all-evidence-closure.md",
  "order_sha256": "84f13270512f7d919a9fb4a9015f27b9c1ad68d7c51e466c54ee272ece2d327c",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 105,
  "pr_number": 106,
  "branch": "codex/105-oap-051-a-read-all-bearer-authority",
  "implementation_head": "c7a51fb0c95b6f497527d95731ec4181a1c69314",
  "base_sha": "3461fa0106c55994a959f88450d4866b018ad890",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "c7a51fb0c95b6f497527d95731ec4181a1c69314",
    "runs": [
      {
        "run_id": 39100248672,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "security": "success",
          "container": "success",
          "test": "success"
        }
      },
      {
        "run_id": 39100248860,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ],
    "test_job_summary": "1243 passed, 1 warning in 595.25s (0:09:55)",
      "warning": "tests/test_product_entry.py:568 UserWarning: Overriding setting DATABASES can lead to unexpected behavior (pre-existing, intentional DB-unavailable negative test, unrelated)",
      "oap_harness_summary": "Ran 160 tests in 30.758s / OK (job success)"
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 051-b — execution report: complete read-all evidence and response contract

Implementation head SHA: c7a51fb0c95b6f497527d95731ec4181a1c69314
Report publication commit: SELF

## Identity and result

COMPLETE for order 051-b (D0) on issue #105 / PR #106 (AMEND) / branch
`codex/105-oap-051-a-read-all-bearer-authority`, base main
`3461fa0106c55994a959f88450d4866b018ad890`. This is the one consolidated
correction round over the frozen 051-a result (implementation
`52045f887a2a5994a9b1d9f757cf8be1d2b32683`, report
`6050a00c5057db63fc9e99e858092687f809738b`, never edited). Single
implementation commit `c7a51fb` (implementation head). The order file
(`oap/orders/051-b-read-all-evidence-closure.md`, state FINAL,
`Decision: NONE`) and the `oap/active` pointer (exact `051-b` + LF) were
committed with the implementation work as the order's allowed paths
require. No merge, no auto-merge, no self-approval.

## Acceptance evidence (order criteria 1–5)

All product evidence was produced against the owned disposable
environment `~/codex-work/slaif-auth-048-922064` (source copy without
`.git` by design, owned PostgreSQL 17 on loopback 22708, owned Chromium
with the Ubuntu24 override). Canonical-repo edits were copied into the
exec copy and parity proven (`diff -rq` clean over `src/`, `tests/`,
`docs/`, `oap/active`, order file) before each test claim.

1. **Early abuse responses meet the published contract** — PASSED.
   Root reproduction confirmed: `AbuseControlMiddleware` answers early
   IP 429/503 BEFORE the new view runs, so the 051-a in-view header
   contract did not hold for those responses. The smallest
   response-header-only change in
   `src/slaif_reservation/config/abuse.py`: when the API request path
   is inside the `/api/v1/all-reservations/` route family, the early
   denial carries `Cache-Control: private, no-store` and a `Vary`
   header containing `Authorization` (same append-never-duplicate
   logic as the in-view `finalize_response`); every other API route and
   the login error page keep exactly `Cache-Control: no-store` with no
   Authorization Vary. Status, body, `Retry-After`, limit keys, rates,
   DB locking, correlation and error privacy are untouched; no limiter,
   auth, proxy or budget behavior changed. Tests added in
   `tests/test_read_all_api.py`:
   `test_early_ip_budget_denials_match_read_all_response_contract`
   (real api_ip budget exhaustion: early 429 on list and valid-UUID
   detail with `private, no-store` + Vary + `Retry-After` + correlation;
   old owner API denial keeps plain `no-store` and no Vary) and
   `test_early_budget_unavailable_503_matches_read_all_response_contract`
   (BudgetUnavailable: early 503 on list and valid-UUID detail with the
   new-route headers, no `Retry-After`; old owner API and login denial
   headers unchanged). In-view 401/403/404/405 and token-budget
   failures remain safe (existing `test_privileged_responses_carry_safe_
   cache_headers`, `test_token_lifecycle_states_still_authenticate_
   closed`, `test_shared_abuse_budgets_still_apply` unchanged and
   green).
2. **Durable real-service lifecycle/negative evidence** — PASSED.
   **Supersession record (explicit, as ordered):** 051-a criterion 6 and
   the 051-a report claimed "real service-produced
   confirmed/released/cancelled bookings" for the blocking-interval
   evidence; that claim was INACCURATE — the 051-a test
   `test_blocking_interval_semantics_per_status` constructed every row
   directly through the ORM. The immutable 051-a report is never edited;
   this order's tests supersede that claim and are recorded as such in
   the test-module docstring. The replaced ORM test is gone; in its
   place, all lifecycle rows are produced by the actual audited
   `create_reservation` / `release_reservation` / `cancel_reservation`
   services with a valid global policy, explicit `book_assets` grants
   and controlled aware instants (`now=` passed explicitly, microsecond-
   zeroed):
   - `test_real_service_lifecycle_blocking_intervals`: upcoming
     confirmed row reports the full original interval; a real mid-
     interval release keeps `end_at` (original end) immutable while
     `effective_end_at`/`released_at` move to the release instant
     (consumed prefix); the consumed prefix still rejects an overlapping
     real creation (`reservation_conflict`) while a real creation
     starting EXACTLY at the effective end succeeds (half-open); a real
     cancellation (with populated reason) yields `blocking_interval:
     null` and the exact same window books again (cancelled never
     blocks); a real completed past row still reports its historical
     interval.
   - `test_history_predating_query_still_overlapping`: `from` excludes
     a past record fully ended before the bound, includes a past record
     whose start predates the bound but still overlaps it, and includes
     a released record whose consumed prefix alone still overlaps the
     bound.
   - `test_history_stays_visible_after_asset_and_account_inactivation`:
     accepted history stays in list and detail after the asset is
     deactivated (per the existing `asset_inactive_not_reservable`
     invariant, with `reservable=False`) and after the owner account is
     set inactive — the active-human restriction applies to the token
     owner, not to history owners.
   - `test_real_service_payload_canaries_list_detail_and_safe_denials`:
     real-service confirmed + cancelled rows with POPULATED canaries
     (purpose, cancellation reason, asset location AND physical
     locator, owner email, display name, external identifier
     `ext-001001`, group name): list and detail render the exact
     allow-list key sets (`ALLOWED_ROW_KEYS`, plus `correlation_id` on
     detail), and NO canary VALUE appears anywhere in the rendered
     list, detail, 403 denial or 404 error body (value-level checks,
     not just field-name absence).
   - `test_group_removal_same_token_additive_grant_retained`: the
     view_all group is removed and the SAME valid token is denied
     (`403 permission_denied`) through the existing unchanged active-
     human helper, while the retained additive grant (booking via the
     other group) still works through the real service AND through the
     bearer creation endpoint (201) with the same token; an individual
     re-grant of view_all restores the same token again.
   Fixtures (`user`/`grant`/`asset`/`bearer`/`auth`/`iso`) were reused
   as-is; two small local helpers (`_policy`, `_book`) were added. No
   broad test refactor.
3. **Current docs say what is implemented** — PASSED.
   `docs/security-model.md` section 6: the false paragraph ("every
   active non-service-account user may ... request any active,
   reservable, exclusive asset" / "Project/group and per-token asset
   restrictions are not implemented" / groups "control administration
   model permissions, not reservation entitlements") is replaced with
   the implemented model: `book_assets` capability + exact-asset group
   eligibility (unrestricted vs restricted, fail closed, only the
   booked asset checked), owner history/lifecycle retained after grant
   loss, explicit management capabilities (link to the management route
   inventory), the read-all dual gate with minimal data, additive group
   + individual grants, and projects/organizational memberships/per-
   token asset scopes still deferred. `docs/api-contract.md`: the
   header no longer defers "resource restrictions" or "API throttling"
   (both implemented; shared abuse budgets and exact-asset group
   eligibility now listed as implemented), the deferred list drops
   "API throttling" and scopes "resource authorization" to beyond
   exact-asset group eligibility + the read-all gate; the read-all
   section states the HTTP verbs accurately (`POST`/`PUT`/`PATCH`/
   `DELETE` refused with 405; standard safe `HEAD`/`OPTIONS` may
   exist); the abuse-limits section notes the read-all route family's
   early denials follow the in-view header contract; `external_
   identifier` `null` now means the consumer cannot infer any machine
   identity and `owner.id` is only an explicit external mapping key,
   never an automatic Linux UID/host-identity fallback (both the
   Representation bullet and the enforcer guidance). No product ledger/
   history prose reintroduced, no historical evidence rewritten.
4. **Actually viewed the changed UI control** — PASSED. Only the two
   screenshot calls changed (`full_page=True` + framing comments; no UI
   redesign). Both relevant Chromium form cases reran at the final
   source state (2 passed, 11.51s). The new captures were ACTUALLY
   VIEWED: at 1440 (default branding, both-capabilities form) the full
   Scopes fieldset is visible including "Read other people's
   reservations (read-only)" with its complete effect line, the
   "Create reservations" effect, the surrounding token-name/lifetime
   fields, nav and footer; at 390 (custom branding, reader form) the
   read_all choice with its effect line is visible, the create option
   is correctly absent for this reader, and no horizontal overflow
   exists (semantic assertions re-ran in-test). MAX TWO safe FORM
   screenshots retained:
   - `browser-artifacts/oap-051-b-retained/token-scope-choices-both-
     1440.png`
   - `browser-artifacts/oap-051-b-retained/token-scope-choices-reader-
     390-custom.png`
   (exec environment, captured at 2026-10-18 ~05:19 UTC before pytest
   output cleanup; both are safe pre-issuance form pages — no plaintext
   token, password, header, CSRF, cookie or raw trace; the 051-a
   retained pair with the cropped framing remains in its own private
   `oap-051-a-retained/` directory, untouched). No additional whole
   browser run.
5. **Exact evidence and frozen publication** — see "Commands and
   results" and "CI observed before authoring". `Closes #105` and PR
   #106 preserved (AMEND on the same branch/issue). No code outside the
   explicit allowance was needed. No merge/self-approve/auto-merge.

## Honest failures and corrections during this round

- First run of `test_history_stays_visible_after_asset_and_account_
  inactivation` FAILED locally: setting only `active=False` on the
  asset violates the existing DB check constraint
  `asset_inactive_not_reservable` (an inactive asset must also be
  non-reservable). This was a TEST SETUP error in the new test, not a
  product defect; the test now sets `active=False` +
  `reservable=False` (same pattern as the pre-existing reservation-
  services suite) and passes.
- 051-a's "real service-produced bookings" lifecycle claim was
  inaccurate (see criterion 2); it is superseded by this round's actual
  service evidence. The immutable 051-a report was not edited.
- 051-a's two retained screenshots cropped out the read_all checkbox;
  the new full-page captures replace that evidence for this round.
- Two E501 line-length and one ruff-format finding in the new code were
  fixed before any test claim; all static checks are green at the
  final head (below).

## Changed files and scope

Single implementation commit `c7a51fb0c95b6f497527d95731ec4181a1c69314`
on top of frozen `6050a00`; 7 files, every one inside the order's
`allowed_paths` (verified against `git show --name-only`):

- `src/slaif_reservation/config/abuse.py` (early-denial headers for the
  read-all route family only)
- `tests/test_read_all_api.py` (2 early-header tests; ORM blocking-
  interval test replaced by 5 real-service tests; local `_policy`/
  `_book` helpers)
- `tests/browser/test_token_scope_authority_browser.py` (two
  screenshot calls: `full_page=True` + framing comments)
- `docs/api-contract.md` (header/deferred claims, verbs, external-
  identifier semantics, abuse-limit header note)
- `docs/security-model.md` (section 6 authorization paragraph)
- `oap/active` (exact `051-b` + LF)
- `oap/orders/051-b-read-all-evidence-closure.md` (committed as ordered)

No model, migration, schema, constraint, unit, lifecycle, policy,
exclusivity, booking-eligibility, audit or idempotency storage change.
No existing token scope backfill/mutation. No `settings/base.py` change
needed (the SPECTACULAR description literal from 051-a already
describes the dual gate). No new dependencies; `uv.lock` untouched. No
other reviewed product file touched.

## Commands and results

Executed in the owned environment (parity proven before each claim):

- `./run.sh run pytest --ds=slaif_reservation.config.settings.test tests/test_read_all_api.py` → PASSED (23 passed)
- Same with `tests/test_abuse_controls.py tests/test_api_v1_reservations.py` → PASSED (53 passed total, final rerun after all fixes)
- `./run-browser.sh run pytest --ds=slaif_reservation.config.settings.test --browser chromium <the two form cases>` → PASSED (2 passed, 11.51s; final run, screenshots retained)
- `./run.sh run ruff check .` → PASSED ("All checks passed!")
- `./run.sh run ruff format --check .` → PASSED (239 files)
- `./run.sh run mypy src` → PASSED ("no issues found in 141 source files")
- `./run.sh run python manage.py check` → PASSED ("0 issues")
- `./run.sh run python manage.py makemigrations --check --dry-run` → PASSED ("No changes detected")
- `./run.sh run python manage.py spectacular --validate --fail-on-warn` → PASSED (exit 0)
- `git diff --check` → PASSED (clean)
- Unchanged third browser case, full pytest, operational/rehearsal/
  HTTPS/Gunicorn/restore sweeps → NOT RUN locally by design; the
  normal full CI at the exact implementation head provides that
  qualification.

Local focused total: 55 passed across the final two commands, 0
failed.

## CI observed before authoring

At the exact implementation head
`c7a51fb0c95b6f497527d95731ec4181a1c69314` (PR #106), all five normal
CI checks observed:

- CI run `39100248672` (workflow `CI`): quality SUCCESS, security
  SUCCESS, container SUCCESS, test SUCCESS. Test job: "1243 passed, 1
  warning in 595.25s (0:09:55)" (up from 1237 at 051-a: +6 tests); the
  single warning is the pre-existing, intentional DB-unavailable
  negative test in `tests/test_product_entry.py` (DATABASES override
  UserWarning, same as observed at 051-a head).
- oap run `39100248860` (workflow `oap`): oap-harness SUCCESS ("Ran
  160 tests in 30.758s").

Report-head CI: NOT YET OBSERVED AT AUTHORING (the report commit is the
last commit of this round; its checks are a normal follow-up, not a
completion claim).

## Security, data, dependencies and local tools

No secrets, tokens, CSRF values, verifiers, peppers, DB URLs, cookies or
Authorization material appear in this report, the commits, the PR, logs
or the retained artifacts. The two retained screenshots are safe
pre-issuance form pages only (viewed; no one-time plaintext token is
shown anywhere). The owned disposable environment (PG17 loopback 22708,
owned Chromium) was reused as instructed; no foreign cleanup, no
production/lab/Neumann contact, no DNS/TLS/firewall/exposure change, no
new dependencies, no runtime configuration change. Ruff/mypy/pytest
were run from the owned `uv` environment only.

## DHA outcome and unresolved gates

Order DHA: `Decision: NONE` — no CRITICAL append was required or made;
`CRITICAL.md` unchanged. No new DHA candidate arose: the header fix
scope (route family only, old routes pinned by tests) is exactly what
the order's strongest-objection mitigation prescribes.

## Limitations and strongest reason against merge

- The early-denial header fix is a string-prefix match on the request
  path (the middleware runs before URL resolution); a hypothetical
  future route under the same prefix would inherit the read-all
  headers. The prefix is the published read-all route family and the
  only routes under it today are the two read-only GET endpoints.
- Full qualification (full pytest incl. browser, operational checks,
  restore drill, container smoke) comes from the normal five exact-head
  CI checks, not local sweeps, as the order requires.
- The A-16 facets remain UNPROVEN until the fresh independent ICA at
  the exact merged revision; strategic review/merge and human release
  remain separate.
- **Strongest reason not to merge:** the shared abuse middleware is
  global; any header behavior introduced there touches every API/login
  denial path. Mitigation as ordered: the change is confined to the
  read-all route family's response headers, old-route responses are
  pinned by new and pre-existing tests, and no budget/auth/proxy
  behavior changed — but strategy may still weigh the shared-file
  blast radius against a header-only discrepancy that leaked no data
  (the original `no-store` was safe).
Recommendation: strategy may proceed to review/acceptance of PR #106 at
implementation head `c7a51fb0c95b6f497527d95731ec4181a1c69314`; no
further coding mutation is made in this round after this report.
