<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "060-a",
  "order_path": "oap/orders/060-a-onboarding-doc-truth.md",
  "order_sha256": "2c7b8ad68612991f628fd12b1b46ff292550b95e1de81d21562df965ef80b3a9",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 124,
  "pr_number": 125,
  "branch": "codex/124-oap-060-a-onboarding-doc-truth",
  "implementation_head": "78af22514f8257680221f74cecfb6ac1c335d341",
  "base_sha": "50eab07e49fad2a56177ce22d66ec1386546b65b",
  "previous_round": null,
  "pr_mode": "CREATE_OR_RESUME",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "78af22514f8257680221f74cecfb6ac1c335d341",
    "runs": [
      {
        "run_id": 42994156220,
        "workflow": "CI",
        "jobs": {
          "quality": "PASS",
          "test": "PASS",
          "security": "PASS",
          "container": "PASS"
        }
      },
      {
        "run_id": 42994156219,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "PASS"
        }
      }
    ]
  },
  "local_equivalent_checks": "docs-only round: git diff --check clean, all changed relative Markdown targets verified to resolve, untouched operator/canonical docs verified byte-identical to base; no application/runtime/dependency/test/Compose bytes changed, so no local product test run is in scope (see Acceptance 3)",
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 060-a — execution report: clarify current onboarding plan and historical pilot pack

Implementation head SHA: 78af22514f8257680221f74cecfb6ac1c335d341
Report publication commit: SELF

## Identity and result

COMPLETE for order 060-a (D0, `Decision: NONE`), issue #124, PR #125
(CREATE_OR_RESUME, `Closes #124`), branch
`codex/124-oap-060-a-onboarding-doc-truth`, base
`50eab07e49fad2a56177ce22d66ec1386546b65b` (current main). The order file at
`oap/orders/060-a-onboarding-doc-truth.md` (strategy-published bytes, SHA-256
`2c7b8ad68612991f628fd12b1b46ff292550b95e1de81d21562df965ef80b3a9`) and the
`oap/active` pointer (`060-a`) were committed together with the
implementation. All 12 order `source_hashes` were verified SHA-256-byte-
identical at the branch base before the first edit; governance revision
`14fc20b1ff52788974fd3f282322afc9d71362f9` was untouched; no other order,
report, migration or domain file was changed. No merge, no auto-merge, no
self-approval, no CRITICAL append, no DHA.

The branch is a single implementation commit
`78af22514f8257680221f74cecfb6ac1c335d341` on base. No force-push, no history
rewrite, no renumbering.

This objective closes the only in-target findings from the fresh independent
full SAR-001..056 audit at exact main `50eab07e` (54 IMPLEMENTED;
SAR-036/037 PARTIAL; no product-code blocker): current canonical PLAN P-09
and a live-linked historical pilot pack could mislead a reader about the now-
implemented email/password and asset-restriction capabilities. A fresh full-
matrix independent ICA at the exact merged revision after this PR merges
determines whether M-ACCOUNT-ONBOARDING may close; this report is not that
self-certification.

## Numbered acceptance evidence

### 1. P-09 dated truth

- Before (base `50eab07e`, `git show 50eab07e:PLAN.md`):
  - The paragraph headed "**Current contradiction recorded honestly.**"
    opened "Today there is no member password-change route: the profile page
    edits display name and timezone only..." — an unqualified present-tense
    absence claim, false after 056-a.
  - The scope-map paragraph said "Purposes 056–059 are DRAFT here: no issue,
    PR, SHA or result for them exists or is claimed, and none is executable
    until strategy issues its order."
  - The closing paragraph was "**Status.** UNPROVEN. ... nothing is
    implemented by this text. No email/password-reset feature, route,
    setting or delivery exists or is claimed as existing until the
    implementation purposes above land...".
- After (implementation head), exactly three hunks, all inside P-09:
  - The absence observation is relabeled "**Selection-era contradiction,
    recorded honestly.** At the 2026-11-09 target selection there was no
    member password-change route: ..." (past tense, dated to the selection).
    The normal-validator baseline sentence, the "Bounded mitigations
    (selected, not optional)" paragraph, the "Selected target, no
    infrastructure authorization" paragraph and the human-provenance
    paragraph are byte-identical to base.
  - The scope-map paragraph is relabeled "**Development purposes — scope map
    (055–059, as selected).**" and now reads "At that selection, purposes
    056–059 were DRAFT: no issue, PR, SHA or result for them existed or was
    claimed, and none was executable until strategy issued its order." The
    055–059 scope table is byte-identical to base.
  - The stale Status paragraph is replaced with a short durable statement:
    the selected logged-in own-password change (SAR-054, delivered by order
    056-a, issue #116 / PR #117), operator SMTP onboarding with the failure
    boundary (SAR-055, order 057-a, issue #118 / PR #119) and the
    six-character temporary Admin onboarding credential with forced change
    (SAR-056, order 058-a, issue #120 / PR #121) have landed in merged main;
    integration and qualification evidence was published by order 059-a
    (issue #122 / PR #123); exact evidence lives in those merged PRs and in
    `oap/reports/`; a fresh independent ICA at the exact merged revision and
    human acceptance/release/real-infrastructure decisions (including any
    real SMTP relay or deployment) remain separate; no
    M-ACCOUNT-ONBOARDING milestone-closure claim is made.
- Grounding verified against main: PR #117 merged at `2df6341`, PR #119 at
  `77742ba`, PR #121 at `0c4a58e`, PR #123 at `50eab07e` (the base of this
  order). The statement asserts only facts that remain true after this docs-
  only PR merges; it is not a status ledger and does not claim ICA pass,
  milestone closure or real SMTP enablement.
- Re-read of P-09 after edit: the only remaining "no member
  password-change route", "DRAFT" and "no issue, PR, SHA or result" texts are
  each explicitly qualified as 2026-11-09 selection-era facts; the remaining
  "no email bodies or credentials in logs" and "no plaintext persistence"
  texts are selected design constraints (bounded mitigations), not feature-
  absence claims.

### 2. Historical pack boundary

- `docs/runbooks/internal-alpha-pilot-preparation.md`: the first content of
  the file (immediately under the H1, so immediately visible to a reader) is
  now a blockquote banner: "**HISTORICAL / SUPERSEDED — NOT a current
  operator document.**" It states the pack was written at the original
  internal-alpha planning date (created 2026-07-02, first added in commit
  `5adb4cc`, verified via `git log --follow`); that its statements that
  account-creation email, OIDC, password reset, and project, membership, or
  resource-restriction authorization are absent reflect that old planning
  date; that they are **not** current operator instructions; that the pack
  must not be used to configure or operate the current service; and it links
  the current operator truth: `[INSTALL.md](../../INSTALL.md)`,
  `[docs/deployment.md](../deployment.md)`,
  `[docs/authorization.md](../authorization.md)`, and the root
  `[ARCHITECTURE.md](../../ARCHITECTURE.md)` (A-16 and A-17).
- All four changed relative targets resolve at the implementation head
  (INSTALL.md, docs/deployment.md, docs/authorization.md, ARCHITECTURE.md
  exist at those paths); no fragment anchors were introduced, and
  ARCHITECTURE.md at the verified source hash contains A-16/A-17.
- The old body below the banner is byte-identical to base: the file's only
  diff hunk is the 12-line inserted banner (12 insertions, 0 deletions).
- `docs/runbooks/internal-alpha-pilot-readiness.md`: the companion link
  sentence now reads "Use `docs/runbooks/internal-alpha-pilot-preparation.md`
  as a historical planning template for pilot asset selection, operator
  checklists, placeholder-only communication templates, and participant
  limitations; it is superseded and is not the current feature contract. This
  readiness gate remains the pass/fail rehearsal checklist." No other line in
  that file changed.
- Unchanged documents verified byte-identical (SHA-256, base vs
  implementation head): README.md, INSTALL.md, docs/deployment.md,
  docs/authorization.md, docs/README.md, docs/runbooks/README.md,
  ARCHITECTURE.md, CRITICAL.md.

### 3. Evidence / publication

- Docs-only diff: `git diff --name-only 50eab07e..78af225` is exactly
  `PLAN.md`, `docs/runbooks/internal-alpha-pilot-preparation.md`,
  `docs/runbooks/internal-alpha-pilot-readiness.md`,
  `oap/orders/060-a-onboarding-doc-truth.md`, `oap/active`. No application
  source, migration, test, fixture, dependency/lock, Docker/Compose/proxy,
  API, security-setting or OAP helper/workflow byte changed.
- `git diff --check` at the implementation head: clean (no whitespace
  errors).
- Exact-head CI at `78af22514f8257680221f74cecfb6ac1c335d341` (both workflow
  runs' `headSha` verified equal to the implementation head): CI run
  42994156220 (quality PASS 14s, test PASS 11m47s, security PASS 12s,
  container PASS 26s) and oap run 42994156219 (oap-harness PASS 40s) — all
  five checks PASS (see OAP-META `observed_implementation_ci`).
- Publication sequence per CP-05: implementation commit (docs + order file +
  `oap/active` pointer) committed and pushed, PR #125 created with
  `Closes #124` before this report; this report is the only file changed in
  the report commit, whose first parent is the implementation head
  `78af22514f8257680221f74cecfb6ac1c335d341`. No real relay/recipient, no
  identity administration, no deployment; CODING did not merge and no
  auto-merge is enabled.

## Uncertainty and limits

- Report-head CI: the report commit's exact-head checks were not yet
  observed at authoring (it does not exist yet); they run on the identical
  docs-only diff and must be observed before strategic merge review.
- A fresh independent full SAR-001..056 architecture-to-new-main ICA is
  required after merge before any M-ACCOUNT-ONBOARDING milestone-closure
  claim; this documentation change does not self-certify (CP-07).
- The live index links to the preparation pack in `docs/README.md`,
  `docs/runbooks/README.md` and `docs/deployment.md` were left untouched (not
  order-allowed paths); the in-pack banner marks the destination document as
  historical/superseded for every reader following those links. If strategy
  later wants the indexes relabeled, that is a separate order.
- No local product test run was performed because no product code, runtime,
  dependency, test or Compose byte changed; the exact-head CI `test` job
  (full suite, PostgreSQL, browser) is green at the implementation head.

## Deferred human adjudication

- Decision: NONE
