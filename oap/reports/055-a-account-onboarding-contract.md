<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "055-a",
  "order_path": "oap/orders/055-a-account-onboarding-contract.md",
  "order_sha256": "0ea29c9078d9d1d9d5c883b54eb05d385b27dc6e6f06e910608620f2a0b752f7",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 114,
  "pr_number": 115,
  "branch": "codex/114-oap-055-a-account-onboarding-contract",
  "implementation_head": "81b68e3f8af435d8af9fc8c07e3865372d811fd2",
  "base_sha": "1eade24e2032b8525d3b0151daaca38830e24d03",
  "result": "PARTIAL",
  "observed_implementation_ci": {
    "observed_head": "81b68e3f8af435d8af9fc8c07e3865372d811fd2",
    "runs": [
      {
        "run_id": 42864895997,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "security": "failure",
          "container": "success",
          "test": "success"
        }
      },
      {
        "run_id": 42864896508,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ],
    "test_job_summary": "1300 passed, 1 warning in 562.44s (0:09:22)",
    "warning": "tests/test_product_entry.py:568 UserWarning: Overriding setting DATABASES can lead to unexpected behavior (pre-existing, intentional DB-unavailable negative test, unrelated)",
    "oap_harness_summary": "CI: Ran 160 tests in 30.907s, OK; local: 159/160 with ambient OAP_ROLE=CODING, 160/160 OK with OAP_ROLE unset (see Uncertainty and limits)",
    "security_failure_root_cause": "CI log: pip-audit 'Found 13 known vulnerabilities in 3 packages' - djangorestframework 3.17.2 (CVE-2026-114136, CVE-2026-114137, CVE-2026-114138; fix 3.18.2), filelock 3.29.4 (CVE-2026-112907, CVE-2026-112909, CVE-2026-112910, CVE-2026-112913, CVE-2026-112915, CVE-2026-112935, CVE-2026-112936, CVE-2026-112939, CVE-2026-112940; fix 4.2.1/4.0.9), msgpack 1.2.1 (CVE-2026-114613; fix 1.2.3). All against the byte-identical base lockfile (git diff base..HEAD -- uv.lock pyproject.toml is empty); reproduced locally with `uv run pip-audit` (same 13 advisories). Base main's last CI run (39520988092 at 1eade24, 2026-10-21) was green before these advisories were published. This order's forbidden_resources bar dependency/lock changes and allowed_paths excludes uv.lock, so the repair is out of scope for this round (precedent: 054-a PARTIAL / 054-b lockfile repair order)"
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 055-a — execution report: selected account-onboarding contract

Implementation head SHA: 81b68e3f8af435d8af9fc8c07e3865372d811fd2
Report publication commit: SELF

## Identity and result

PARTIAL for order 055-a (D0, `Decision: NONE`), a fresh CREATE_OR_RESUME round
(issue #114): before any edit, `git ls-remote` and `gh pr list` showed no
`codex/114*` branch and no PR referencing issue 114, so branch
`codex/114-oap-055-a-account-onboarding-contract` was created from main
`1eade24e2032b8525d3b0151daaca38830e24d03` (verified equal to `origin/main`)
and PR #115 was opened with `Closes #114`. All five order
`source_hashes` were verified SHA-256-byte-identical before the first write
(ARCHITECTURE.md `4566e797b709...`, PLAN.md `8298ef941d02...`,
ARCHITECTURE-for-agents.md `41c32e0b0d64...`,
docs/governance/GROUP-AUTHORIZATION-PROJECTION-REVIEW.md
`dc0085fe0b8c...`, docs/security-model.md `7fcd7abf72a7...`); governance
revision `14fc20b1ff52788974fd3f282322afc9d71362f9` present in history;
foreign PR113 untouched (no read, push or edit). One implementation commit
`81b68e3f8af435d8af9fc8c07e3865372d811fd2` (first parent exactly the base)
changes exactly: `PLAN.md`, `ARCHITECTURE.md`,
`ARCHITECTURE-for-agents.md`,
`docs/governance/ACCOUNT-ONBOARDING-PROJECTION-REVIEW.md` (new),
`oap/orders/055-a-account-onboarding-contract.md` (FINAL, SHA-256
`0ea29c9078d9d1d9d5c883b54eb05d385b27dc6e6f06e910608620f2a0b752f7`) and the
`oap/active` pointer (exact `055-a` + LF, 6 bytes, verified with `od -c`).
No merge, self-approval or auto-merge; no auto-merge enabled.

The PARTIAL result is caused solely by the `security` CI job at the exact
implementation head: pip-audit now reports 13 newly published advisories
against the UNCHANGED locked dependencies (full list and evidence in
metadata `observed_implementation_ci.security_failure_root_cause`). This
order explicitly forbids dependency/lock changes (`forbidden_resources`)
and `uv.lock` is not in `allowed_paths`, so the first failing boundary is
external and out of scope for this round; the analogous 054-a certifi
advisory was resolved by a separate strategy-issued repair order (054-b).
Every in-scope acceptance item below is complete with evidence.

## Numbered acceptance evidence

### 1. Canonical selected meaning (PLAN P-09) — PASSED

`PLAN.md` gained exactly one appended section, P-09 (git diff for the file
is +71/-0, purely append-only at end of file). P-09 records: (a) the exact
three human requirements of the 2026-11-09 message, restated verbatim;
(b) the current contradiction, honestly: no member password-change route
exists (the profile `ProfileForm` edits `display_name`/`timezone` only,
verified at `src/slaif_reservation/web/forms.py`), the Administration
user-page help currently states members cannot change their own password
(`accounts/admin.py` add-form help), and the normal baseline is the standard
validator set including `MinimumLengthValidator` (default minimum 8) at
`config/settings/base.py`; (c) the bounded mitigations (CSPRNG temporary
password, max 24h with no NEW login after expiry, forced first change to
the normal validators, active-only-after-SMTP-acceptance, no
automated ambiguous-send retry with manual rotating reissue, canonical
HTTPS base URL not Host, no plaintext persistence or logged bodies,
production TLS + bounded timeout) and the strongest objection kept visible
(mailbox/relay compromise reduced but not eliminated; not a setup link,
not MFA); (d) the precise deferral narrowing — only admin-created onboarding
email and logged-in own-password change leave the deferral; general OIDC,
public forgotten-password reset, public self-registration and general
notifications remain deferred; (e) the five sequential purposes 055–059
(contract / self-change / SMTP / onboarding / integration+fresh ICA) with
dependencies (056→055; 057→055; 058→056,057; 059→056,057,058), each requiring
its own strategy-issued order, with 056–059 explicitly DRAFT and NO issue,
PR, SHA or result claimed for them; (f) status UNPROVEN, with an explicit
statement that no email/password-reset feature, route, setting or delivery
exists or is claimed as existing. The selection is nowhere described as
real SMTP/identity/deployment authorization.

### 2. Full architecture first (A-17 + SAR-054..SAR-056) — PASSED

`ARCHITECTURE.md` changed only by controlled appends (git diff: intro
temporal bullet added, one edition sentence appended to the existing
edition paragraph, three rows inserted after SAR-053 before A-15, A-17
section appended at end of file; no existing A-01–A-16 section or
SAR-001–SAR-053 row deleted, renumbered or rewritten). The 2026-11-09
temporal bullet and edition sentence state that A-17/SAR-054–SAR-056 are
appended under the controlled-append rule. New stable rows: SAR-054
(logged-in own-password change), SAR-055 (operator SMTP onboarding and
failure boundary), SAR-056 (six-character temporary admin creation and
forced change) — each with Source (attributable human message 2026-11-09,
requirement 1/2/3; A-17), Inspect paths, evidence description, and
`Initial independent-closure classification: **UNPROVEN** (new selected
target)`. A-17 (2026-11-09) defines the acceptance semantics directly:
controlled evolution of the P-04/SAR-036 email/reset deferral (narrowed
ONLY for the two selected behaviors; general OIDC/public reset/
self-registration/general notifications remain deferred), the normal
validator baseline retained with the six-character length admitted only as
a generated temporary credential (never a global weakening), SAR-014/040/
043/044/053 applicability, the historical A-07 "members cannot change
their own password" prose explicitly demoted to baseline context, and an
explicit statement that A-17 infers no broader mail system. All prior
requirements and ICA statements remain historical and untouched.

### 3. Required safety semantics — PASSED (recorded as contract)

Every element of the order's acceptance clause 3 is recorded in root A-17
and in the SAR-054..SAR-056 rows: member change requires current password,
normal validators including the existing minimum, CSRF, active
non-service-account human, current-session continuity and other-session
invalidation, no bearer mutation, no reset/forgotten-password flow (A-17
SAR-054 paragraph + row). The admin add GET prepopulates BOTH controls
with the same new CSPRNG six-character value; only the generated initial
temporary credential receives the narrow length exception, never a global
validator weakening; expiry within 24h with no NEW login after expiry;
successful login restricted to the forced change before any
member/management/Administration/session-API work; existing accounts
unchanged (A-17 SAR-056 paragraph + row). SMTP is explicitly
operator-enabled; disabled/incomplete => no delivery claim and no active
short-password account; enabled add commits the account first inactive
(pending onboarding), sends exactly one login-details email (canonical
configured HTTPS URL, account email identifier, temporary password)
through external SMTP, and activates only after SMTP accepts; failure
stays inactive with a nonsecret status; manual reissue rotates the
previous credential; no automated retry of an ambiguous SMTP send; no
plaintext persistence; no email bodies or credentials in logs; links from
the canonical URL, never the request Host; production-enabled relay
requires TLS and bounded timeout; no queue/Celery/Gateway dependency; no
real relay or recipient contacted in development; human/password
permissions, group grants, API token records and reservation/domain
services remain intact (A-17 SAR-055 paragraph + row). These are contract
statements: nothing is implemented or claimed implemented.

### 4. Projection recomposition and semantic review — PASSED

After the full source was written, `ARCHITECTURE-for-agents.md` was
recomposed: header updated to the 2026-11-09 edition with the actual new
full-source SHA-256 `5ad0ab631696213432c8f513a80b3481fa28a8b0ab89641195ad38725e07db38`
(computed from the post-edit ARCHITECTURE.md bytes, 93251 bytes), the
2026-10-17 identity and the initial projection source hash preserved as
historical provenance; scope line lists A-17; the three new compact
clauses SAR-054/SAR-055/SAR-056 inserted after the SAR-053 clause; a new
`Selected account onboarding target (A-17)` section carrying the executor
obligations and explicit retained exclusions directly, with the
initially-UNPROVEN classification and the fresh-ICA-before-closure rule;
root A-15/A-16/A-17 remain reference-only (no mandatory full-architecture
read for routine CODING). Git diff against the pre-edit projection shows
only the header identity/scope lines changed and new text added; every
pre-existing SAR clause is byte-identical.
`docs/governance/ACCOUNT-ONBOARDING-PROJECTION-REVIEW.md` (new, 13581
bytes committed) maps each H requirement and A-17 facet to requirement ID
and compact clause, lists the strategy-only future D0 decisions, reports
measured context (projection 42676 bytes; routine read set total 57599
bytes, exceeding the archived A-15-era ceilings by 7599 bytes — reported,
not hidden, strategy-owned disposition), and states the method/limitation
that a structural hash alone is not semantic proof.

### 5. Evidence and publication — PARTIAL (doc-only proof PASSED; one CI job FAILED, out of scope)

- **Allowed paths only / no runtime change — PASSED.** `git diff
  1eade24e2032b8525d3b0151daaca38830e24d03 HEAD --stat` shows exactly the
  six allowed paths (4 documents + order + pointer). No file under
  `src/`, `tests/`, settings, migrations, `uv.lock`/`pyproject.toml`,
  Docker/Compose/deploy or runtime was changed; `git diff --check` clean.
  Prior orders, reports, ICA records, CRITICAL and role-law files are
  untouched (verified by working-tree status and diff).
- **Links/anchors — PASSED.** No Markdown link or anchor was added by the
  new text (grep over all changed files: only the pre-existing, unchanged
  links in PLAN.md P-06/P-08); no changed link target exists.
- **Focused OAP harness — PASSED (with one documented host-local
  anomaly).** Local command `python3 -m unittest discover -s tests/oap
  -p 'test_*.py'`: first run 159/160, 1 FAILED
  (`test_ba38_39_tmux_config.Ba39OperationPrereqs.
  test_ba39_strategic_same_prerequisites`, "print-only is always
  allowed"). The identical failure reproduces on a throwaway worktree of
  the UNTOUCHED base main (pre-existing, not caused by this diff); with
  the wrapper's ambient `OAP_ROLE=CODING` unset, the full local harness
  is 160/160 OK (same ambient-role conflict documented in the 054-b
  report). The CI oap-harness job at the implementation head is green
  ("Ran 160 tests in 30.907s — OK").
- **Normal five CI checks at the exact implementation head — 4/5
  SUCCESS, security FAILED (external, out of scope).** Observed at
  implementation head `81b68e3f8af435d8af9fc8c07e3865372d811fd2`
  (CI run 42864895997, oap run 42864896508, all completed before this
  report was authored): quality SUCCESS; test SUCCESS ("1300 passed, 1
  warning in 562.44s"; the single warning is the pre-existing
  `tests/test_product_entry.py:568` DATABASES-override UserWarning from
  the intentional DB-unavailable negative test); container SUCCESS;
  oap-harness SUCCESS; security **FAILED** in 13s at `uv run pip-audit`
  with "Found 13 known vulnerabilities in 3 packages" — djangorestframework
  3.17.2 (CVE-2026-114136/114137/114138, fix 3.18.2), filelock 3.29.4
  (CVE-2026-112907/112909/112910/112913/112915/112935/112936/112939/112940,
  fix 4.2.1/4.0.9), msgpack 1.2.1 (CVE-2026-114613, fix 1.2.3). Root cause
  evidence: `git diff base HEAD -- uv.lock pyproject.toml` is EMPTY
  (lockfile byte-identical to base); local `uv run pip-audit` at this head
  reproduces the same 13 advisories; the last CI on base main
  (run 39520988092 at `1eade24`, 2026-10-21) was green before these
  advisories were published. The failure is therefore a new external
  advisory set on the unchanged lockfile — the same failure class the
  054-a report recorded as PARTIAL (external certifi advisory on the
  unchanged lockfile), which strategy then repaired via the separate
  054-b lockfile order. This order's `forbidden_resources` bars
  dependency/lock changes and its `allowed_paths` exclude `uv.lock`, so
  the repair is a strategy-owned decision (a 055-b correction order or
  bundling the lock repair into the first implementation purpose), not a
  self-assigned fix by this round.
- **PR/report mechanics — PASSED.** PR #115 (open, base main, exact
  branch) was created BEFORE this report with `Closes #114` in the body
  and no actual feature claim; this report is written at the literal
  implementation head; after publication the report commit's first parent
  is the implementation head and changes only this file (to be verified
  with `oap/bin/verify_report.py`; publication checks are recorded in the
  private execution receipt, not in a report rewrite). No merge,
  self-approval or auto-merge occurred.

## Uncertainty and limits

- The pip-audit advisory database is time-dependent: base main was CI-green
  on 2026-10-21 and the same byte-identical lockfile is flagged today. The
  security red is a check failure, not a waiver; it is recorded as FAILED
  and blocks a COMPLETE result, but it is not attributable to this diff
  and is unreproducible-as-passing at any head of this branch without a
  lockfile change this order forbids.
- The local oap-harness single failure is host/ambient-environment only
  (documented above, reproduced on base, and green in CI); the final local
  clean run (160/160 OK with OAP_ROLE unset) supersedes the first.
- No local full product suite run was performed this round: the change is
  documentation-only (zero non-document bytes changed), and the CI test
  job at the exact implementation head ran the full suite green
  (1300 passed) on the changed tree.
- Tokens are UNMEASURED (no qualified tokenizer for the configured model);
  byte figures are exact UTF-8 bytes.
- Report-head CI is NOT YET OBSERVED AT AUTHORING and is not claimed;
  publication verification results belong to the private execution
  receipt. No future push/check success is asserted.
- A-17/SAR-054–SAR-056 remain UNPROVEN selected-target design; nothing
  here is an implementation, release, deployment or ICA claim. A fresh
  exact-revision independent ICA is required before any later
  M-ACCOUNT-ONBOARDING milestone-closure claim.

## Privacy, dependencies and DHA

No credentials, tokens, pepper/verifiers, passwords, Authorization/cookie
material, CSRF tokens, raw request bodies, private exports, physical
locators, auth homes, traces or sidecar artifacts appear in the diff or
this report; no real SMTP account, recipient, relay or credential was
contacted or configured; no production DB, private data, DNS/TLS/firewall,
identity administration or deployment target was touched; foreign PR113
remains untouched. Dependency change: NONE (uv.lock/pyproject.toml
byte-identical to base). DHA: the order declares `Decision: NONE`; no
CRITICAL entry was appended and none was needed; the security-gate
observation above is an evidence record for strategy, not a disposition.
