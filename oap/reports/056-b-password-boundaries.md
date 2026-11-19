<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "056-b",
  "order_path": "oap/orders/056-b-password-boundaries.md",
  "order_sha256": "d2453879d75f077d46d4dc471ce0a5c11de13e9fbaaba0b7faa7bdbd1d0de2ba",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 116,
  "pr_number": 117,
  "branch": "codex/116-oap-056-a-member-password-change",
  "implementation_head": "aded144c98f1776d8a4263a5d047d02aa451242f",
  "base_sha": "bfc6efd2beeeeebe9df794cdbfc0e93b38ddfff0",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "aded144c98f1776d8a4263a5d047d02aa451242f",
    "runs": [
      {
        "run_id": 42914772023,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "test": "success",
          "security": "success",
          "container": "success"
        }
      },
      {
        "run_id": 42914772047,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ],
    "test_job_summary": "1320 passed, 1 warning in 534.07s (0:08:54)",
    "warning": "tests/test_product_entry.py:568 UserWarning: Overriding setting DATABASES can lead to unexpected behavior (pre-existing, intentional DB-unavailable negative test, unrelated)",
    "oap_harness_summary": "Ran 160 tests in 28.671s - OK"
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 056-b — execution report: member password-change security boundaries

Implementation head SHA: aded144c98f1776d8a4263a5d047d02aa451242f
Report publication commit: SELF

## Identity and result

COMPLETE for order 056-b (D0, `Decision: NONE`), the single consolidated corrective
suffix (AMEND) of the same objective: same issue #116 / PR #117 / branch
`codex/116-oap-056-a-member-password-change`, reusing the PR opened by 056-a. Before
the first write, all five order `source_hashes` were verified SHA-256-byte-identical
against the frozen 056-a report head
`4457e9e5b6ca1f5f26fb624e4626bb0ab95f96bf` (= `origin/<branch>` at start):
web/views.py `e4d5faa3...`, tests/test_member_password_change.py `5c67af1f...`,
web/forms.py `f64c4f8f...`, templates/web/password_change.html `148d712a...`,
docs/security-model.md `3c62587f...`. `oap/active` was exactly `056-b\n`; the order
file bytes are the strategy-published FINAL bytes (SHA-256
`d2453879d75f077d46d4dc471ce0a5c11de13e9fbaaba0b7faa7bdbd1d0de2ba`). Base
`bfc6efd2beeeeebe9df794cdbfc0e93b38ddfff0` equals `origin/main` at start; governance
revision `14fc20b1ff52788974fd3f282322afc9d71362f9` is in main's history. All five
056-a report-head (`4457e9e5...`) jobs were observed terminal and green before
activation: CI run 42903756587 (test/quality/container/security success) and oap run
42903756585 (oap-harness success); the 056-a order and report were left
byte-identical and unmodified.

The single implementation commit `aded144c98f1776d8a4263a5d047d02aa451242f` (first
parent exactly the 056-a report commit `4457e9e5b6ca1f5f26fb624e4626bb0ab95f96bf`)
changes exactly the ordered non-report paths:
`src/slaif_reservation/web/views.py`, `tests/test_member_password_change.py`,
`oap/active`, `oap/orders/056-b-password-boundaries.md`. No other product, doc,
form, template, admin, model, migration, settings, dependency, lock, proxy, CI or
governance file changed; the foreign PR113 was not touched.

## Numbered acceptance evidence

1. **Sensitive POST marking with negative evidence.** The member
   `password_change` view is now decorated, outermost, with
   `@sensitive_post_parameters("old_password", "new_password1", "new_password2")`,
   preserving `@active_human_required`, `@sensitive_variables("form")` and the
   existing safe request logger; form validation, CSRF, the current-session hash
   update and the active-human gate are unchanged. New focused failure-path test
   `test_submitted_credentials_are_redacted_from_exception_report` POSTs synthetic
   canary credentials through the decorated view (wrong current password, no DB
   change), asserts the request marks exactly the three submitted credential
   fields, then renders the REAL Django technical 500 report for that request
   under `DEBUG=False` (production `SafeExceptionReporterFilter`) and asserts no
   canary value appears anywhere in the report while the cleansed substitute is
   present. The canaries never appear in test output or assertion diagnostics
   (values compared via `request.POST`; failure messages name fields only).
   Negative control: with the decorator temporarily removed the same test FAILS
   (marking attribute absent), then the file was restored byte-identical. PASSED
   (real PostgreSQL17 test DB). This makes the implementation match
   `docs/security-model.md` ("submitted values are excluded from
   request/exception logging"), which is now literally true for technical
   exception reporting; no doc change was needed or made.
2. **GET/POST-only methods.** PUT/PATCH/DELETE for an admitted member now return
   `405` with `Allow: GET, POST` before any form creation;
   `test_unsupported_methods_are_rejected_without_change[put|patch|delete]`
   verifies status, Allow header and byte-identical stored hash for all three
   methods. Anonymous/inactive/service-account behavior stays under the existing
   `active_human_required` guard (their denials are unchanged and re-passed);
   the route remains a browser form only. PASSED.
3. **Real bearer denial.** `test_bearer_only_request_is_denied` now sends the
   actual opaque `issue_api_token(...).bearer_token` string (056-a stringified
   the `ApiToken` model object, so it had only proved invalid-bearer denial).
   With a valid `reservations:read` token and no session, GET and POST are both
   302-denied to login and the stored password is unchanged (new assertion). No
   bearer authentication backend, scope or endpoint was added; the bearer canary
   is used only in the request header and never printed, logged or asserted by
   value (`ApiTokenIssueResult.bearer_token` carries `repr=False`). PASSED.
4. **Focused suites, five CI jobs, publication.** Focused member suite now 18
   tests, all PASSED (14 carried over re-passed); focused browser test
   `test_browser_member_password_change[chromium]` re-passed explicitly
   (real Chromium/HTTP/PostgreSQL, unchanged UI bytes, so the 056-a local
   screenshots remain valid by byte identity). Full local product suite (real
   PostgreSQL17, real Chromium): 1310 passed, 9 skipped, 1 failed in 641.89s —
   the 9 skips are the pre-existing HTTPS-boundary rehearsal prerequisite skips
   (identical count to the 056-a local run; prerequisites absent on this host,
   none faked) and the single failure is the pre-existing local-environment oap
   harness test
   `tests/oap/test_ba38_39_tmux_config.py::Ba39OperationPrereqs::test_ba39_strategic_same_prerequisites`,
   which fails identically on an unmodified checkout of the 056-a report head
   `4457e9e5...` on this host (verified in a throwaway worktree) and is untouched
   by this diff; it is the same failure already documented in the 056-a report.
   Normal five CI jobs at the exact implementation head
   `aded144c98f1776d8a4263a5d047d02aa451242f`: quality success (14s), test
   success (9m58s; "1320 passed, 1 warning in 534.07s (0:08:54)"; the warning is
   the pre-existing intentional DATABASES-override negative in
   test_product_entry.py:568), security success (13s), container success (21s;
   UID:GID 10001:10001, static/bootstrap files present), oap-harness success
   (160/160 OK) — runs 42914772023 (CI) and 42914772047 (oap), all observed
   terminal at authoring. PR #117 amended (description and title now cover
   056-a and 056-b; `Closes #116` retained). Publication: this report file is
   the only change in the report-only commit, whose first parent is the
   implementation head. CODING does not merge, self-approve or enable
   auto-merge.

## Local exact-head runs (evidence index, not CI)

- `uv sync --locked --all-groups` PASSED; `uv run ruff check .` PASSED;
  `uv run ruff format --check .` PASSED (244 files); `uv run mypy src` PASSED
  (141 files, strict); `git diff --check` PASSED.
- `uv run --env-file .env python manage.py check` PASSED (0 issues);
  `uv run --env-file .env python manage.py makemigrations --check --dry-run`
  PASSED (no changes).
- `uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test
  tests/test_member_password_change.py` → 18 passed (real PostgreSQL17 test DB).
- `uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test
  tests/browser/test_member_password_change_browser.py --browser chromium` →
  1 passed (real Chromium/HTTP/PostgreSQL, 1440/390).
- Full local `uv run --env-file .env pytest` at the implementation head:
  1310 passed, 9 skipped, 1 failed in 641.89s (see acceptance 4 for the
  pre-existing, already-documented explanations of the skip/fail sets).
- `uv run pip-audit` → "No known vulnerabilities found"; production-settings
  import fail-closed negative confirmed (nonzero exit, as CI expects).
- `docker compose config` PASSED; `docker build` PASSED with image user
  `10001:10001` and all five CI static/data file existence checks PASSED
  (container files unchanged by this diff).
- OpenAPI: `manage.py spectacular --file build/openapi/schema.yaml
  --validate --fail-on-warn` PASSED; generated schema SHA-256
  `ac17d86cafac24e59618b232670d1e381b26f7e8523f3e8ec463d4f106a2becd` is
  byte-identical to a pristine main (`bfc6efd2...`) generation (no API surface
  change).

## Uncertainty, limits and notes

- Report-head CI (the publication commit) is NOT YET OBSERVED AT AUTHORING; it
  is tracked separately and never folded into the implementation-head CI above.
- The one local oap-harness failure is host-environment-specific (strategic
  launcher `--print-only` prerequisite check); it is pre-existing at the 056-a
  head on this host, outside this diff, and the CI oap-harness job at the exact
  implementation head (160/160 OK) is the authoritative observation.
- No DHA: the order declares `Decision: NONE`; no CRITICAL entry was appended or
  needed.
- This round does not merge, self-approve, enable auto-merge, or claim strategic
  acceptance; merge remains with strategy after review of this report head.
