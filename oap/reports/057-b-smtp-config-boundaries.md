<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "057-b",
  "order_path": "oap/orders/057-b-smtp-config-boundaries.md",
  "order_sha256": "9b556896e8402679f71fcf38fa3c5f44c0306ee8809b245150f725cdc46859c3",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 118,
  "pr_number": 119,
  "branch": "codex/118-oap-057-a-external-smtp-config",
  "implementation_head": "c56957dc0f6c7d278cf1175a34d110e921b70034",
  "base_sha": "2df6341d4d89dd45c835e3ac1af67ce076e54346",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "c56957dc0f6c7d278cf1175a34d110e921b70034",
    "runs": [
      {
        "run_id": 42934150882,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "test": "success",
          "security": "success",
          "container": "success"
        }
      },
      {
        "run_id": 42934150878,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ],
    "test_job_summary": "1407 passed, 1 warning in 618.26s (0:10:18)",
    "warning": "tests/test_product_entry.py UserWarning: Overriding setting DATABASES can lead to unexpected behavior (pre-existing, intentional DB-unavailable negative test, unchanged)",
    "oap_harness_summary": "Ran 160 tests in 30.892s - OK"
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 057-b — execution report: close SMTP validation and secret-representation gaps

Implementation head SHA: c56957dc0f6c7d278cf1175a34d110e921b70034
Report publication commit: SELF

## Identity and result

COMPLETE for order 057-b (D0, `Decision: NONE`), an AMEND round reusing
objective 57: issue #118, PR #119, branch
`codex/118-oap-057-a-external-smtp-config`. The 057-a order, its frozen
implementation `cdb3f68978d7650ee34960808c0ff8bfedc74883`, its immutable
report `oap/reports/057-a-external-smtp-config.md` and the 057-a report
publication commit `3b2b20b8e68eea88a0b60ac8bec8beab5d4ee806` are all
untouched (verified: report file byte-identical to the branch base, no edit
in this round; `git diff c56957dc0f6c7d278cf1175a34d110e921b70034^
c56957dc0f6c7d278cf1175a34d110e921b70034 --name-only` lists only the five
allowed non-report paths).

Reconciliation at start: local branch HEAD =
`origin/codex/118-oap-057-a-external-smtp-config` = PR119 head =
`3b2b20b8e68eea88a0b60ac8bec8beab5d4ee806`; `origin/main` =
`2df6341d4d89dd45c835e3ac1af67ce076e54346` = order `base_sha`. `oap/active`
was exactly `057-b\n` (wrapper-placed, committed with this round per the
order's allowed paths); the order file at
`oap/orders/057-b-smtp-config-boundaries.md` is state FINAL with the
strategy-published bytes (SHA-256
`9b556896e8402679f71fcf38fa3c5f44c0306ee8809b245150f725cdc46859c3`). All
three order `source_hashes` were verified SHA-256-byte-identical at the
branch base before the first edit:
`src/slaif_reservation/config/email.py`
`9ea889a991b4f67ecee8ad1b4cad2eb197dcb05b40dbf4f66d61503a8ae4b3fa`,
`src/slaif_reservation/config/env.py`
`6aae85bbe79471813be9f2f7919371ea79e5bb19819a96bf852aacd62739582d`,
`tests/test_account_email_settings.py`
`e271a8d71724036dc58dad3f0d79d0118d54e3907b0ed7a9d897aa5635b4046b`.
Governance revision `14fc20b1ff52788974fd3f282322afc9d71362f9` was not
touched by this round.

## Numbered acceptance evidence

1. **Precondition and gap reproduction (order test 1).** Before any edit,
   all 057-a report-head CI jobs at
   `3b2b20b8e68eea88a0b60ac8bec8beab5d4ee806` were observed terminal: CI run
   42929689709 (quality/test/security/container all success) and oap run
   42929689713 (oap-harness success). A read-only synthetic diagnostic
   (in-process Python, no relay, no network) against the frozen source then
   reproduced all four proven gaps:
   `validate_canonical_service_url('https://@reservation.example.test')`
   ACCEPTED and normalized to the bare host; the resolver ACCEPTED
   `SLAIF_PUBLIC_BASE_URL=' https://reservation.example.test '` and silently
   normalized it; `SLAIF_SMTP_FROM='bad-address'` ACCEPTED; and
   `repr(AccountEmailSettings(...))` contained the synthetic SMTP password.
   PASSED (gaps reproduced exactly as the order's E provenance states).

2. **Acceptance 1 — empty userinfo and base-URL whitespace rejected.**
   `validate_canonical_service_url()` now rejects any userinfo including the
   empty form (`parsed.username is not None or parsed.password is not None
   or "@" in parsed.netloc`); the resolver passes the raw configured
   `SLAIF_PUBLIC_BASE_URL` into canonical validation without stripping
   (missing/empty still yields the safe required-setting error). New direct
   validator negatives: `https://@reservation.example.test` and
   `https://:@reservation.example.test`. New resolver matrix negatives
   (run both in-process and through the real production settings module in
   a subprocess): `base-url-empty-userinfo`, `base-url-surrounding-whitespace`
   and `base-url-trailing-whitespace` (category-only messages
   "must not include userinfo" / "must not include whitespace"; the
   pre-existing required-setting and canonical positive cases are unchanged
   and still pass, with and without port). PASSED.

3. **Acceptance 2 — bare sender validated at enabled settings load.**
   `SLAIF_SMTP_FROM` now must be a valid bare email address: whitespace and
   CRLF/header-injection forms are rejected before validation, then Django's
   `EmailValidator` is applied with `ValidationError` mapped to a
   category-only `ImproperlyConfigured` ("SLAIF_SMTP_FROM must be a valid
   bare email address") that echoes no raw value. New matrix negatives
   `from-malformed` (`bad-address`), `from-surrounding-whitespace` and
   `from-header-injection` (`...@example.test\r\nBCC: ...`) fail closed both
   in-process and in the production-settings subprocess load, with the
   existing category-only no-echo assertions (synthetic password/username/
   sender absent from stderr). The existing valid sender and the synthetic
   loopback SMTP sink tests remain green. PASSED.

4. **Acceptance 3 — SMTP secret excluded from representations.**
   `AccountEmailSettings.host_password` is now
   `field(default=None, repr=False, compare=False)`: the value stays
   attribute-accessible (settings modules map it to `EMAIL_HOST_PASSWORD`
   unchanged — no settings file edited), while `repr`/`str`/equality can no
   longer expose it. New canaries: `test_account_email_settings_repr_and_str_exclude_smtp_secret`
   (synthetic secret absent from `repr()`, `str()` and a rendered failed-
   assertion message) and
   `test_account_email_settings_keeps_secret_attribute_accessible`
   (attribute value preserved; equality not driven by the excluded field).
   No real credential was printed or committed; only the existing synthetic
   test sentinel is used. PASSED.

5. **Acceptance 4 — tests, CI, PR, publication.** Focused suite
   `uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test
   tests/test_account_email_settings.py -q` at
   `c56957dc0f6c7d278cf1175a34d110e921b70034`: **87 passed** (71 prior 057-a
   tests + 16 new). Baseline commands at the same head: `uv sync --locked
   --all-groups` (68 packages, lock untouched), `uv run ruff check .` PASSED,
   `uv run ruff format --check .` PASSED (246 files already formatted),
   `uv run mypy src` PASSED (142 files, no issues), `uv run --env-file .env
   python manage.py check` PASSED (0 issues), `uv run --env-file .env python
   manage.py makemigrations --check --dry-run` PASSED (no changes),
   `uv run pip-audit` PASSED (no known vulnerabilities), `git diff --check`
   PASSED. Full local product suite
   `uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test
   -q`: **1397 passed, 9 skipped, 1 failed** in 776.63s — the single failure
   is `tests/oap/test_ba38_39_tmux_config.py::Ba39OperationPrereqs::test_ba39_strategic_same_prerequisites`,
   a supervision-harness test (separate CI job, pure stdlib) unrelated to
   this change; it was proven pre-existing/environment-bound by running the
   same harness (`python3 -m unittest discover -s tests/oap -p 'test_*.py'`)
   at pristine HEAD `3b2b20b8e68eea88a0b60ac8bec8beab5d4ee806` in a
   disposable `git worktree` (160 tests, the identical single failure,
   worktree removed afterwards). Remote exact-head five checks at
   `c56957dc0f6c7d278cf1175a34d110e921b70034` are all terminal green: CI run
   42934150882 (quality, test, security, container success; test job
   "1407 passed, 1 warning in 618.26s" — +16 vs 057-a's 1391, the warning is
   the pre-existing intentional DB-unavailable negative test) and oap run
   42934150878 (oap-harness success, "Ran 160 tests in 30.892s - OK").
   PR119 required no amendment: it already states the same opt-in SMTP
   transport objective and `Closes #118`, and the correction stays inside
   that description; the branch push updated the PR head to
   `c56957dc0f6c7d278cf1175a34d110e921b70034` (mergeable). No settings
   module, operator docs, dependency, migration, container or prior
   order/report bytes changed. PASSED.

## Changed files (implementation commit)

- `src/slaif_reservation/config/env.py` — reject any URL userinfo
  including the empty form.
- `src/slaif_reservation/config/email.py` — raw (unstripped) base-URL
  validation; bare-email sender validation with category-only error;
  `host_password` excluded from repr/str/comparison.
- `tests/test_account_email_settings.py` — 16 new focused tests (2
  validator negatives, 6 matrix negatives x2 harnesses, 2 repr/str
  canaries) plus scope docstring note.
- `oap/orders/057-b-smtp-config-boundaries.md` — strategy-published order
  bytes (committed per order allowed paths).
- `oap/active` — pointer `057-a` -> `057-b`.

## Privacy, dependencies, DHA and limits

No real SMTP relay, recipient, credential, production DB, host, DNS/TLS or
deployment was touched; all transport evidence is synthetic loopback/in-
process. No secret, token, pepper, verifier, cookie or raw operator value
appears in this report, the diff, or any log; the only password-like value
in scope is the pre-existing synthetic test sentinel already in the repo.
No dependency or lock change. DHA: `Decision: NONE` (no CRITICAL append,
none was ordered). Report-head CI at this publication commit was not yet
observed at authoring and is recorded as such; implementation-head CI is
observed and green as listed. This report does not claim strategic
acceptance, merge, or the next onboarding objective.
