<!-- OAP-META
{
 "id": "028-a",
 "round": "a",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "base_sha": "cb2045c51099dbc2878173e18ae5550d10793170",
 "issue_number": 55,
 "branch": "codex/55-oap-028-a-doc-truth-post-027",
 "pr_mode": "CREATE_OR_RESUME",
 "previous_round": null,
 "allowed_paths": [
  "README.md (status bullet line 12 only)",
  "docs/roadmap.md (WO 0014 line 190 + Next-roadmap-item paragraph only)",
  "oap/orders/028-a-doc-truth-post-027.md",
  "oap/active",
  "oap/reports/028-a-doc-truth-post-027.md"
 ],
 "forbidden_resources": [
  "any change to any other file (no product, test, workflow, INSTALL, deployment, or other doc byte)",
  "any change to historical/labeled docs (STATUS.md and docs/project-handoff.md stay byte-identical; they are correctly labeled historical snapshots)",
  "any change to ICA artifacts (docs/audit/requests/local-pilot.md, docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-21f6204.md, ARCHITECTURE.md, ARCHITECTURE-for-agents.md, PLAN.md)",
  "any ICA activity: no audit execution, no classifications, no re-audit, no new audit request",
  "any status wording implying production-readiness, deployment approval, or that a real deployment has been evidenced",
  "any fabricated revision, run ID, result, or PR number",
  "any mutating GitHub operation except pushing this branch and opening this objective's PR",
  "deployment of any kind, real secrets, DNS/TLS, production access, private exports",
  "merging or auto-merging any PR (merge is strategy's delegated act after exact-head review)",
  "credentials, auth files, sessions, tokens, auth homes"
 ]
}
-->

# 028-a — Correct post-027 documentation drift (three lines, two files)

## Goal

Strategy's documentation-truth sweep at base main (section E of the 2026-09-17
human deployment-qualification instruction: "correct current-state drift,
especially post-024 wording") found exactly three stale current-state lines.
Historical documents (STATUS.md, docs/project-handoff.md) are correctly
labeled as historical and are NOT touched. This round makes the three
smallest possible wording corrections so current-state docs tell the truth
about current main.

## Provenance (H/A/E/I/C)

- H: in-session human instruction 2026-09-17 (deployment qualification and
  closure task), section E (documentation truth) and section 9 (precise
  status language).
- A: S-05 (canonical current documents; distinguished intended invariants
  vs current state), S-12 (proof-sized objective), S-16/S-17 (exact-head
  review; delegated merge), S-19 (truthful evidence).
- E: strategy sweep at cb2045c51099dbc2878173e18ae5550d10793170
  (2026-09-17): README.md line 12 "015-a through 024-a"; docs/roadmap.md
  line 190 "015-a through 024-a"; docs/roadmap.md lines 207-213
  "Next roadmap item" paragraph ("objective 024-a ... is complete; the
  current selection is deployment qualification ... (objective 025-a and
  the independent closure audit that follows)"). Live oap/orders/ contains
  order files for 015-a through 027-a (13 orders). Completed since the
  2026-09-17 selection: 024-a (PR #48, merged), 025-a/b/c (PR #50, merge
  979882e), 026-a (PR #52, merge 41d811c; ICA request at 21f6204), 027-a
  (PR #54, merge 55937a6; ICA findings F-001/F-002 fix). ICA executed
  2026-09-17 in a fresh isolated context at product revision 21f6204,
  report docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-21f6204.md (committed
  a7b89d2): 37 IMPLEMENTED / 1 PARTIAL (SAR-037, drift corrected by 027-a) /
  0 ABSENT / 0 UNPROVEN; no in-target blockers. No real deployment has been
  evidenced.
- I: documentation-only truth correction. No product byte, no ICA artifact,
  no historical doc byte changes.
- C: S-19 (exact values), S-22 (truthful status language; CI-green
  candidate, not production-ready), SAR-038 (development merge only).

## Base and prerequisites

- Base main (local and remote): cb2045c51099dbc2878173e18ae5550d10793170.
  Verify with git rev-parse main and git ls-remote origin refs/heads/main;
  if either differs, STOP and report BLOCKED with the exact discrepancy.
- Fresh round: no local/remote branch codex/55-oap-028-a-doc-truth-post-027,
  no PR for issue #55 (verify before creation); pr_mode CREATE_OR_RESUME
  resolves to CREATE. Record the GitHub-assigned PR number truthfully.

## Ordered read set

Standard compact read set, plus: README.md (Status section), docs/roadmap.md
(WO 0014 section + Next-roadmap-item section), docs/audit/reports/
M-LOCAL-PILOT-EVIDENCE-21f6204.md (result statement only, for exact counts),
and `ls oap/orders/` (for the 015-a..027-a existence check).

## Scope (exactly the three corrections)

1. README.md, Status bullet (line 12) ONLY: replace "015-a through 024-a"
   with "015-a through 027-a". No other README change.
2. docs/roadmap.md, WO 0014 section (line 190) ONLY: replace "015-a through
   024-a" with "015-a through 027-a". No other change in that section.
3. docs/roadmap.md, "### Next roadmap item" section ONLY: replace the
   paragraph beginning "Current human selection (2026-09-17):" with this
   exact text (re-wrapping allowed, wording must match):

   "Current human selection (2026-09-17): deployment qualification for the
   first controlled internal-alpha Docker deployment. Completed since that
   selection: 024-a (canonical installation/deployment documentation),
   025-a/b/c (deployment-qualification docs, image reproducibility, and the
   post-merge full-rehearsal CI workflow), 026-a (materialized
   M-LOCAL-PILOT-EVIDENCE ICA request at merged main 21f6204), and 027-a
   (ICA findings F-001/F-002 doc-drift fix). The Independent Closure Audit
   was executed 2026-09-17 in a fresh isolated context at product revision
   21f6204 (report: `docs/audit/reports/M-LOCAL-PILOT-EVIDENCE-21f6204.md`;
   37 IMPLEMENTED / 1 PARTIAL / 0 ABSENT / 0 UNPROVEN; no in-target
   blockers; the single PARTIAL row's drift was corrected by 027-a, with the
   protocol re-audit scheduled at the next milestone-closure attempt). The
   next slice is the first real internal-alpha deployment, human-authorized
   and performed per `INSTALL.md` (deployment-gate brief presented
   2026-09-17; a real deployment has not yet been evidenced). The slice
   after that remains human-selected."

## Non-goals

- No rewrite of historical snapshots (STATUS.md, docs/project-handoff.md
  stay byte-identical; their historical labels are correct).
- No change to any ICA artifact, PLAN/ARCHITECTURE bytes, INSTALL.md,
  docs/deployment.md, runbooks, workflows, product, tests, or dependencies.
- No re-audit, no new audit request, no OAP expansion, no merge, no D2.

## Numbered acceptance criteria

1. `git diff --name-status <base>..<impl>` touches ONLY README.md,
   docs/roadmap.md, and the round bytes; `git diff -U0` shows exactly one
   changed line in README.md and exactly two changed hunks in docs/roadmap.md
   (the line-190 single line and the Next-roadmap-item paragraph).
2. Both "015-a through 027-a" claims are verified true: scripted check that
   oap/orders/ contains one order file per ID 015-a, 016-a, 017-a, 018-a,
   019-a, 020-a, 021-a, 022-a, 023-a, 024-a, 025-a, 025-b, 025-c, 026-a,
   027-a (record the command + literal listing; 15 files).
3. The new Next-roadmap-item paragraph: contains the exact completed-objective
   list, the ICA report path, the exact counts "37 IMPLEMENTED / 1 PARTIAL /
   0 ABSENT / 0 UNPROVEN", and the exact sentence fragment "a real deployment
   has not yet been evidenced"; a grep proves it contains NO
   "production-ready", NO "deployment approved", and NO claim that a
   deployment was performed.
4. STATUS.md and docs/project-handoff.md are byte-identical to base (prove
   by diff).
5. CI at the exact implementation head: four standard jobs plus oap-harness
   all green, head_sha verified from the API (round bytes touch oap/** so
   oap-harness is triggered; if the known pre-existing oap-harness flake
   fails one run, document it exactly and show the same job green at the
   same head in the report-head runs).
6. PR description: the three lines corrected with provenance (strategy
   sweep at cb2045c; the E-section instruction), the verification commands,
   and truthful status language (development merge only; no deployment
   performed or approved; deployment remains human-authorized).
7. Report (oap/reports/028-a-doc-truth-post-027.md): report-only commit with
   the implementation head as first parent; contains the diff proof
   (criterion 1), the orders-listing proof (criterion 2), the paragraph
   grep proofs (criterion 3), the historical-docs byte-identity proof
   (criterion 4), and the honest implementation-head vs report-head CI
   separation.
8. DHA outcome: NONE.

## Deferred human adjudication

- Decision: NONE
