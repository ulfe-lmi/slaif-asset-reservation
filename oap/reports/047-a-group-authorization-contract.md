<!-- OAP-META
{
  "kind": "report",
  "id": "047-a",
  "order_path": "oap/orders/047-a-group-authorization-contract.md",
  "order_sha256": "2b3d16ef5458bab4df4128aee0907dc7d489fd2a6295c90fe2f54c95660eddc4",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 97,
  "pr_number": 98,
  "branch": "codex/97-oap-047-a-group-authorization-contract",
  "implementation_head": "546cdaa21eb5f63400dee4eb56cc3eb2cd1d870d",
  "base_sha": "dad6e29d4f8e4fd941843b230474d35dafb69d1a",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "546cdaa21eb5f63400dee4eb56cc3eb2cd1d870d",
    "runs": [
      {
        "run_id": 39052694874,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      },
      {
        "run_id": 39052694921,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "test": "success",
          "security": "success",
          "container": "success"
        }
      }
    ]
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# Selected group authorization contract

Implementation head SHA: 546cdaa21eb5f63400dee4eb56cc3eb2cd1d870d
Report publication commit: SELF

COMPLETE for the selected M-GROUP-AUTHORIZATION contract (documentation-only, D0).
Branch `codex/97-oap-047-a-group-authorization-contract` from exact base
`dad6e29d4f8e4fd941843b230474d35dafb69d1a`; PR #98 created BEFORE this report with
`Closes #97` in its body. No application, runtime, test, migration, deployment,
dependency, bootstrap or CRITICAL change.

## Acceptance evidence

1. Full source: the strategy-authored A-16 payload was appended to ARCHITECTURE.md
   verbatim (order fence lines 123–156; `diff` against the appended block: no
   difference) and the six stable rows SAR-048..SAR-053 were inserted verbatim
   before A-15 (order fence lines 163–215; `diff`: no difference). A concise top
   note identifies A-16 as the current 2026-10-17 selected target and points to its
   controlled-evolution paragraph; the edition paragraph records the 2026-10-17
   controlled append. Old IDs, invariants and historical baseline/audit prose are
   preserved; no existing row was deleted, renumbered or silently repurposed.
2. PLAN P-08: human provenance (request 2026-10-17 sections 1–11 via order
   provenance H), selected target, explicit no-infrastructure-authorization, the
   prerequisite (A-16 contract) plus five purposes (048 permissions/external ID/
   upgrade; 049 booking; 050 management; 051 bearer; 052 qualification/fresh
   independent ICA) marked scoped future work, not completed; existing milestone
   history preserved; SAR-036's group/asset restriction deferral superseded only
   by A-16; all other deferrals remain.
3. Projection + review: ARCHITECTURE-for-agents.md was recomposed after the full
   source was authored: the six new compact rows (SAR-048..SAR-053) plus the new
   `Selected group authorization target (A-16)` clause carry all A-16 executor
   obligations directly (eligibility, every capability boundary/partial visibility,
   scope + current grants, minimal owner data, explicit upgrades, no execution/
   deployment); the conflicting SAR-010/012/013/016/036 rows carry explicit A-16
   applicability sentences; all other pre-existing clauses are byte-identical. The
   full-source digest was updated to
   `4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd` only after
   semantic reconciliation; full architecture and A-16 remain reference-only (not a
   routine mandatory read). `docs/governance/GROUP-AUTHORIZATION-PROJECTION-REVIEW.md`
   traces all A-16 facets and human sections 1–11 (via the order's H provenance
   record; the raw transcript was not loaded) to full and compact clauses, with
   exact sources/hashes, accepted-vs-candidate changes, honest byte estimates and
   limitations. Semantic review, not an ICA.
4. `docs/authorization.md`: added, clearly labelled SELECTED TARGET / NOT
   IMPLEMENTED BY THIS CONTRACT: permission matrix, Admin/staff distinction,
   baseline and explicit legacy-staff upgrade intent, exact-asset semantics, future
   owner-only vs separate read-all bearer contract and external enforcer boundary.
   No operator commands or endpoints are published as existing; no product history
   ledger.
5. Review coverage: all human sections 1–11 are covered through the A-16 facet
   mapping (review section 2). Privacy/upgrade negative boundaries are recorded in
   the full and compact clauses and the guide: no automatic grants for new
   accounts, no read-all inference from Administration View permissions, minimal
   cross-user representation with explicit exclusions, no SSH/PAM/synchronization/
   execution/GPU/login grants, no rewriting of existing bookings, retained owner
   lifecycle access, owner-only routes preserved. No projects/hierarchies/execution
   invented. Application/test/migration/deployment/dependency/bootstrap files are
   byte-identical to base: `git diff --name-only dad6e29d4f8e4fd941843b230474d35dafb69d1a
   HEAD` lists only ARCHITECTURE.md, PLAN.md, ARCHITECTURE-for-agents.md and
   oap/active (tracked) plus the three new untracked allowed files; every changed
   path is within the order's allowed_paths. No CRITICAL change. `git diff
   --check`: clean.
6. Tests (exact commands):
   - `python3 -m unittest discover -s tests/oap -p 'test_*.py' -v` (system Python
     3.14.4): PASSED 160/160 in a clean environment (`env -u OAP_ROLE`). Run under
     the CODING wrapper environment: 159/160 pass, with
     `test_ba39_strategic_same_prerequisites` failing solely because the wrapper's
     `OAP_ROLE=CODING` environment variable is inherited by the fixture's strategic
     launcher subprocess (error: "conflicting OAP_ROLE=CODING; refusing") — an
     environment artifact, not a code change (the test exercises unmodified
     oap/bin scripts); CI runs in a clean environment and the oap-harness job
     PASSED at the exact head.
   - Changed Markdown link/anchor check over all six changed Markdown files:
     2 relative links verified present; no broken anchors.
   - `git diff --check`: clean.
   - Remote CI at exact head 546cdaa21eb5f63400dee4eb56cc3eb2cd1d870d (observed):
     quality PASSED (14s), test PASSED (9m23s), security PASSED (12s), container
     PASSED (24s) — GitHub Actions run 39052694921, conclusion success; oap-harness
     PASSED (37s) — run 39052694874, conclusion success. No missing/skipped/
     cancelled check at the head; the four product CI jobs remain intact.
   - Focused checks were used during editing; no repeated expensive full-suite runs
     without a relevant change/failure; no unrelated bespoke qualification.

## Uncertainty, privacy, dependencies, DHA, limits

- Report-head CI is not observed at authoring; strategy observes it after this
  immutable report is published. Implementation CI is separately recorded above.
- The measured routine coding read set total is 51047 bytes, exceeding the archived
  A-15-era 50000-byte ceiling by 1047 bytes (projection 36124 bytes vs the archived
  20000-byte target). This is reported honestly in the review (sections 3/4);
  disposition is strategy-owned (redistill in a later order, or accept the new
  measured set). No truncation of any A-16 obligation was performed.
- The raw human request 2026-10-17 transcript is outside the coding read set; the
  A-16 payload in order 047-a is the authorized record of sections 1–11.
- No credentials, private artifacts or sensitive data in this report or the
  changed documents.
- DHA: `Decision: NONE` per the order; no CRITICAL entry was created or disposed
  of. No product milestone acceptance, release or deployment authorization.
- This contract is not an implementation or qualification claim: SAR-048..SAR-053
  are initially UNPROVEN until a fresh independent ICA at the exact merged
  revision.
- Limits: the semantic mapping is a deliberate clause-level comparison, not an
  ICA; compact clauses are faithful condensations of A-16, whose full wording
  remains in root A-16 (reference only).
