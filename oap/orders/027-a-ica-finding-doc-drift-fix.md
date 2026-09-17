<!-- OAP-META
{
 "id": "027-a",
 "round": "a",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "base_sha": "a7b89d21dbb2512d94168d4f3c8a6ceb2f283e45",
 "issue_number": 53,
 "branch": "codex/53-oap-027-a-ica-finding-doc-drift-fix",
 "pr_mode": "CREATE_OR_RESUME",
 "previous_round": null,
 "allowed_paths": [
  "ARCHITECTURE-for-agents.md (SAR-022 line only: DRF3.16 -> DRF3.17)",
  "ARCHITECTURE.md (header line 5 only: snapshot path correction)",
  "oap/orders/027-a-ica-finding-doc-drift-fix.md",
  "oap/active",
  "oap/reports/027-a-ica-finding-doc-drift-fix.md"
 ],
 "forbidden_resources": [
  "any change to any other file (no product, test, workflow, request, report, or other doc byte)",
  "any change to the ICA report docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-21f6204.md or the request docs/audit/requests/local-pilot.md (revision-bound artifacts, immutable)",
  "any ICA activity: no audit execution, no classifications, no re-audit, no new audit request",
  "any fabricated measurement, digest, or revision; any change to a Git blob hash citation",
  "any mutating GitHub operation except pushing this branch and opening this objective's PR",
  "deployment of any kind, real secrets, DNS/TLS, production access, private exports",
  "merging or auto-merging any PR (merge is strategy's delegated act after exact-head review)",
  "credentials, auth files, sessions, tokens, auth homes"
 ]
}
-->

# 027-a — Fix ICA findings F-001/F-002 (two-line governance-doc drift)

## Goal

The fresh-isolated ICA at product revision 21f6204 (report
docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-21f6204.md, recorded at main
a7b89d2) found exactly two LOW documentation-drift defects, both
strategy-spot-verified against live bytes on 2026-09-17:

- F-001 (SAR-037): ARCHITECTURE-for-agents.md line 51 (the SAR-022
  projection row) says "DRF3.16" while the canonical ARCHITECTURE.md
  SAR-022 row (line 526) says "DRF3.17" and uv.lock pins djangorestframework
  3.17.2. The auditor's scripted 38-row comparison found this as the ONLY
  semantic drift.
- F-002: ARCHITECTURE.md header line 5 cites the preserved baseline
  snapshot at `sources/repository/docs-architecture.md`, which does not
  exist in-tree (git ls-files count 0). The byte-identical snapshot (Git
  blob 246870a7771452ce3878c228b9ad7ffd8e71eda0, verified by
  git rev-parse) lives at docs/bootstrap/1/previous/docs-architecture.md,
  with docs/architecture.md as the compatibility pointer.

This round makes the two smallest possible wording-only corrections so
current main carries no known ICA finding.

## Provenance (H/A/E/I/C)

- H: in-session human instruction 2026-09-17 (deployment qualification and
  closure task) — the ICA and its findings are the mandated closure
  mechanism for the selected internal-alpha target; findings require
  bounded H/A/E/I/C-linked repair (ICA-PROTOCOL.md).
- A: S-05 (one current canonical architecture; source-observed
  implementation never papered over), S-12 (proof-sized objective),
  S-16/S-17 (exact-head review; delegated merge), S-19 (truthful evidence),
  S-23 (findings create bounded closure orders; the architecture-to-
  current-main rerun is required BEFORE accepting the milestone complete —
  see Non-goals for the recorded sequencing decision).
- E: ICA report findings F-001/F-002 (docs/audit/reports/
  M-LOCAL-PILOT-EVIDENCE-21f6204.md, committed at a7b89d2); strategy
  spot-verification 2026-09-17 (grep line 51 vs line 526 vs uv.lock
  version 3.17.2; git ls-files 'sources/repository' = 0; git rev-parse
  HEAD:docs/bootstrap/1/previous/docs-architecture.md =
  246870a7771452ce3878c228b9ad7ffd8e71eda0).
- I: documentation-only repair. The ICA report and request stay
  revision-bound and immutable; no audit is executed or re-executed in
  this round.
- C: S-19 (exact values), S-23 (honest closure sequencing), SAR-037
  (projection must not drift from canonical), SAR-038 (this merge is a
  development merge only).

## Base and prerequisites

- Base main (local and remote): a7b89d2 (ICA report commit). Verify with
  git rev-parse main and git ls-remote origin refs/heads/main; if either
  differs, STOP and report BLOCKED with the exact discrepancy.
- Fresh round: no local/remote branch codex/53-oap-027-a-ica-finding-doc-
  drift-fix, no PR for issue #53 (verify before creation); pr_mode
  CREATE_OR_RESUME resolves to CREATE. Record the GitHub-assigned PR number
  truthfully.

## Ordered read set

Standard compact read set, plus: the two lines named in F-001/F-002, the
canonical SAR-022 row (ARCHITECTURE.md line 526), docs/architecture.md
(compatibility pointer), uv.lock djangorestframework entry, and the
ICA report findings section (F-001/F-002) for exact wording.

## Scope (exactly two wording-only line corrections)

1. ARCHITECTURE-for-agents.md, line 51 ONLY (the SAR-022 projection row):
   replace "DRF3.16" with "DRF3.17" so the row reads "Preserve
   Python3.13, Django5.2, DRF3.17, PostgreSQL17, ..." — matching the
   canonical SAR-022 row exactly on the stack labels. Do NOT touch line 7
   (the "Existing baseline" historical description of baseline 1fcc2c91,
   which pre-dates the 016-a dependency remediation) or any other line.
2. ARCHITECTURE.md, header line 5 ONLY: replace the path
   `sources/repository/docs-architecture.md` with
   `docs/bootstrap/1/previous/docs-architecture.md` (wrap as needed so the
   sentence stays grammatical). Do NOT change the Git blob citation
   (246870a7771452ce3878c228b9ad7ffd8e71eda0) or any other header text.

## Non-goals (recorded sequencing decision, S-23)

- NO re-audit and NO re-materialized ICA request in this round. Recorded
  decision: the 21f6204 ICA report remains the revision-bound audit record
  for the deployment gate (it is true at its audited revision); this fix
  changes two governance-doc reference lines only, zero product bytes.
  Per ICA-PROTOCOL.md the architecture-to-current-main matrix rerun is
  required BEFORE the milestone is accepted complete — it is scheduled at
  the next milestone-closure attempt (post-deployment pilot evidence)
  against whatever revision is then-current. Strongest reason not to
  re-audit now: a full fresh-context cycle for two doc lines is the
  ceremony the human standing instruction minimizes, and it cannot change
  the deployment-gate evidence (gate revision 21f6204 is unchanged).
- No change to any test (tests/oap/test_ba51_52_continuity.py only
  existence-checks the read-set files; verified no hash pinning).
- No product, workflow, request, report, or other doc byte. No OAP
  expansion. No real deployment, no secrets, no DNS/TLS, no merge.

## Numbered acceptance criteria

1. `git diff --name-status <base>..<impl>` touches ONLY
   ARCHITECTURE-for-agents.md, ARCHITECTURE.md, and the round bytes.
   Exactly one changed line in each of the two doc files (proven by
   `git diff -U0`).
2. ARCHITECTURE-for-agents.md line 51 contains "DRF3.17" and does NOT
   contain "DRF3.16"; line 7 is byte-identical to the base. Scripted
   check: the projection SAR-022 row's stack labels (Python3.13,
   Django5.2, DRF3.17, PostgreSQL17) match the canonical SAR-022 row's
   stack labels; record the comparison command + output.
3. The ARCHITECTURE.md header cites
   `docs/bootstrap/1/previous/docs-architecture.md`, that path exists in
   the tree, and `git rev-parse HEAD:docs/bootstrap/1/previous/
   docs-architecture.md` prints 246870a7771452ce3878c228b9ad7ffd8e71eda0
   (command + literal output recorded). The blob citation is unchanged.
4. Report records the NEW ARCHITECTURE.md SHA-256 (header edit changes the
   canonical digest; expected to differ from 182d9cf924931e846bc7965a762af8
   07196ca0b87f8dffdf863 — record both values and note the 21f6204 ICA
   request/report remain bound to the old digest as revision-bound
   artifacts). PLAN.md digest must be unchanged (d03eb29713cfbdb7e22741361
   8396e6bb2a7a08749225979c3055dacfd461d06).
5. CI at the exact implementation head: four standard jobs plus oap-harness
   all green, head_sha verified from the API (the round bytes touch oap/**
   so oap-harness is triggered; if the known pre-existing oap-harness flake
   fails one run, document it exactly and show the same job green at the
   same head in the report-head runs).
6. PR description: the two findings fixed (with provenance: ICA report
   F-001/F-002 + strategy spot-verification), the exact one-line diffs,
   the recorded no-re-audit sequencing decision (S-23 non-goal above), and
   truthful status language (development merge only; deployment gate
   revision 21f6204 unchanged; deployment remains human-authorized).
7. Report (oap/reports/027-a-ica-finding-doc-drift-fix.md): report-only
   commit with the implementation head as first parent; contains the
   diff proof (criterion 1), the scripted stack-label comparison output
   (criterion 2), the rev-parse proof (criterion 3), the digest
   before/after record (criterion 4), and the honest implementation-head
   vs report-head CI separation.
8. DHA outcome: NONE.

## Deferred human adjudication

- Decision: NONE
