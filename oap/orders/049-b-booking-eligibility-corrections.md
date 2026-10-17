<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "049-b",
  "objective": 49,
  "round": "b",
  "slug": "booking-eligibility-corrections",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "12947e9b368445eeb4a48416421626224b49f4dc",
  "issue_number": 101,
  "branch": "codex/101-oap-049-a-booking-eligibility",
  "pr_mode": "AMEND",
  "pr_number": 102,
  "previous_round": "049-a",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd",
    "PLAN.md": "2c856ae47ec985b953a8d26edbe2c07fd343833a41bc45aefcd304a7e67c1432",
    "ARCHITECTURE-for-agents.md": "41c32e0b0d6427a173dfe0b722446ae8ee311f3880929db65ed0245309b3a59e",
    "src/slaif_reservation/accounts/authorization.py": "d1b0879fbda947c7c9a75aa153a88a272a3481d33ea74a9d8ef25bbc39daaf6b",
    "src/slaif_reservation/assets/authorization.py": "46cec7345fcaaff5b06f870cd3c5bf28e55359d2874fb18a810873a044a51a39",
    "src/slaif_reservation/reservations/services.py": "fcba30664d6f44cee7caf5fd2b9130fa820f6aeca257da56fcc1016592065368",
    "src/slaif_reservation/legacy_import/planner.py": "7afa35c321d7a14732021874291c48d76c588e0bfaf66f8bd92f4b0b76a567a6",
    "src/slaif_reservation/legacy_import/importer.py": "6f6c275eee4dc9836559d14b63b2465ed962d7b04cb54d9f41f8ae3bdccf01f9",
    "src/slaif_reservation/api/management/commands/restore_drill.py": "8063db907d7fdc000fb31d6175c908c4768a628624dfb4dabfb0b8c37957a2e4"
  },
  "requirements": [
    "SAR-001",
    "SAR-005",
    "SAR-006",
    "SAR-007",
    "SAR-008",
    "SAR-009",
    "SAR-010",
    "SAR-011",
    "SAR-012",
    "SAR-014",
    "SAR-015",
    "SAR-017",
    "SAR-018",
    "SAR-019",
    "SAR-020",
    "SAR-028",
    "SAR-029",
    "SAR-030",
    "SAR-032",
    "SAR-043",
    "SAR-044",
    "SAR-048",
    "SAR-049",
    "SAR-053"
  ],
  "allowed_paths": [
    "tests/test_legacy_import.py",
    "src/slaif_reservation/api/management/commands/restore_drill.py",
    "tests/test_restore_drill.py",
    "tests/test_pilot_path.py",
    "docs/runbooks/backup-and-restore.md",
    "tests/test_booking_authorization.py",
    "tests/test_booking_access_upgrade.py",
    "tests/browser/test_booking_authorization_browser.py",
    "src/slaif_reservation/web/views.py",
    "docs/authorization.md",
    "INSTALL.md",
    "oap/active",
    "oap/orders/049-b-booking-eligibility-corrections.md",
    "oap/reports/049-b-booking-eligibility-corrections.md"
  ],
  "forbidden_resources": [
    "Any source edit except truthful web denial-reason selection and narrow restore probe principal/asset selection; specifically keep shared predicate/service/API/legacy planner+apply gates, model and new migration byte-identical to049-a.",
    "No changes to core reservation policy/time/exclusion/lifecycle/audit/idempotency/authentication/abuse/API scopes or endpoints; no automatic permission/group grants, no global fixture grants or UserManager defaults.",
    "No dependency/runtime/Compose/proxy/settings/bootstrap/architecture/PLAN/projection/governance/helper/image ownership/clock changes. Prior049-a and older orders/reports immutable.",
    "No real user/data/export/DB/deployment/host/DNS/TLS/firewall/secret resources, foreign container/process inspection or cleanup, broad host packages, merge/automerge or delegation."
  ],
  "provenance": [
    {
      "marker": "H",
      "source": "Human authorization extension request sections2-4,7,9-11; explicit Concentrated OAP/coding clarification",
      "section_or_evidence": "Same selected scope: explicit booking capability and exact-asset eligibility, active-human/owner lifecycle, deliberate upgrade, meaningful positive/negative evidence. No expanded product target."
    },
    {
      "marker": "A",
      "source": "ARCHITECTURE.md A-16 and SAR-049/SAR-053",
      "section_or_evidence": "One shared reservation creation authority, no Staff/superuser asset-group bypass or parent inheritance; preserve existing grants/rows/operational boundaries."
    },
    {
      "marker": "E",
      "source": "049-a implementation5fb13875f90c00bd222125856fb5e1f1f13d2350 / report6d08d99ddf724db1eb437dff7c028e8ab7223786 / PR102",
      "section_or_evidence": "Truthful PARTIAL: CI39072679343 has1173passed2failed; quality/security/container/OAP pass. Legacy positive fixture omitted from049-a allowed paths; restore probe picks arbitrary no-book first human. Immutable report preserved, exact-parent/remote verifier PASS."
    },
    {
      "marker": "I",
      "source": "STRATEGIC whole frozen049-a diff review and private owned-PG test_review_049.py at5fb13875f90c00bd222125856fb5e1f1f13d2350",
      "section_or_evidence": "Root probes2FAIL1PASS in2.81s: restore probe rejects valid eligible pair; non-reservable direct GET gives false group reason; same bearer group revocation before replay and retained owner cancel work. Root Chromium2PASS6.44s/1440+390; actually inspected member/admin1440 PNGs. Required parent negative/delete/token ACL evidence and lazy upgrade snapshot incomplete."
    },
    {
      "marker": "C",
      "source": "049-a numbered acceptance2-9 and collected strategic R1-R7 review",
      "section_or_evidence": "One bounded corrective round on same issue101/PR102; no planner weakening, blanket grants or unrelated refactor. Restore selector compatibility is actual demonstrated dependency of booking gate."
    },
    {
      "marker": "E",
      "source": "Frozen049-a report-head CI39073753109/OAP39073753119 at6d08d99ddf724db1eb437dff7c028e8ab7223786",
      "section_or_evidence": "Terminal report CI1173passed2failed: legacy future fixture and test_pilot_path.py:617 midnight-clipped availability assertion; restore roundtrip passed by arbitrary UUID order, does not repair actual selector defect. Other4checks success. Full report-head run preserved/not cancelled."
    }
  ],
  "decision_class": "D0",
  "target_gate": "M-GROUP-AUTHORIZATION bookingeligibilityslice only; management/read_all/qualification/independentclosure follow; no release/deployment",
  "expected_report_path": "oap/reports/049-b-booking-eligibility-corrections.md",
  "tests": [
    "Focused legacy future fixture and existing legacy-import suite; shared authorization new negative tests with real owned PostgreSQL.",
    "Deterministic direct restore-probe tests: first no-book user skipped; incompatible restricted asset skipped; valid current user/asset pair succeeds; no eligible pair fails with no writes/grants; existing real roundtrip and destructive safety guards in normal fullCI.",
    "Correct parent-denial/actualGroup.delete/current bearer grant+membership+ACL loss/new+cachedPOST/restored replay/retained owner cancel+release/inactive-service-superuser checks; preserve old meaningful negatives.",
    "Materialized pre-migrate snapshot and operator-configured ACL retention on repeat migrate; affected web denial-reason tests; actual form-encoded Chromium forged POST with CSRF; default/custom1440+390 focused assertions; MAX2selected screenshots member1440/admin390 actually viewed and retained privately.",
    "Focused tests while editing, Ruff/mypy/check/migrationsdryrun/OpenAPI/docs links/diffcheck;160OAP tests withOAP_ROLEunset. FullnormalCI once at finalimplementation and required reporthead; no localfull/rehearsal/HTTPS/Gunicorn/restore wholequalification detour.",
    "Report-head reproduced midnight integration assertion: explicit availability date from active_start in member timezone, preserve consumed-prefix conflict/effective-end checks; focused real Chromium pilot test. No app time/window or global clock changes."
  ]
}
-->

# 049-b — complete booking-eligibility compatibility and required negative evidence

## Goal / scope

Correct the collected defects and evidence gaps in frozen049-a on SAME issue101, branch and PR102. Base main remains12947e9b368445eeb4a48416421626224b49f4dc; start from exact current report6d08d99ddf724db1eb437dff7c028e8ab7223786 (first parent5fb13875f90c00bd222125856fb5e1f1f13d2350). Do not replay048/047, rewrite049-a or redesign the selected booking gate. Result is still SAR-049 booking slice, not management/read-all/milestone closure.

## Compact reads

Follow normal CODING router/law/projection/communication/SECURITY-CORE/TESTING-CORE, then this order. Read049-a acceptance2-9 and report exact CI failures/limits (not all older history); relevant code/tests only. STRATEGIC R1-R8 are reproduced below; no need to ingest private strategic handoff or full architecture/PLAN. Reuse qualified owned environment from049-a and private local-testing memo; no new agent/dependency/platform.

## Numbered acceptance / negative paths

1. **Legacy positive fixture:** tests/test_legacy_import.py is now allowed solely to give the legitimately booking future-policy-revalidation fixture its explicit real Book assets permission BEFORE plan creation. It must again prove the stale policy is rejected at APPLY with zero reservations/provenance/success audit. Preserve planner AND apply authorization checks byte-identically. Do not grant every legacy test user merely for convenience: completed-past no-grant tests still prove the historical exception. Preserve assertions and source classifications.
2. **Restore probe compatibility (actual runtime dependency):** api/management/commands/restore_drill.py currently picks first active human and first policy-qualified asset independently. That is no longer sufficient: first user may lack book_assets or exact-asset membership even though an eligible pair exists (root reproduced with stable UUID1 reader/UUID2 booker). Select a current active human and an active/reservable/exclusive asset with effective policy that pass the SAME existing user_can_book_asset predicate together. Continue using create_reservation as authority and the existing PROBE_WINDOWS/policy/time/audit/error handling. Never grant permissions/groups, change asset ACL or add an authorization bypass to make a drill work. If no eligible pair exists, fail clearly and safely before a probe write. Tests pin deterministic no-book-first-user, incompatible restricted asset/pair and valid later pair, and no-eligible-pair refusal/no writes/no grants. Preserve all dry-run/owned target/source-write opt-in/backup/restore/cleanup boundaries. Run direct probe tests locally; full actual roundtrip/destructive guards in normal CI where pg_dump/pg_restore exist. Do not install host tools or run a bespoke local restore qualification.
3. **Required negative evidence, no feature expansion:** repair test_no_parent_inheritance_either_direction: its current union_booker has group_a and its `allowed` branch always succeeds, so the rejection branch is unreachable. With a nonmember holding book_assets, prove restricted parent denied/unrestricted child allowed AND unrestricted parent allowed/restricted child denied; keep eligible member positives without conflicting intervals. Test real deletion of the last allowed Group (current test only clears M2M), leaving restricted=True/empty and new creation denied, old booking unchanged. Use valid unchanged bearer tokens to prove removing a capability-carrying group, removing only asset-allowed membership while retaining book_assets, and removing the group from the asset allow-list blocks NEW and cached create POSTs; restoring access replays original status/body/correlation without another reservation/audit. Preserve the existing direct-grant revocation case. Prove own list/detail/cancel AND release after exact-asset eligibility loss (active/upcoming accepted records, current lifecycle/cutoff rules), including bearer release which the current owner-only test never exercises. Pin inactive/service-account superuser denial, not only ordinary service accounts. No individual permission/global autouse/default-manager bypass, and no cross-user scope/mutation work.
4. **Truthful browser refusal:** direct reserve URL for an unrestricted non-reservable asset currently tells an otherwise eligible member they are not in approved groups (root reproduced). Keep refusal, but choose the actual reason: asset non-reservable/unsupported mode vs missing booking capability vs allowed-group mismatch. Do not change asset active/reservable rules, filters, availability privacy or accepted owner lifecycle. Add focused direct GET/POST assertions for truthfulness/no writes, preserving existing negative authorization tests.
5. **Real upgrade idempotence evidence:** tests/test_booking_access_upgrade.py currently stores `before` as an unevaluated QuerySet then evaluates both snapshots AFTER migrate. Materialize the before snapshot BEFORE the command. Verify a deliberately operator-configured restriction and allowed-group list survive a repeated migrate; keep all existing populated-row preservation/default-unrestricted checks. New migration/model bytes unchanged.
6. **Current documentation, only affected text:** place deliberate reservations.book_assets assignment (group or individual) and restricted-asset membership guidance next to ordinary-account setup in INSTALL's required/completion path, not only its late limitations; no default auto-enrolment. Remove round-number migration narration from normal INSTALL wording. Reconcile false current statements in docs/authorization (foundation helper now used by booking gates; booking behavior no longer wholly planned); other management/read_all remain planned. Mention new asset ACL fields/list are backed up, reversing that migration drops that configuration (code rollback does not restore it), and document restore probe's eligible user/asset-pair prerequisite in backup-and-restore runbook. Preserve Compose project names/topology and existing backup instructions. Do not rewrite README/history/governance or invent a new ADR.
7. **Focused browser evidence:** change forged Playwright POST from data=dict (JSON) to form= with valid existing session CSRF, a valid reservation payload and same denied/no-write assertions. Exercise custom-brand eligibility controls at390 as well as1440; existing default member/admin viewport checks remain. Preserve maxTWO selected screenshot inputs in fresh context: member1440 and admin390 are enough (desktop admin already reviewed at049-a). Retain privacy-safe screenshots in the private evidence folder BEFORE another Playwright run can clear its default output, actually view them and report exact retained paths. No large image bundles, full visual redesign or brittle snapshots. Root independently reran two049-a browser tests with both viewport assertions PASS and reviewed their1440 images; don't claim that proves your corrected browser input encoding.
8. **Actual report-head midnight assertion:** full report-head CI39073753109 completed with1173passed2failed: legacy fixture plus tests/test_pilot_path.py:617. The restore roundtrip happened to pass (arbitrary UUID ordering), so its selector defect remains proven by implementation CI/root deterministic test, not repaired. The browser pilot test expects previous-local-day23:40 consumed-prefix start in a default availability window beginning current-day00:00, which correctly clips it. Adjust ONLY the relevant browser page.goto query to explicitly use active_start converted to the member profile timezone/local date and sufficient days (e.g.2); preserve full prefix/effective-end/conflict assertions and real browser/domain timing. No production availability/date semantics, clock monkeypatch, retries, skips or weakened assertions. Run that focused Chromium integrated pilot test, which is already an affected fixture from049-a.
9. **Verification/publication:** focused relevant tests during edits. Final lint/format/types/check/makemigrationsdryrun/OpenAPI--validate--fail-on-warn/changed-doc links/diffcheck and160OAP stdlib tests withOAP_ROLEunset; full normal CI at final implementation and exact report head, never waive failures. Do not repeat local full suite/unchanged operational/HTTPS/Gunicorn/restore wholequalification. Prior049-a CI failure and report overclaims (last Group deletion, parent negative and token membership coverage; restore being merely fixture omission) remain historical; supersede explicitly with concrete corrected evidence in new report, do not edit immutable report. Group/capability auth checks, policy/time/lifecycle/API/idempotency core behavior unchanged beyond selected049 scope.

## Non-goals / strongest objection

Do not make code fit an omitted fixture by weakening planner/advisory rejection; do not grant every staff account or modify restore-source permissions to pass a probe. Main objection is that operational probe compatibility and genuine negative evidence were missing despite numerous passing tests. Resolve with shared-predicate selection and meaningful required cases, no new policy language, command framework, general refactor or unselected feature. Management gates/read_all/issuance follow separately. D0, no new human risk/product decision, no CRITICAL entry.

## Owned resources / execution

Reuse ONLY existing owned ~/codex-work/slaif-auth-048-922064 source copy/Python3.13/Chromium and PG17 CID7680db038ecebff114a19a929c6b2e3800d7274b23254a41707c2873d7c4067d/name slaif-auth-048-922064/loopback22708 after exact receipt validation. Synthetic0600 env data never printed. Sync only authorized Git-listed branch sources; sequential database tests, no host-wide/foreign resource inspection, no host package installs. Source copy lacks Git by design: do not recreate it or run operational harness qualification locally. Source-before-Codex/--yolo/right tmux pane already handled by authorized wrapper. Concrete edit or smallest diagnostic within15min after compact reads. No subagents.

## Publication / reporting / recovery

Amend existingPR102, keep Closes #101. Commit/push allowed corrections + exact new order/active bytes, observe truthful normal full implementation CI, capture literal full implementation head, then immutable report-only commit with that head as first parent, Report publication commit: SELF. Report acceptance1-9, actual failures/skips/results/screens retained, superseded049-a interpretations, no invented CI or future SHAs. Push and verify actual remote/PR/head/order/report-only/parent before exact response FIFO OK, then exit/no more mutation. Report-head CI NOT YET OBSERVED at authoring, strategy separately verifies. If blocked publish truthful PARTIAL, do not force green or expand scope. Never merge/automerge/activate another order. Keep same objective/branch/PR if interrupted.

## Deferred human adjudication
- Decision: NONE
