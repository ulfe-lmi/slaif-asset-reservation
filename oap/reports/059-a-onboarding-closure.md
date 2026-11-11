<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "059-a",
  "order_path": "oap/orders/059-a-onboarding-closure.md",
  "order_sha256": "dbeecba7a002b92cae1fd29d18931ad77a4c99627894c0742fa8e92f662e28e1",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 122,
  "pr_number": 123,
  "branch": "codex/122-oap-059-a-onboarding-closure",
  "implementation_head": "c95a7a27e14b5b89137f405ec8dc0fa1435c6154",
  "base_sha": "0c4a58e419005b87585b7621f309ab4f6f704d99",
  "previous_round": null,
  "pr_mode": "CREATE_OR_RESUME",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "c95a7a27e14b5b89137f405ec8dc0fa1435c6154",
    "runs": [
      {
        "run_id": 42985751524,
        "workflow": "CI",
        "jobs": {
          "quality": "PASS",
          "test": "PASS",
          "security": "PASS",
          "container": "PASS"
        }
      },
      {
        "run_id": 42985751535,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "PASS"
        }
      }
    ],
    "earlier_head_note": "First implementation head 0f330b8d421be06b61650dcb3c5d9277267f7dee (CI run 42984720797 / oap run 42984720711) was superseded by the strategic-review corrections commit; the authoritative exact-head CI is at the final head c95a7a27e14b5b89137f405ec8dc0fa1435c6154"
  },
  "local_equivalent_checks": "five CI check groups executed locally where in scope (see Acceptance 4); one environment-bound OAP_ROLE/launcher oap-harness test fails locally and is green in the exact-head oap-harness CI job (see Limits)",
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 059-a — execution report: close account-onboarding ICA blockers

Implementation head SHA: c95a7a27e14b5b89137f405ec8dc0fa1435c6154
Report publication commit: SELF

## Identity and result

COMPLETE for order 059-a (D0, `Decision: NONE`), issue #122, PR #123
(CREATE_OR_RESUME, `Closes #122`), branch
`codex/122-oap-059-a-onboarding-closure`, base
`0c4a58e419005b87585b7621f309ab4f6f704d99` (current main). The order file at
`oap/orders/059-a-onboarding-closure.md` (strategy-published bytes, SHA-256
`dbeecba7a002b92cae1fd29d18931ad77a4c99627894c0742fa8e92f662e28e1`) and the
`oap/active` pointer (`059-a`) were committed together with the
implementation. All 12 order `source_hashes` were verified SHA-256-byte-
identical at the branch base before the first edit; governance revision
`14fc20b1ff52788974fd3f282322afc9d71362f9` was untouched; no other order,
report, migration or domain file was changed. No merge, no auto-merge, no
self-approval, no CRITICAL append, no DHA.

The branch is two implementation commits on base:
`0f330b8d421be06b61650dcb3c5d9277267f7dee` (initial closure) and
`c95a7a27e14b5b89137f405ec8dc0fa1435c6154` (the two mandatory in-scope
corrections directed by strategic review of the first head, comment
6790687507). This report references the FINAL implementation head
`c95a7a27e14b5b89137f405ec8dc0fa1435c6154`. No force-push, no history
rewrite, no renumbering; the first head's CI (42984720797/42984720711) is
superseded by the final head's CI.

The independent ICA against base `0c4a58e` that this objective closes is a
failed historical checkpoint (53 IMPLEMENTED; SAR-036/038/055 PARTIAL; F-01
activation bypass, F-02 stale operator prose). Its private artifact SHA-256
is in the order provenance; the F-01/F-02 evidence is reproduced below and in
the tests. A fresh full-matrix architecture-to-new-main ICA is required after
merge and is not this round's self-certification.

## Numbered acceptance evidence

### 1. Pending-account Admin activation guard (F-01)

- `src/slaif_reservation/accounts/admin.py`:
  - `UserAdmin.get_readonly_fields` adds `is_active` to the read-only set
    while the account is inactive AND pending its first forced change
    (`_activation_locked` = `onboarding.is_pending_onboarding(obj)` and
    `not obj.is_active`). The change form therefore offers NO editable
    `is_active` switch for such an account, so it cannot be made active from
    the form.
  - **Server-side backstop** in `UserAdmin.save_model` (change path): a
    re-read of the persisted `is_active` forces the instance back to inactive
    if a crafted change POST would flip an inactive pending account to
    active. Only that inactive->active transition is prevented; every other
    change is untouched.
  - Activation remains relay-callback-only: the exact-generation
    `onboarding.deliver_onboarding_email` post-commit send is the only path
    that activates; the explicit reissue control is preserved and unchanged.
- `web/templates/admin/accounts/user/change_form.html`: the inactive pending
  block adds a hint stating activation is unavailable from this page (the
  Active control is read-only) and that the account becomes active only when
  the onboarding login-details email is accepted by the configured relay,
  with reissue as the recovery path. No credential is rendered.
- Evidence (owned disposable PostgreSQL, CSRF-valid real Admin HTTP,
  synthetic mail only):
  - `test_zero_accept_add_then_forged_is_active_on_cannot_activate`
    (COMPOSED, the exact audited path): a real Admin Add GET/POST under a
    synthetic zero-accept relay commits the account inactive/pending (one
    send, no retry); a CSRF-valid, manually constructed User change POST
    with `is_active=on` on THAT SAME account leaves it inactive, with the
    stored password hash and pending expiry unchanged, `authenticate` with the
    correct temporary value still refused, and no delivery status claimed by
    either the forged POST or the Add administrator (the Add admin's
    truthful `undelivered` is not flipped to `delivered`). The change GET
    renders `is_active` read-only with the restriction text.
  - `test_change_post_active_pending_deactivate_allowed_reactivate_blocked`:
    an accepted-delivery (active) pending account can be deliberately
    deactivated; once inactive+pending the switch is read-only and a
    CSRF-valid forged `is_active=on` cannot reactivate it (reissue is the
    only path), hash/expiry unchanged, temporary credential refused.
  - `test_change_post_ordinary_account_activation_deactivation_unaffected`:
    a non-onboarding account keeps the editable switch and normal
    permission-checked activate/deactivate (see Acceptance 2).
  - Browser (real Chromium, real HTTP, real PostgreSQL, synthetic relay):
    `test_browser_failed_delivery_activation_locked_ui` — a failed-delivery
    (zero-accept) pending account's change page at desktop 1440 and mobile
    390 shows the state, why activation is unavailable here, the reissue
    path, NO editable `is_active` input, no credential, no horizontal
    overflow and no framework branding (two privacy-safe screenshots).

### 2. Ordinary account operations remain

- Non-onboarding (non-pending) accounts keep the normal editable
  `is_active` switch and permission-checked activation/deactivation:
  `test_change_post_ordinary_account_activation_deactivation_unaffected`
  (activates then deactivates under the existing change permission).
- An accepted-delivery active pending account may still be deactivated
  deliberately (existing behavior), with reissue required to reactivate
  (acceptance-1 backstop; `test_change_post_active_pending_...`).
- The accepted-delivery callback still activates the exact generation;
  failed delivery, reissue rotation, forced first change, 24-hour expiry and
  new-session denial, service-account denial and CLI `createsuperuser` are
  all unchanged and covered by the existing passing tests (44 in
  `tests/test_account_onboarding.py`, 5 in the browser file).

### 3. Current operator prose (F-02)

- `INSTALL.md` (security-boundaries bullet and operating-limits bullet) and
  `docs/deployment.md` (operating-limits paragraph) no longer claim
  password-reset/email workflows are absent. After the strategic-review
  correction the clauses are separated:
  - A logged-in member can change their own password **at any time** (no
    SMTP dependency).
  - The administrator-created onboarding login-details email is available
    **only when the account email transport is configured**.
  - Public forgotten-password reset, institutional OIDC and general
    notifications remain deferred.
- No historical audit/bootstrap rewrite; README was not turned into a
  ledger; no link syntax added (prose rewording only).

### 4. Evidence / publication

- Focused suites (local, owned disposable PostgreSQL, synthetic mail only):
  - `uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test tests/test_account_onboarding.py -q` → 44 PASSED (includes the composed Add->forged-POST regression and the two preservation tests).
  - `uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test tests/test_form_guidance.py -q` → 36 PASSED.
  - `uv run --env-file .env pytest --ds=slaif_reservation.config.settings.test --browser chromium tests/browser/test_account_onboarding_browser.py -q` → 5 PASSED (includes the new activation-locked UI test).
  - Full local product suite (non-browser, non-oap) at the first
    implementation head `0f330b8`: 1210 PASSED, 9 SKIPPED. The final head's
    corrections touch only operator docs and the onboarding unit test, whose
    focused suite is green above; the full suite at the FINAL head is green
    via the exact-head CI `test` job (below).
- Quality gates at the final head: `uv run ruff check .` (All checks passed),
  `uv run ruff format --check .` (all formatted), `uv run mypy src`
  (Success, 146 files), `uv run --env-file .env python manage.py check`
  (0 issues), `... makemigrations --check --dry-run` (No changes detected),
  `uv run pip-audit` (No known vulnerabilities), `git diff --check` clean.
- Exact-head CI at `c95a7a27e14b5b89137f405ec8dc0fa1435c6154`: CI run
  42985751524 (quality PASS, test PASS, security PASS, container PASS) and
  oap run 42985751535 (oap-harness PASS) — all five checks PASS (see OAP-META
  `observed_implementation_ci`).
- Browser review: real Chromium at desktop 1440 and mobile 390 over real
  HTTP for the safe failed-delivery activation-locked surface; exactly two
  privacy-safe screenshots, both free of credentials/secret, no horizontal
  overflow, no framework branding.
- No model/migration, authentication-backend, SMTP-settings/resolver,
  reservation/asset/policy/group/token/API, dependency/lock or
  Docker/Compose/proxy change; `makemigrations --check` clean.
- Publication: implementation + order + pointer committed and pushed to PR
  #123 before this report; this report is the only file changed in the
  report commit, whose first parent is the implementation head
  `c95a7a27e14b5b89137f405ec8dc0fa1435c6154`. No real relay/recipient/
  deployment; CODING did not merge.

## Uncertainty and limits

- `tests/oap/test_ba38_39_tmux_config.py::Ba39OperationPrereqs::test_ba39_strategic_same_prerequisites`
  FAILS in the local environment (stale `__pycache__` from a copied host
  referencing `/home/ubuntu`, plus the OAP launcher/`OAP_ROLE` runtime
  prerequisites of this host). It is environment-bound, unrelated to this
  round's changes (which touch no OAP/launcher code), and the authoritative
  exact-head oap-harness CI job for the final head PASSED (run 42985751535).
- Report-head CI is not observed at authoring; the implementation CI at
  `c95a7a2` above is separate from report-head CI. No future push/check
  success is claimed.
- The two mandatory in-scope corrections (separated operator-doc clauses;
  composed real-zero-accept-Add -> forged-change-POST regression) were
  applied in the second implementation commit `c95a7a2` after the first
  head; this report and the exact-head CI reference the final head.
- The trusted-operator-with-direct-DB-access case is outside the web
  Administration boundary and is not regulated by this objective (order
  provenance C). No D2 crossing; no real SMTP, recipient, identity, data or
  deployment.

