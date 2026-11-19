<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "063-a",
  "order_path": "oap/orders/063-a-developer-reference-truth.md",
  "order_sha256": "6283a723d1bcfc5b82193200d27048c8fe15b29360e0ee643c4eb571d0980cb2",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 131,
  "pr_number": 132,
  "branch": "codex/131-oap-063-a-developer-reference-truth",
  "implementation_head": "bbfd167e231eaee946d07c60a01979a02950c9e2",
  "base_sha": "287b23ba687689d9f7cb947d9a3ec8acb38ff1ab",
  "previous_round": null,
  "pr_mode": "CREATE_OR_RESUME",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "bbfd167e231eaee946d07c60a01979a02950c9e2",
    "runs": [
      {
        "run_id": 43015975910,
        "workflow": "CI",
        "jobs": {
          "quality": "PASS",
          "test": "PASS",
          "security": "PASS",
          "container": "PASS"
        }
      },
      {
        "run_id": 43015975902,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "PASS"
        }
      }
    ]
  },
  "local_equivalent_checks": "docs-only round: git diff --check clean at final head, all changed relative Markdown targets and anchors verified to resolve (incl. ARCHITECTURE.md A-05/A-06/A-16 heading anchors), present-tense absence-language scan of the changed docs clean in context, scope proven by exact diff name-only listing; no application/runtime/dependency/test/Compose bytes changed, so no local product test run is in scope (see Acceptance 3)",
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 063-a — execution report: make linked domain and form-guidance references current

Implementation head SHA: bbfd167e231eaee946d07c60a01979a02950c9e2
Report publication commit: SELF

## Identity and result

COMPLETE for order 063-a (D0, `Decision: NONE`), issue #131, PR #132
(CREATE_OR_RESUME, `Closes #131`), branch
`codex/131-oap-063-a-developer-reference-truth`, base
`287b23ba687689d9f7cb947d9a3ec8acb38ff1ab` (current main, verified equal to
origin/main at start). The order file at
`oap/orders/063-a-developer-reference-truth.md` (strategy-published bytes,
SHA-256 `6283a723d1bcfc5b82193200d27048c8fe15b29360e0ee643c4eb571d0980cb2`)
and the `oap/active` pointer (`063-a`, ID+LF, verified by od) were committed
with the first implementation commit. All 15 order `source_hashes` were
verified SHA-256-byte-identical at the branch base before the first edit;
governance revision `14fc20b1ff52788974fd3f282322afc9d71362f9` was untouched;
no other order, report, migration or domain file was changed. No merge, no
auto-merge, no self-approval, no CRITICAL append, no DHA.

The branch carries two implementation commits on base plus this report-only
child:

- `127a6dac5095ca4273ef8a7a0a226539e5610737` — the original documentation
  repair (four allowed docs + order/pointer bytes);
- `bbfd167e231eaee946d07c60a01979a02950c9e2` — the two mandatory in-scope
  corrections from STRATEGIC's review of the frozen diff (PR #132 review
  comment 6795061361), a new child commit, no amend, no force-push, no
  renumbering.

This objective closes the linked developer-reference truth cluster found by
the fresh independent full SAR-001..056 ICA at exact clean merged main
`50502f2e158d64fb0f16135e0ea187fa44b82589` (52 IMPLEMENTED / 4 PARTIAL; no
code blocker). The CI observed at the superseded head
`127a6dac…` is not relied on; the five exact-head CI below ran at the final
head `bbfd167e…`. A fresh full-matrix independent ICA at the exact merged
revision after this PR merges determines milestone closure; this report is
not that self-certification.

## Numbered acceptance evidence

### 1. Domain-model navigation

- **Banner.** `docs/domain-model.md` now opens immediately under the title
  with a prominent blockquoted **HISTORICAL / SUPERSEDED** banner (added
  063-a, 2026-11-11): it names the unimplemented proposals (the
  `PROJECT`/`MEMBERSHIP` and `AVAILABILITY_RULE` entities, project/group
  policy targeting, the staff-only / no-group assumptions) and carries
  resolved relative links to
  [ARCHITECTURE.md A-05](../ARCHITECTURE.md#a-05-data-ownership-and-lifecycle),
  [A-06](../ARCHITECTURE.md#a-06-transactional-reservation-flows),
  [A-16](../ARCHITECTURE.md#a-16-selected-group-authorization-extension-2026-10-17)
  and [authorization.md](../docs/authorization.md). All four targets/anchors
  were verified to resolve at the head (heading-slug check against
  ARCHITECTURE.md; file-existence check for authorization.md).
- **Body preserved verbatim.** The git diff for the file is purely additive:
  20 insertions (the banner block) and zero deletions or modifications; the
  original `**Status:** design contract…` line and the full ~460-line sketch
  body are byte-identical to the base.
- **Routing.** README.md docs table line "Domain model and time semantics"
  is now "Data model, lifecycle and time semantics (current)" pointing to
  `ARCHITECTURE.md#a-05-data-ownership-and-lifecycle` (A-05 / A-06) with
  `docs/authorization.md` for authorization/booking eligibility; the
  root README no longer links the old sketch. docs/README.md's "Users and
  API clients" entry now routes to the same canonical A-05 / A-06 anchors
  plus `authorization.md`, and the sketch is retained only as a clearly
  labeled "historical/superseded pre-implementation design sketch" entry in
  the "Governance and history" section. First ~100 lines of the README are
  byte-untouched (diff touches only the docs-table line), so the
  product-first structure is preserved and no OAP ledger was introduced.
- Observation (out of allowed paths, unchanged): `docs/discovery-brief.md`
  (an unindexed historical discovery brief, not linked from README or
  docs/README) still mentions `docs/domain-model.md` in prose; per the
  order's scope rule it was not touched and is reported to STRATEGIC for
  disposition, not expanded silently.

### 2. Current form inventory

- **Contradiction 1 fixed (no-self-password-change).** The User add row no
  longer claims "members have no self-service password change — the profile
  page edits display name and timezone only". Section 1 now carries
  source-verified rows for `/profile/`'s change-your-password action and
  `/profile/password/` (route in `web/urls.py`; `MemberPasswordChangeForm`
  in `web/forms.py`): Current password (`id_old_password-help`, bound), New
  password (rendered normal validator list incl. the existing minimum
  length, block-level `id_new_password1-help`, bound), New password
  confirmation (bound), plus the conditional onboarding note and its
  session-gate behavior (`OnboardingForcedChangeMiddleware`, 24-hour
  temporary-credential window).
- **Contradiction 2 fixed (ungranted-staff /manage/).** The verification
  paragraph's "a real staff without individual/group permissions can access
  the management area" is now "…is DENIED the management area — 403 from
  `management_required` before the view body". A section-2 admission note
  states the actual gate: capability-gated `management_required`, dashboard
  admitted on any of the nine management capabilities
  (`MANAGEMENT_PERMISSIONS`, `reservations.book_assets` alone does not
  admit), per-route narrower sets, staff flag alone confers nothing, active
  non-service-account human required. This matches the verified source
  (`management_ui/auth.py`, `accounts/authorization.py`).
- **Source-accurate onboarding rows added.** Admin Add: generated
  six-character temporary password prefilled in BOTH password controls
  (fresh value per GET, `no-store`), the enabled-state inactive-pending
  path (email only after save, activation only on SMTP acceptance, own
  password within 24h) and the account-email-disabled refusal (every
  submission refused, no account created); pending onboarding status block
  with nonsecret delivery-failure warning; reissue route
  (`onboarding-reissue/`, GET confirm + CSRF-checked POST, pending-only,
  change-permission-checked, refused on BOTH GET and POST before any
  mutation while email is disabled); and the inactive-pending `is_active`
  read-only lock with the `save_model` persisted-flag backstop (058-c).
  Every claim was source-checked against `accounts/admin.py`,
  `accounts/forms.py` (`SlaifUserCreationForm`), `accounts/onboarding.py`
  behavior, `web/views.py` and the named tests before being written.
- **Review corrections (final head).** Per PR #132 comment 6795061361:
  section 2 is now "Management surfaces (capability-gated management UI,
  `/manage/`)"; the "Staff cancel reason" / "Staff release" rows are now
  "Management cancel reason" / "Management release" with the cancel-reason
  visibility described as authorized management access; and the
  `test_browser_admin_onboarding_form_guidance` evidence sentence now states
  that the Admin Add page intentionally renders the generated six-character
  credential in both controls (the controlled prefill) and is deliberately
  not screenshotted, while only the later pending status block and reissue
  confirmation page render no credential material — matching the actual
  render-only suite (no `_capture` calls; prefill asserted in both
  controls).
- **Provenance preserved.** The 037/048/049 rows and work-order provenance
  remain in place, with the header noting 063-a (2026-11-11) as the dated
  correction round. No field-help association or browser test is claimed
  that the current source/tests do not support: the verification section
  names only real tests — `test_password_change_page_guidance`,
  `test_admin_user_add_temporary_prefill_guidance`,
  `test_admin_user_change_onboarding_pending_block`,
  `test_admin_user_onboarding_reissue_page_guidance` (all present in
  `tests/test_form_guidance.py`), `test_browser_admin_onboarding_form_guidance`
  (`tests/browser/test_form_guidance_browser.py`), plus the separate
  `test_member_password_change_browser.py` and
  `test_account_onboarding_browser.py` suites.

### 3. Evidence/publication and scope proof

- `git diff --check` at the final head: clean (exit 0).
- Changed-path proof (both implementation commits, name-only, against base):
  exactly `README.md`, `docs/README.md`, `docs/domain-model.md`,
  `docs/ux/form-guidance-inventory.md`,
  `oap/orders/063-a-developer-reference-truth.md` and `oap/active` — all
  within the order's allowed_paths. INSTALL/QUICKSTART/SECURITY/PLAN/
  ARCHITECTURE/CRITICAL/projection/authorization/human-ui/TESTING/runbooks,
  all application source/migrations/tests/fixtures, dependencies/uv.lock,
  Docker/Compose/proxy/settings, API behavior, OAP helpers/workflows and
  historical audit/order/report bytes are unchanged (second commit touched
  only `docs/ux/form-guidance-inventory.md`: 8 insertions, 6 deletions).
- Link/anchor check: every changed relative Markdown target and anchor
  resolves at the final head (re-verified after the review corrections);
  no changed link is broken; pre-existing untouched links were not
  modified.
- Absence-language scan of the changed docs: no present-tense claim
  remains that members lack own-password change, that ungranted staff
  reach `/manage/`, or that the old sketch is the live model; no new
  false readiness or cross-user access claim introduced.
- **Five exact-head CI at final implementation head
  `bbfd167e231eaee946d07c60a01979a02950c9e2`: PASSED** — CI run
  43015975910: quality pass (16s), test pass (11m55s), security pass
  (15s), container pass (21s), run conclusion success; oap run
  43015975902: oap-harness pass (34s), run conclusion success. Five/five
  SUCCESS, no missing/skipped/cancelled check. The earlier runs at the
  superseded head `127a6dac…` (CI 43015283372, oap 43015283451) are not
  relied on.
- No local product test run was executed in this round: the diff is pure
  Markdown in the four allowed docs plus the order/pointer bytes, and the
  order's test list assigns evidence to the link/anchor/absence scans, the
  docs-only diff proof and the normal five exact-head CI, all performed.
  No unrelated local bespoke qualification was added.
- PR #132 was opened before this report with `Closes #131`; publication
  remote checks (remote head/report bytes/parent/report-only diff) are
  recorded in the private execution receipt, not here.

## Uncertainty, dependencies, DHA and limits

- Report-head CI is NOT YET OBSERVED AT AUTHORING; it is reported separately
  from the observed implementation-head CI above and no future check success
  is claimed.
- This is docs truth only: no security/authorization behavior, reservation
  semantics, route, form, migration or test changed. The strongest
  objection (demoting the only domain-model page leaving readers without a
  usable current model guide; a rushed inventory edit claiming untested UI
  help) is addressed by the prominent canonical ARCHITECTURE A-05/A-06/A-16
  and authorization links at every former entry point, source-checked
  targeted rows only, and real-test-named evidence.
- The unindexed `docs/discovery-brief.md` prose mention of
  `docs/domain-model.md` is outside this order's allowed paths and is
  reported to STRATEGIC for disposition.
- The fresh independent full SAR-001..056 architecture-to-current-main ICA
  at the exact merged revision remains separate and determines milestone
  closure; nothing here claims milestone closure, ICA acceptance, real
  SMTP/deployment or strategic acceptance of this report.
- DHA: NONE. No CRITICAL append; no human disposition requested or
  invented.
