<!-- OAP-META
{
  "kind": "report",
  "id": "049-b",
  "order_path": "oap/orders/049-b-booking-eligibility-corrections.md",
  "order_sha256": "3e4547a1423326a03114d5dd7930c75aec0043413074516dd008b6ae8506edc7",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 101,
  "pr_number": 102,
  "branch": "codex/101-oap-049-a-booking-eligibility",
  "implementation_head": "464445146f7dc2c110079df6d1dab87645c72881",
  "base_sha": "12947e9b368445eeb4a48416421626224b49f4dc",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "464445146f7dc2c110079df6d1dab87645c72881",
    "runs": [
      {
        "run_id": 39077442644,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "security": "success",
          "container": "success",
          "test": "success"
        }
      },
      {
        "run_id": 39077442645,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ],
    "test_job_summary": "1185 passed, 1 warning in 481.45s (0:08:01)",
    "warning": "tests/test_product_entry.py:558 UserWarning: Overriding setting DATABASES can lead to unexpected behavior. (pre-existing, unrelated)",
    "superseded_observation": {
      "run_id": 39076632805,
      "workflow": "CI",
      "observed_head": "fcdf3e8152d45cc2856c3a1563791d744d9bf2e3",
      "jobs": {
        "quality": "failure (ruff format --check on one reformatted test line only)",
        "security": "success",
        "container": "success",
        "test": "success (1185 passed, 1 warning in 571.14s, incl. real restore drill round trip)"
      },
      "note": "Repaired by the format-only follow-up commit 464445146f7dc2c110079df6d1dab87645c72881; the full suite was re-observed green at that exact head (runs above). No behavioral change in the repair."
    }
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 049-b — complete booking-eligibility compatibility and required negative evidence

Implementation head SHA: 464445146f7dc2c110079df6d1dab87645c72881
Report publication commit: SELF

COMPLETE for the 049-b correction round on the 049-a A16/SAR-049
booking-eligibility slice (D0). Same objective (issue 101), same branch
`codex/101-oap-049-a-booking-eligibility`, amended into the existing PR #102
(body carries `Closes #101`). Base main remains
`12947e9b368445eeb4a48416421626224b49f4dc`; work started from the exact
frozen 049-a report commit `6d08d99ddf724db1eb437dff7c028e8ab7223786`
(first parent verified as the 049-a implementation head
`5fb13875f90c00bd222125856fb5e1f1f13d2350`). The shared booking predicate,
reservation service/API gates, legacy planner+apply, all models and all
migrations are byte-identical to the 049-a implementation head (verified by
git object-id comparison: `assets/authorization.py`,
`accounts/authorization.py`, `reservations/services.py`,
`api/reservation_views.py`, `legacy_import/planner.py`,
`legacy_import/importer.py`, `assets/models.py`, `reservations/models.py`,
`accounts/models.py` IDENTICAL; assets/accounts/reservations migration
directories unchanged). The only source edits are the two order-authorized
ones: the restore-probe principal/asset selection and the web
denial-reason selection. No merge, no auto-merge, no CRITICAL mutation, no
deployment, no real DB/data/exposure operation.

## Provenance / order verification

- `oap/active` contains exactly `049-b` + LF; the order file
  `oap/orders/049-b-booking-eligibility-corrections.md` (state FINAL,
  pr_mode AMEND, pr_number 102, issue 101, base 12947e9) is byte-identical
  to the strategy workorder copy (sha256
  `3e4547a1423326a03114d5dd7930c75aec0043413074516dd008b6ae8506edc7`).
- Local HEAD at start was exactly `6d08d99` (the 049-a report commit,
  first parent `5fb1387`), branch in sync with origin; PR 102 OPEN at that
  head with no auto-merge. Base `12947e9` equals `origin/main`.
- The order's `source_hashes` are strategy-side canonical bindings: none of
  them are reproducible from this coding checkout or from this repository's
  git objects (same pattern as the 049-a order, whose frozen state strategy
  itself validated and fixed as the mandatory start for this round). The
  binding start state — the exact 049-a report commit — is verified and is
  what this round used. Recorded as a provenance observation, not a
  blocker, consistent with the 049-a round.
- Decision: NONE (D0); no DHA append performed.

## Acceptance evidence (order items 1-9)

All local test runs used the owned isolated environment
`~/codex-work/slaif-auth-048-922064` (source copy, pinned uv 0.11.23,
Python 3.13, owned Chromium with `PLAYWRIGHT_HOST_PLATFORM_OVERRIDE`,
PostgreSQL 17 container CID `7680db038ecebff114a19a929c6b2e3800d7274b23254a41707c2873d7c4067d`,
name `slaif-auth-048-922064`, loopback 22708 — validated against the order
before reuse). Suites ran sequentially; `OAP_ROLE` unset for the OAP
harness. No host packages installed; no foreign resource touched.

1. **Legacy positive fixture.** PASSED (local + CI).
   `tests/test_legacy_import.py::test_apply_revalidates_missing_future_policy_inside_transaction`
   now grants the mapped future-appointment user the explicit real
   `reservations.book_assets` permission BEFORE plan creation (the only
   change in that file); the stale (deactivated) global policy is still
   rejected at APPLY with `policy_not_configured == 1` and zero
   reservations/provenance/success audit. Planner and apply authorization
   checks are byte-identical to 049-a (no weakening). The completed-past
   no-grant historical exception tests
   (`test_apply_past_completed_still_imported_without_grant`,
   `test_planner_past_completed_exception_preserved`) were preserved and
   pass (2 passed locally). Local file result: 33 passed in 7.15s; CI
   test job green (see below).
2. **Restore probe compatibility.** PASSED (local direct + CI real
   round trip). `restore_drill.py::_create_probe_reservation` now selects
   the probe principal and asset TOGETHER: the first (user, asset) pair in
   stable id order in which a current active non-service-account human
   passes the SAME shared `user_can_book_asset` predicate for an
   active/reservable/exclusive asset with a resolvable effective policy.
   `create_reservation` remains the authority (unchanged
   PROBE_WINDOWS/policy/time/audit/error handling); the drill never grants
   permissions or changes asset ACLs; with no eligible pair it raises a
   clear, credential-free CommandError before any probe write. Module
   docstring updated to state the eligible user/asset-pair prerequisite.
   Deterministic direct probe tests (new `RestoreDrillProbeSelection`
   class, explicit UUIDs for stable id order): first user without the
   booking grant is skipped in favor of the later eligible user (nothing
   granted); incompatible restricted pair (capability present, allowed
   group absent) is skipped and the later member books the same asset; a
   no-eligible-pair source fails with no reservation/audit/grant/ACL
   change; no-active-human and no-qualifying-asset refusals preserved.
   Local: 5 passed in 4.71s (direct tests only — the host has no
   pg_dump/pg_restore, an environmental fact unchanged since 049-a; no host
   tools were installed). The full real round trip
   (`RestoreDrillRoundTrip`, now deterministically eligible) and all
   destructive safety guards (`RestoreDrillNegatives`, incl. the
   pg-tool-dependent refusals) ran and PASSED in the CI test job at the
   implementation head (1185 passed).
3. **Required negative evidence.** PASSED (local + CI), in
   `tests/test_booking_authorization.py` (57 passed in 12.28s locally):
   - `test_no_parent_inheritance_either_direction` (both directions) now
     uses `direct_booker` (holds `book_assets`, NOT a member of group_a):
     restricted parent denied / unrestricted child allowed, and
     unrestricted parent allowed / restricted child denied — the denial
     branch is actually reached; an eligible-member positive control books
     the restricted asset in a non-conflicting window.
   - New `test_last_allowed_group_deletion_denies_new_keeps_existing`:
     real `Group.delete()` of the only allowed group (not an M2M clear)
     leaves `booking_restricted=True` with an empty list; new creation is
     denied with `booking_not_authorized`; the accepted booking remains
     confirmed and unchanged.
   - Three new bearer tests with valid unchanged tokens: (a) removing the
     group that carries `book_assets`, (b) removing only the
     asset-allowed membership while retaining `book_assets`, (c) removing
     the group from the asset allow-list. Each proves NEW and cached
     create POSTs return 403 `booking_not_authorized` (no replay header,
     no second reservation/audit), and that restoring access replays the
     ORIGINAL status/body/correlation (X-Request-ID equality,
     `X-Idempotent-Replay: true`) without another reservation or creation
     audit. The existing direct-grant revocation case
     (`test_api_authorization_rechecked_before_cached_replay`) is
     preserved.
   - `test_owner_retains_lifecycle_after_losing_capability_and_membership`
     now also exercises the BEARER routes after exact-asset eligibility
     loss: owner list (200), detail (200), cancel (200, upcoming record)
     and RELEASE (200, active record; `released_at` set,
     `effective_end_at == released_at`) — including bearer release, which
     the 049-a owner-only test never exercised.
   - `test_service_denies_inactive_and_service_accounts` pins the
     superuser variants: an inactive superuser is denied
     (`principal_inactive`) and a service-account superuser is denied
     (`booking_not_authorized`) — not only ordinary service accounts.
   - No individual-permission/global autouse/default-manager bypass was
     introduced; no cross-user scope/mutation work.
4. **Truthful browser refusal.** PASSED (local + CI).
   `web/views.py` adds `_reserve_denial_reason(asset, state)` used by the
   direct reserve GET redirect and POST form error: the principal's
   current booking state is reported first (capability, then
   allowed-group mismatch, mirroring the service order), and only for an
   otherwise-eligible member is the asset-side state stated
   ("This asset is not reservable." / "This asset cannot be reserved
   through this page."). The asset active/reservable rules, filters,
   availability privacy and owner lifecycle are unchanged. New
   `test_browser_denial_reason_is_truthful_for_nonreservable_asset`
   asserts, for an otherwise-eligible member on a non-reservable asset:
   GET redirects with "This asset is not reservable." (no false group
   message), forged POST renders the same truthful reason, zero
   reservations/audit; for a no-capability member the truthful
   user-state reason is stated. Existing negative authorization tests
   preserved (their expectations are unchanged by the fix).
5. **Real upgrade idempotence evidence.** PASSED (local + CI).
   `tests/test_booking_access_upgrade.py` materializes the `before`
   snapshot (`list(...)`) BEFORE the repeated `migrate`, and first applies
   a deliberately operator-configured restriction (`booking_restricted`
   + one allowed group on the populated legacy GPU asset); after the
   re-run the snapshot comparison is real and the configured
   restriction/allowed-group list is asserted to survive. All existing
   populated-row preservation and default-unrestricted checks are
   unchanged. New migration/model bytes unchanged (verified identical to
   049-a). Local: 1 passed in 5.40s.
6. **Current documentation.** DONE (affected text only):
   - INSTALL.md: deliberate `reservations.book_assets` assignment guidance
     (operator group or individual permission; restricted-asset allowed
     group membership; no auto-enrolment; superuser meets the global
     capability via Django semantics but still needs an allowed group)
     now sits next to ordinary-account creation in the required step 9
     completion path, not only in the late limitations section; the
     round-number migration narration ("in the 048 migration") is removed
     from normal wording.
   - docs/authorization.md: the helper bullet no longer claims "wires no
     endpoint or service enforcement yet" (it is the foundation of the
     active booking-eligibility enforcement); the planned list no longer
     names "booking behavior" as a planned change (it already carries the
     active gate; management/read-all remain planned, stated as such).
   - docs/authorization.md backup/reverse limits: the new asset ACL
     fields/list are ordinary backed-up database state; dropping/reverting
     that migration deletes that configuration and a code rollback does
     not restore it.
   - docs/runbooks/backup-and-restore.md: the restore probe's eligible
     user/asset-pair prerequisite is documented (capability + exact-asset
     membership; shared-predicate selection; never grants; fails before
     any probe write). Compose project names/topology and existing backup
     instructions untouched; README/history/governance untouched; no new
     ADR.
   - Changed-doc relative link check: 14/14 targets exist.
7. **Focused browser evidence.** PASSED (local Chromium, 5 passed in
   15.40s; browser suite green in the CI test job):
   - The forged Playwright POST is now a REAL form-encoded request
     (`form=`) carrying the valid existing session CSRF token (cookie +
     `csrfmiddlewaretoken` form field) with a valid reservation payload;
     same denied/no-write assertions (200, truthful denial rendered, zero
     reservations).
   - Custom-brand eligibility controls are exercised at 390 as well as
     1440 (per-row bookable cells + restricted detail + no overflow);
     existing default member/admin viewport checks remain.
   - Exactly TWO privacy-safe screenshots captured in a fresh context and
     actually viewed this round; retained privately BEFORE any later
     Playwright run can clear its default output dir:
     `/home/janezp/codex-work/slaif-auth-048-922064/browser-artifacts/oap-049-b-retained/booking-eligibility-member-detail-1440.png`
     (member restricted-asset detail at 1440: Booking access line +
     truthful warning note; no group names, no member/tokens/CSRF
     visible) and
     `/home/janezp/codex-work/slaif-auth-048-922064/browser-artifacts/oap-049-b-retained/booking-eligibility-admin-asset-390.png`
     (admin asset change at 390: booking-restricted checkbox + bound
     dual-select with the selected operator group; no member data).
   - Note: strategy's independent re-run of the two 049-a browser tests
     (both viewport assertions PASS, 1440 images reviewed) does NOT prove
     the corrected input encoding; the form-encoding fix is proven by
     this round's local and CI runs.
8. **Actual report-head midnight assertion.** PASSED (local Chromium +
   CI). `tests/test_pilot_path.py::test_integrated_pilot_path_shared_state_across_surfaces`
   now navigates the consumed-prefix availability check with an EXPLICIT
   window: `date` = `active_start` converted to the member profile
   timezone (local date) and `days=2`, so the default current-day window
   can no longer clip a prefix that began late the previous local day.
   Only that `page.goto` query changed: the full consumed-prefix
   conflict probe (domain-level, consistent clock), effective-end
   assertions, remainder booking and real browser/domain timing are
   preserved; no app time/window semantics, clock monkeypatch, retries,
   skips or weakened assertions. Focused Chromium run: 1 passed in
   14.90s (local time 22:45 UTC); the identical test passed in the CI
   test job at the implementation head.
9. **Verification/publication.** Local baseline (owned env, OAP_ROLE
   unset where specified): `ruff check .` All checks passed!; `ruff
   format --check .` 232 files already formatted; `mypy src` no issues in
   139 source files; `manage.py check` no issues (0 silenced);
   `makemigrations --check --dry-run` No changes detected; OpenAPI
   `spectacular --validate --fail-on-warn` exit 0; changed-doc links
   14/14; `git diff --check` clean; OAP stdlib harness
   `python3 -m unittest discover -s tests/oap -p 'test_*.py' -v`: Ran 160
   tests, OK (36.44s). Focused local suites as itemized above. One full
   normal CI at the final implementation head (never waived) and the
   required report-head CI; no local full-suite/rehearsal/HTTPS/Gunicorn/
   restore-whole-qualification detour was repeated.

## Observed implementation CI (exact)

At implementation head `464445146f7dc2c110079df6d1dab87645c72881`:

- CI run 39077442644: quality SUCCESS, security SUCCESS, container
  SUCCESS, test SUCCESS — `1185 passed, 1 warning in 481.45s (0:08:01)`.
  The single warning is the pre-existing, unrelated
  `tests/test_product_entry.py:558` DATABASES-override `UserWarning`.
  The 1185 count is the 049-a full suite (1175) plus the 10 new tests
  from this round (5 booking-authorization, 5 restore-probe-selection).
- OAP run 39077442645: oap-harness SUCCESS.

Superseded observation: CI run 39076632805 at the pre-repair commit
`fcdf3e8152d45cc2856c3a1563791d744d9bf2e3` had test SUCCESS (1185 passed,
1 warning in 571.14s — including the real restore drill round trip and
destructive guards) but quality FAILURE on one unformatted test line
(`ruff format --check`: `Would reformat: tests/test_restore_drill.py`).
That line was repaired by the format-only follow-up commit
`464445146f7dc2c110079df6d1dab87645c72881` (1 insertion, 3 deletions;
no behavioral change; probe tests re-run locally, 5 passed) and the full
suite was re-observed green at that exact head. No force-push, no
amend; the implementation head is the last non-report commit.

## Superseded 049-a interpretations (explicit)

- 049-a CI failure #1 (legacy future-policy fixture) was characterized as
  "scope blocker, not a gate-design rejection". Superseded: the fixture
  now carries its legitimate explicit grant before plan creation in the
  (now allowed) file, and the gate remains byte-identical; the test
  proves the stale policy is rejected at APPLY.
- 049-a CI failure #2 (restore round trip) was characterized in the 049-a
  report as an incomplete fixture adaptation. Superseded by the root
  probe and this round: the actual defect was the probe's independent
  first-user/first-asset selection (UUID-order dependent). It is fixed by
  shared-predicate pair selection; the 049-a report-head observation
  "restore roundtrip PASSED on this UUID ordering" is explicitly
  superseded — the round trip now passes by construction, not by UUID
  luck (deterministic direct tests + CI real round trip).
- 049-a acceptance 7 claimed "restricted empty / last-group-deleted"
  coverage. Superseded: only an M2M clear had been executed; a real
  `Group.delete()` of the last allowed group is now proven.
- 049-a's parent-non-inheritance test had an unreachable denial branch
  (union_booker's `allowed` branch always succeeded). Superseded by the
  non-member-principal rewrite with both directions actually denied/
  allowed as specified.
- 049-a's token-loss coverage was direct-grant revocation only. Superseded
  by the capability-group, asset-membership and asset-allow-list variants
  with NEW+cached denial and restored replay.
- 049-a's forged browser POST used `data=dict` (JSON body). Superseded by
  a real form-encoded request with the valid existing session CSRF.

## Limits / uncertainties

- Local host lacks `pg_dump`/`pg_restore` (unchanged environmental fact
  from 049-a; no host tools installed per the order). The three
  pg-tool-dependent `RestoreDrillNegatives` tests and the full real
  round trip therefore ran only in CI, where they PASSED at the
  implementation head.
- The midnight-window fix is structural (the window now explicitly spans
  `active_start`'s member-timezone local date over 2 days); the local
  focused run (current time) plus the CI pass at the implementation head
  are the evidence. No clock monkeypatch was added.
- Report-head CI NOT YET OBSERVED at authoring; the automatic required
  full CI at the exact frozen report head is preserved, not waived, and
  must pass before any conditional merge (strategy separately verifies).
- Target gate unchanged: this is the booking-eligibility slice only.
  Management capabilities, cross-user read-all, token-scope issuance
  refusal, qualification and a fresh independent ICA at the exact merged
  revision remain separate; no deployment, no audit claim, no ICA
  acceptance.
