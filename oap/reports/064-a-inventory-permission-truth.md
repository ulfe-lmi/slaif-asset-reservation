<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "064-a",
  "order_path": "oap/orders/064-a-inventory-permission-truth.md",
  "order_sha256": "64e359bea3fdb02e4d791bd83a9b014a1576dd96d2a02c01dd1f15d6825c0175",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 133,
  "pr_number": 134,
  "branch": "codex/133-oap-064-a-inventory-permission-truth",
  "implementation_head": "c3c8d1365ea5bdd5e4da7a355c2658de23b16440",
  "base_sha": "d473d767208cb6ef06770f6a8a0b6dba8d17a347",
  "previous_round": null,
  "pr_mode": "CREATE_OR_RESUME",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "c3c8d1365ea5bdd5e4da7a355c2658de23b16440",
    "runs": [
      {
        "run_id": 43022829072,
        "workflow": "CI",
        "jobs": {
          "quality": "PASS",
          "test": "PASS",
          "security": "PASS",
          "container": "PASS"
        }
      },
      {
        "run_id": 43022829142,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "PASS"
        }
      }
    ]
  },
  "local_equivalent_checks": "docs-only round: git diff --check clean at final head, changed paragraph checked in context, zero relative Markdown links in the changed file (nothing to break), scope proven by exact diff name-only listing against base; no application/runtime/dependency/test/Compose bytes changed, so no local product test run is in scope (see Acceptance 2)",
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 064-a — execution report: correct asset API guard name in current form inventory

Implementation head SHA: c3c8d1365ea5bdd5e4da7a355c2658de23b16440
Report publication commit: SELF

## Identity and result

COMPLETE for order 064-a (D0, `Decision: NONE`), issue #133, PR #134
(CREATE_OR_RESUME, `Closes #133`), branch
`codex/133-oap-064-a-inventory-permission-truth`, base
`d473d767208cb6ef06770f6a8a0b6dba8d17a347` (verified equal to origin/main
at start, both local and remote, before the first edit). The order file at
`oap/orders/064-a-inventory-permission-truth.md` (strategy-published bytes,
SHA-256 `64e359bea3fdb02e4d791bd83a9b014a1576dd96d2a02c01dd1f15d6825c0175`)
and the `oap/active` pointer (`064-a` + LF, verified by od) were committed
with the single implementation commit
`c3c8d1365ea5bdd5e4da7a355c2658de23b16440`. All 9 order `source_hashes`
(ARCHITECTURE.md, PLAN.md, CRITICAL.md, docs/audit/ICA-PROTOCOL.md,
docs/ux/form-guidance-inventory.md,
src/slaif_reservation/assets/api.py,
src/slaif_reservation/api/permissions.py, docs/human-ui.md, TESTING.md)
were verified SHA-256-byte-identical at the branch base before the first
edit; governance revision `14fc20b1ff52788974fd3f282322afc9d71362f9` was
untouched; no other order, report, migration or domain file was changed.
No merge, no auto-merge, no self-approval, no CRITICAL append, no DHA.

This objective closes the sole in-target documentation finding of the fresh
independent full SAR-001..056 ICA at exact clean merged main
`d473d767208cb6ef06770f6a8a0b6dba8d17a347` (55 IMPLEMENTED / 1 PARTIAL —
SAR-044; no product-code blocker; exact-main CI runs 43020371985 and
43020371947 five/five SUCCESS). A fresh independent full
SAR-001..056 architecture-to-current-main ICA at the exact merged revision
after this PR merges determines whether M-ACCOUNT-ONBOARDING can close;
this report is not that self-certification and claims no milestone
closure.

## Numbered acceptance evidence

### 1. Asset REST paragraph names the actual guard

- **Correction.** `docs/ux/form-guidance-inventory.md` (asset REST
  paragraph, formerly line 162) now reads "`SessionAuthentication` +
  `IsActiveStaffHuman` (an active non-service-account human staff
  session), with the bearer `assets:read` scope still reserved (no token
  authentication is offered there)". The incorrect `IsAdminUser` is gone:
  `grep -c IsAdminUser docs/ux/form-guidance-inventory.md` returns 0 at the
  head, and the file's only guard mention is the corrected
  `IsActiveStaffHuman` line.
- **Verified against current source.** Both routed views —
  `AssetListAPIView` (lines 48–50) and `AssetDetailAPIView` (lines 72–74)
  in `src/slaif_reservation/assets/api.py` — set
  `authentication_classes = [SessionAuthentication]` and
  `permission_classes = [IsActiveStaffHuman]`; `IsActiveStaffHuman` in
  `src/slaif_reservation/api/permissions.py` admits only
  `is_active_human(user) and bool(user.is_staff)`, i.e. a current active
  non-service-account human staff session. The new sentence names exactly
  that existing gate and nothing more.
- **Semantics preserved.** `SessionAuthentication`, the live
  `/api/v1/assets/` (list) and `/api/v1/assets/<uuid>/` (detail)
  routes, and the reserved, non-working bearer `assets:read` scope are all
  retained verbatim in the paragraph; no text implies tokens can discover
  assets or that the runtime guard changed. The paragraph's rendered-suite
  sentence (anonymous and non-staff get 403, staff session gets the
  inventory JSON) is unchanged in meaning and matches the verified guard.

### 2. Scope and negative paths

- **No other file changed.** Implementation diff against base (name-only):
  exactly `docs/ux/form-guidance-inventory.md`,
  `oap/orders/064-a-inventory-permission-truth.md` and `oap/active`. All
  application source (including `assets/api.py` and
  `api/permissions.py`, byte-identical to base), tests, migrations,
  settings, API schema/behavior, dependencies/uv.lock, Docker/Compose,
  other documentation, OAP helpers/workflows and historical
  audit/order/report bytes are unchanged.
- **`git diff --check`**: clean (exit 0) at the implementation head.
- **Relative Markdown link check**: the changed file contains zero
  Markdown links (0 checked, 0 broken), so the paragraph edit breaks no
  link; the edit is confined to the single paragraph shown above
  (6 lines replaced, no other hunk in the file).
- **No local full product suite**: per the order's test list, this
  one-document correction is evidenced by the paragraph/context/absence
  checks above, the docs-only diff proof and the normal five exact-head
  CI; no local product test run was executed and none is claimed.

### 3. Publication

- PR #134 was opened before this report with `Closes #133` and carries the
  full evidence summary.
- **Five exact-head CI at implementation head
  `c3c8d1365ea5bdd5e4da7a355c2658de23b16440`: PASSED** — CI run
  43022829072: quality pass (17s), test pass (10m36s), security pass
  (12s), container pass (24s), run conclusion success; oap run
  43022829142: oap-harness pass (35s), run conclusion success. Five/five
  SUCCESS, no missing/skipped/cancelled check.
- Publication remote checks (remote head/report bytes/parent/report-only
  diff) are recorded in the private execution receipt, not here.

## Uncertainty, dependencies, DHA and limits

- Report-head CI is NOT YET OBSERVED AT AUTHORING; it is reported
  separately from the observed implementation-head CI above and no future
  check success is claimed.
- This is docs truth only: the strongest objection (overclaiming a
  security change from a one-word docs correction) is addressed directly —
  the live runtime guard was already correct and is byte-identical here;
  this round only names it accurately. No route, guard, test, grant or
  other prose changed; session-only staff admission and the
  reserved/non-working bearer scope semantics are preserved.
- The fresh independent full SAR-001..056 architecture-to-current-main ICA
  at the exact merged revision remains separate and determines milestone
  closure; nothing here claims milestone closure, ICA acceptance, real
  SMTP/deployment or strategic acceptance of this report.
- DHA: NONE. No CRITICAL append; no human disposition requested or
  invented.
