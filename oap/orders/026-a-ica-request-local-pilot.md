<!-- OAP-META
{
 "id": "026-a",
 "round": "a",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "base_sha": "21f6204d5f03c304991d4cd5c45a74aecdcb686a",
 "issue_number": 51,
 "branch": "codex/51-oap-026-a-ica-request-local-pilot",
 "pr_mode": "CREATE_OR_RESUME",
 "previous_round": null,
 "allowed_paths": [
  "docs/audit/requests/local-pilot.md (NEW — the materialized request, replacing the stale draft)",
  "docs/audit/requests/local-pilot.DRAFT.md (DELETED — superseded; record the deletion)",
  "oap/orders/026-a-ica-request-local-pilot.md",
  "oap/active",
  "oap/reports/026-a-ica-request-local-pilot.md"
 ],
 "forbidden_resources": [
  "any change to any other file (no ARCHITECTURE.md, PLAN.md, product, test, workflow, or other docs change)",
  "any ICA activity: no audit execution, no classifications beyond the ordered UNPROVEN skeleton, no findings, no audit report",
  "any fabricated auditor identity, audit result, measured result, or future revision (ICA-PROTOCOL.md: do not invent accepted targets, measured results, independent identities or future revisions in inactive audit drafts)",
  "any pre-filled 'Result: PASS' or equivalent in the request",
  "any mutating GitHub operation except pushing this branch and opening this objective's PR",
  "deployment of any kind, real secrets, DNS/TLS, production access, private exports",
  "merging or auto-merging any PR (merge is strategy's delegated act after exact-head review)",
  "credentials, auth files, sessions, tokens, auth homes"
 ]
}
-->

# 026-a — Materialize the M-LOCAL-PILOT-EVIDENCE ICA request at merged main 21f6204

## Goal

The human-selected target is now fixed (2026-09-17): determine whether
SLAIF Asset Reservation is ready for its FIRST CONTROLLED INTERNAL-ALPHA
DOCKER DEPLOYMENT, through the documented Docker/Compose path. Per
S-23/SAR-038, an Independent Closure Audit is mandatory before that
milestone/deployment acceptance, and the repository's ICA protocol requires a
materialized request bound to the exact merged revision. This round
materializes the complete ICA request for the current merged main
(21f6204d5f03c304991d4cd5c45a74aecdcb686a), replacing the stale pre-target
draft. The audit itself is NOT performed this round: after merge, strategy
spawns a fresh isolated audit context (permitted by ICA-PROTOCOL.md) and
records the report. No audit bytes, no classifications, no auditor identity
are produced here.

## Durable provenance and requirements

- H: attributable in-session human instruction 2026-09-17 (deployment
  qualification and closure task): "We now want to determine whether SLAIF
  Asset Reservation is genuinely ready for its first controlled
  internal-alpha deployment. The service MUST be deployable through the
  documented Docker/Compose path." Exclusions binding on the audit and this
  round: "Do not interpret this instruction as authorization to perform a
  real deployment, create/rotate real secrets, configure real DNS/TLS,
  expose a host, touch production/private data, or cross any other D2
  boundary." Human milestone acceptance and release/deployment authority
  remain separate from ICA.
- A: S-05 (canonical current documents), S-12 (proof-sized objective;
  H/A/E/I/C), S-16/S-17 (exact-head review; delegated merge), S-19 (truthful
  evidence; name exact commands/results), S-23 (ICA mandatory before
  milestone acceptance; fresh isolated context; human scope -> full
  architecture -> exact revision; IMPLEMENTED/PARTIAL/ABSENT/UNPROVEN;
  no fabricated identities/results), SAR-038 (human target and ICA),
  docs/audit/ICA-PROTOCOL.md (materialization from the ARCHITECTURE.md SAR
  requirement index; structural validation is structural-only).
- E: strategy-verified at merged main 21f6204d5f03c304991d4cd5c45a74aecd
  cb686a (2026-09-17; coding re-verifies each value and records it —
  verify, do not assume; if any value differs, STOP and report BLOCKED):
  - main = 21f6204d5f03c304991d4cd5c45a74aecdcb686a (merge of PR #50 /
    objective 025 rounds a+b+c + quiesce); OAP INACTIVE, pointer ABSENT;
    main CI green (merge 979882e3ed318b0a90f35bd3a99fca0161edb782 and
    quiesce 21f6204: all runs success, head_sha verified).
  - Gate-time rehearsal dispatch at main HEAD: run 35182574499 (workflow
    deployment-rehearsal.yml, head 21f6204) — outcome recorded by strategy
    in the deployment-gate evidence; NOT part of this order's scope.
  - ARCHITECTURE.md SHA-256 at main: 182d9cf924931e846bc7965a079482b6753de
    762af807196ca0b87f8dffdf863.
  - PLAN.md SHA-256 at main: d03eb29713cfbdb7e227413618396e6bb2a7a08749225
    979c3055dacfd461d06.
  - SAR index: ARCHITECTURE.md, SAR-001 through SAR-038 (each row carries
    Source/Inspect/Evidence/initial-UNPROVEN — the materialization source).
  - docs/audit/ICA-REQUEST-TEMPLATE.md is the field template; docs/audit/
    requests/local-pilot.DRAFT.md is the stale pre-target draft (18 lines;
    contains historical wording "Future drafts016–020" and "419-test
    report"); it is superseded by this round's materialized request.
  - docs/audit/ICA-PROTOCOL.md: input order (human scope -> full
    architecture + exact digest -> canonical requirement map -> exact
    merged revision -> enforcing source/tests/negative evidence);
    classifications start UNPROVEN; deferrals recorded out-of-target with
    authority; audit output read-only by default; structural validation
    never proves independence/correctness/closure.
  - oap/bin/check_ica.py: structural validator for requests (human-scope
    line; current 64-hex ARCHITECTURE.md digest in text; "Merged product
    revision:" line; >=10 SAR IDs or --requirements-json cross-check;
    classification vocabulary; Auditor + Independence lines; "negative"
    mentioned; no pre-filled "Result: PASS"; auditor identity left
    unfilled/pending; structural-only disclaimer).
  - Approved deferrals with authority (to be recorded in the request's
    separate deferral section, NOT silently dropped): institutional OIDC /
    password reset / email workflow (SAR-036; roadmap deferred; INSTALL.md
    known-alpha-limitations); projects/memberships/resource restrictions
    (SAR-036; broad authenticated-human authorization is the current model,
    acceptable only under a constrained trusted pilot — the exposure
    boundary is an explicit human-gate input); execution gateway / automatic
    physical allocation (SAR-036); notification system (SAR-036);
    monitoring stack (SAR-036; Phase 4); SmartScheduling production
    cutover (SAR-030 scope; deferred); database role separation + backup
    hardening (docs/security-model.md section 6: "Remain operational work";
    exposure-scope dependent — input to the human gate).
- I: audit-area documentation only. No product, no governance machinery, no
  workflow change. The request is a read-only input to the auditor; it
  binds the audit to the exact merged revision and the real requirement
  source. After merge, strategy (not coding) spawns the independent audit
  context and files the report; if the audit finds in-target defects,
  remediation rounds follow per protocol, then a fresh architecture-to-
  current-main rerun.
- C: S-23 (independence; no self-audit; honest provenance), S-19 (exact
  values, no invention), SAR-038 (human target and ICA).

## Current reconciled state and prerequisites

- Base main (local and remote): 21f6204d5f03c304991d4cd5c45a74aecdcb686a.
  Worktree clean on main; oap/active absent (INACTIVE).
- Fresh round: no local/remote branch codex/51-oap-026-a-ica-request-local-
  pilot, no PR for issue #51 (verify with git ls-remote and gh before
  creation); pr_mode CREATE_OR_RESUME resolves to CREATE. Record the
  GitHub-assigned PR number truthfully.
- If any E-list value differs from the live base, STOP and report BLOCKED
  with the exact discrepancy.

## Ordered read set

Standard compact read set, plus: docs/audit/ICA-PROTOCOL.md (in full),
docs/audit/ICA-REQUEST-TEMPLATE.md (in full), docs/audit/requests/local-
pilot.DRAFT.md (in full — to be superseded), ARCHITECTURE.md (A-03 stack
section; SAR index header + ALL 38 SAR rows' Source/Inspect/Evidence lines),
PLAN.md (P-03 + deferred scope), docs/security-model.md (section 6),
INSTALL.md (section 12 known alpha limitations), oap/bin/check_ica.py
(the structural checks, to know exactly what the validator requires).

## Scope and allowed paths

1. docs/audit/requests/local-pilot.md (NEW) — the complete materialized
   request, following ICA-REQUEST-TEMPLATE.md fields, containing at least:
   - Status line: REQUEST (not an audit result); materialized 2026-09-17 at
     merged main; structural validation via oap/bin/check_ica.py --kind
     request.
   - Milestone: M-LOCAL-PILOT-EVIDENCE (first controlled internal-alpha
     Docker deployment target).
   - Human scope/provenance: the 2026-09-17 instruction, quoted (objective
     sentence + the verbatim exclusions sentence), attributed to the
     in-session human principal; note that human milestone acceptance and
     release/deployment authority remain separate from ICA.
   - Repository: ulfe-lmi/slaif-asset-reservation.
   - "Merged product revision: 21f6204d5f03c304991d4cd5c45a74aecdcb686a"
     (full 40-hex; line starting exactly "Merged product revision:").
   - Canonical PLAN/ARCHITECTURE revisions and hashes: both at the merged
     revision; ARCHITECTURE.md SHA-256 182d9cf924931e846bc7965a079482b6753
     de762af807196ca0b87f8dffdf863; PLAN.md SHA-256 d03eb29713cfbdb7e22741
     3618396e6bb2a7a08749225979c3055dacfd461d06 (re-verified live in this
     round and recorded).
   - Requirement matrix: ALL 38 SARs (SAR-001 through SAR-038), one row
     each, every row: ID + title, initial classification UNPROVEN,
     enforcing source path(s) (from the SAR row's Inspect line), evidence
     pointer (from the SAR row's Evidence line, as an INDEX — e.g. test
     paths/commands — not a claim of result), and a named negative path
     (a concrete falsifying check, e.g. auth-failure path, CSRF rejection,
     exclusion-conflict insert, idempotency replay, restore-into-nonempty,
     rehearsal-residue refusal, fail-closed missing-env, etc.). Rows must
     be materialized from the live ARCHITECTURE.md SAR index (not from
     memory); if a SAR row lacks an Inspect/Evidence line, record the
     missing field explicitly rather than inventing one.
   - Deferrals (separate section, with authority per item): the six groups
     listed in the E section (OIDC/password-reset/email; projects/
     memberships/resource restrictions + the constrained-trusted-pilot
     exposure condition; execution gateway/automatic allocation;
     notifications; monitoring stack; SmartScheduling cutover; database
     role separation/backup hardening) — each with its authority (SAR-036 /
     SAR-030 / security-model section 6 / roadmap) and the note that a
     deferral is out-of-target, not a pass.
   - Auditor/context identity: "PENDING — fresh isolated audit context to
     be spawned by strategy per ICA-PROTOCOL.md after this request is
     merged; concrete identity (model, session origin, spawn time) recorded
     in the audit report." (Must remain unfilled/pending; the validator
     requires an unresolved auditor identity in a request.)
   - Independence evidence: fresh isolated context, no prior involvement
     in this audit or the rounds under audit, inputs limited to human
     scope + request + exact revision + architecture + repository bytes,
     read-only mandate (report-artifact write only), same model family as
     development recorded honestly, structural validation cannot prove
     independence, human retains final milestone acceptance.
   - Audit method paragraph per ICA-PROTOCOL.md (input order; reports/CI/
     test counts are evidence indexes not proof; classify every applicable
     row; name negative paths; findings with provenance and strongest
     reason not to fix now; repeat after remediation on the new exact
     revision; applicable unresolved DHA/D2 gates remain explicit).
   - Deliverable line: the audit report lands at docs/audit/reports/
     M-LOCAL-PILOT-EVIDENCE-<revision-prefix>.md (written by the audit
     context, not this round).
   - The structural-only disclaimer (validation is structural; it never
     proves independence, correctness, or closure) and NO "Result: PASS"
     or equivalent pre-fill anywhere.
2. docs/audit/requests/local-pilot.DRAFT.md — DELETED (superseded by the
   materialized request; the file is a pre-target draft, not an immutable
   historical snapshot; record the deletion and the reason in the report).
3. Round bytes — oap/orders/026-a-ica-request-local-pilot.md (rename from
   the materialized .FINAL source, bytes preserved), oap/active (now
   "026-a"), oap/reports/026-a-ica-request-local-pilot.md.

## Non-goals

- No ICA execution, no audit report, no classifications beyond UNPROVEN,
  no findings, no remediation, no milestone claims.
- No other documentation change (ARCHITECTURE.md, PLAN.md, INSTALL.md,
  security-model.md, etc. all stay byte-identical — the request binds to
  their live digests, not the reverse).
- No product, test, workflow, or dependency change. No OAP expansion.
- No real deployment, no secrets, no DNS/TLS, no merge.

## Numbered acceptance criteria

1. docs/audit/requests/local-pilot.md exists with every ordered field
   (section 1), the "Merged product revision:" line carrying the full 40-hex
   main SHA, the current ARCHITECTURE.md 64-hex digest in the text, the
   complete 38-row SAR matrix (every row UNPROVEN + enforcing path +
   evidence index + named negative path, materialized from the live SAR
   index), the separate deferral section with authorities, the PENDING
   auditor identity, the independence statement, the audit-method
   paragraph, the deliverable line, the structural-only disclaimer, and no
   pre-filled result.
2. docs/audit/requests/local-pilot.DRAFT.md is deleted; the report records
   the deletion + reason (superseded pre-target draft).
3. `python3 oap/bin/check_ica.py --repo . --file docs/audit/requests/local-
   pilot.md --kind request` PASSES at the implementation head (command +
   literal output recorded in the report).
4. The diff between base 21f6204 and the implementation head touches ONLY
   docs/audit/requests/local-pilot.md (new), docs/audit/requests/local-
   pilot.DRAFT.md (deleted), and the round bytes. No other file changes
   (prove by diff; ARCHITECTURE.md and PLAN.md digests re-verified
   unchanged and recorded).
5. CI at the exact implementation head: the four standard jobs plus
   oap-harness all green, head_sha verified from the API (if a standard job
   fails on the known oap-harness flake, document it exactly and show the
   same job green at the same head elsewhere — e.g. the report-head runs).
6. PR description: what was materialized and why (human target fixed
   2026-09-17; 025 merged at 21f6204; ICA mandatory per S-23/SAR-038), the
   exact values bound (revision + both digests), the 38-row matrix summary,
   the deferral list with authorities, the next step (strategy spawns the
   isolated audit context after merge — the audit is NOT performed in this
   PR), and truthful status language (CI-green candidate; real deployment
   not yet evidenced; deployment remains human-authorized).
7. Report (oap/reports/026-a-ica-request-local-pilot.md): report-only
   commit with the implementation head as first parent; contains the diff
   proof, the check_ica.py output, the digest re-verification, the deletion
   record, and the honest implementation-head vs report-head CI separation.
8. DHA outcome: NONE.

## Deferred human adjudication

- Decision: NONE
