<!-- OAP-META
{
  "id": "032-c",
  "round": "c",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_sha": "3abe17d026d7ebfe402426afd89e30cdc6924f61",
  "issue_number": 63,
  "branch": "codex/63-oap-032-a-internet-ux-contract",
  "pr_mode": "AMEND",
  "previous_round": "032-b",
  "pr_number": 64,
  "allowed_paths": [
    "ARCHITECTURE-for-agents.md (exact SAR-041 negation correction only)",
    "docs/governance/INTERNET-UX-PROJECTION-REVIEW.md (corresponding correction note and actual projection hash/measurements only)",
    "oap/orders/032-c-preserve-inactive-policy.md",
    "oap/active",
    "oap/reports/032-c-preserve-inactive-policy.md"
  ],
  "forbidden_resources": [
    "all product/source/runtime/config/test/dependency/migration/inventory changes",
    "all immutable historical reports/orders/bootstrap archives/digests/maps/manifests and installed role-law files",
    "real production/lab/private data/secrets/DNS/TLS/firewall/public exposure",
    "foreign/ignored files, valuable deployment resources, reset/clean/stash/forcepush, merge or auto-merge"
  ],
  "requirements": [
    "SAR-001",
    "SAR-002",
    "SAR-003",
    "SAR-004",
    "SAR-005",
    "SAR-006",
    "SAR-007",
    "SAR-008",
    "SAR-009",
    "SAR-010",
    "SAR-011",
    "SAR-012",
    "SAR-013",
    "SAR-014",
    "SAR-015",
    "SAR-016",
    "SAR-017",
    "SAR-018",
    "SAR-019",
    "SAR-020",
    "SAR-021",
    "SAR-022",
    "SAR-023",
    "SAR-024",
    "SAR-025",
    "SAR-026",
    "SAR-027",
    "SAR-028",
    "SAR-029",
    "SAR-030",
    "SAR-031",
    "SAR-032",
    "SAR-033",
    "SAR-034",
    "SAR-035",
    "SAR-036",
    "SAR-037",
    "SAR-038",
    "SAR-039",
    "SAR-040",
    "SAR-041",
    "SAR-042",
    "SAR-043",
    "SAR-044",
    "SAR-045",
    "SAR-046",
    "SAR-047"
  ],
  "decision_class": "D0",
  "target_gate": "M-INTERNET-UX-PILOT development; real exposure remains human D2",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "06dd0f50e778b9843e2a709caa0ae1f0c97f48baee726f4e3a1397cc6a198d8c",
    "PLAN.md": "b19219e2d727af5a9554e011ba45a786f1bb61f25c001011fc18006cae665d08"
  }
}
-->

# 032-c — Preserve inactive-policy configuration in the executor contract

## Goal and provenance
H: human requirement 2 requires predictable upgrades and preservation of operator-configured policies. A: full A-15 and SAR-041, S-20 semantic projection duty, preceding 032-b criterion 3 explicitly prohibits silent reactivation. E: actual frozen report deaf1cdf7ec73e1430a6638c6c8a8888ae4d43dd, implementation first parent 277b0090637a35092a8a43da6c0e0c153717dcf2, PR64 identity verified, all five exact report-head checks SUCCESS. Root source review found SAR-041 says `no silent overwrite, reactivation supported;` whereas the full architecture requires preserving deliberately inactive operator configuration. This contradicts the order and can mislead the next initialization implementation. Other 032-b coverage expansions are retained. C: D0 correction of a lost negation, not a new policy decision; no CRITICAL or deployment consequence.

## Scope and non-goals
Same issue63/PR64/branch. No full architecture, PLAN, old 38 clauses, application, runtime, dependency, migration, tests, archive, role law or other document changes. Previous orders/reports are immutable. No foreign resource, real data, secret, network/exposure, reset/clean/stash/force-push or merge/auto-merge.

## Numbered acceptance
1. In ARCHITECTURE-for-agents.md, replace exactly one occurrence of `no silent overwrite, reactivation supported;` with `no silent overwrite or reactivation;`. Preserve every other normative clause byte-identically, including the expanded qualification inventory. This is the intended faithful contract: initialization must not silently reactivate operator-inactive configuration. Do not add a reactivation feature or infer a future operator workflow.
2. Update only the corresponding current projection review record: note that the preceding compact wording was incorrect and is superseded by this precise correction; recompute the actual projection hash and exact byte measurements. Full architecture and PLAN hashes stay unchanged. Preserve old semantic mapping and historical records. Projection remains <=20000 bytes and mandatory transitive read set <=50000; tokens UNMEASURED. Do not describe 18 bytes of margin as a large margin; further growth will need explicit faithful redistillation, not truncation.
3. Verify exact one-phrase projection diff, unchanged original 38 clauses/full architecture/PLAN/runtime/dependencies/migrations, current links, appropriate lint/format/type/diff and the five standard checks at the literal implementation head. No new tests for prose. Normal order/pointer/implementation push -> exact five checks -> immutable report-only first-parent actual implementation SHA / publication SELF / report-head checks unobserved at authoring -> push and actual remote verification -> response then exit. Closes #63 remains in PR64.

## Negative paths and strongest objection
A short incorrect negation can cause a later initializer to reactivate operator-disabled booking authority. Exact source/projection comparison and the one-phrase correction prevent that. CI alone cannot establish semantic equivalence; the strategic review does so, and is not an ICA. No implementation or milestone-readiness claim is made here.

## Recovery and reporting
Reconcile the same branch/PR on interruption; do not rewrite 032-a or 032-b reports, which remain historical claims. Expected report oap/reports/032-c-preserve-inactive-policy.md. No new model/provider/profile/home settings. Report actual diff/hash/bytes/checks and superseded interpretation without broad cleanup.

## Deferred human adjudication
- Decision: NONE
