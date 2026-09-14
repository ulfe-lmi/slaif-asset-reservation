<!-- OAP-META
{
 "schema_version": 1,
 "kind": "order",
 "id": "015-a",
 "objective": 15,
 "round": "a",
 "slug": "simplify-canary",
 "state": "FINAL",
 "repo": "ulfe-lmi/slaif-asset-reservation",
 "base_branch": "main",
 "base_sha": "14fc20b1ff52788974fd3f282322afc9d71362f9",
 "issue_number": 29,
 "branch": "codex/29-oap-015-a-simplify-canary",
 "pr_mode": "CREATE_OR_RESUME",
 "pr_number": null,
 "previous_round": null,
 "provenance": [
  {"marker": "H", "source": "in-session human principal instruction (Janez Pers), 2026-09-14", "section_or_evidence": "directive to simplify the merged Concentrated OAP conversion to the smallest understandable orchestration layer, five-point proposal, and explicit approval of one bounded first PR; dependency-security failure declared out of scope with truthful-status obligation and no-waiver"},
  {"marker": "A", "source": "oap/strategic-instructions/OAP-COMMUNICATION-strategic.md", "section_or_evidence": "OP-02 objective/issue/PR identity; OP-03 order format; OP-04 two recoverable writes; OP-05 FIFO framing; OP-09 PR-before-report; OP-10 report verification; OP-11 merge gate"},
  {"marker": "E", "source": "remote CI at base 14fc20b1ff52788974fd3f282322afc9d71362f9", "section_or_evidence": "run 34783895298: quality PASS, test PASS, container PASS, security FAIL in uv run pip-audit (20 known vulnerabilities: django 5.2.15, djangorestframework 3.16.1, pip 26.1.2, sqlparse 0.5.5) — pre-existing baseline, out of scope, no waiver"},
  {"marker": "I", "source": "oap/strategic-instructions/initial-orders/015-a-concentrated-oap-round-trip-canary.md", "section_or_evidence": "DRAFT 015-a reconciled by strategy 2026-09-14: scope widened from canary-document-only to the approved simplification PR whose round-trip canary test proves the simplified path; drafts 016-a..020-a unchanged"},
  {"marker": "C", "source": "installed strategic constitution (AGENTS.md)", "section_or_evidence": "S-04 preserve product; S-05 architecture stewardship; S-12 order content; S-13 publication/serialization; S-16 exact-head review; S-17 development merge blocked (delegation disabled, human merge)"}
 ],
 "requirements": ["SAR-033", "SAR-034", "SAR-035", "SAR-037", "SAR-038"],
 "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
 "source_hashes": {
  "PLAN.md": "d5677519a1546906eca644cb5be34a93f038a73fa20d6ba241cfdd0add6b9ef6",
  "ARCHITECTURE.md": "9e7c60e4ef6cee99d5baf20ee5ef6afcff38b10aa2eaa74a5a27084ff515a0c4",
  "CRITICAL.md": "f5c4d78ed599ac9a8ce44687925dab29f221d8b65a2350a4f858c9f32a92c672",
  "oap/strategic-instructions/AGENTS.md": "c08e07bf6b5719682079e2d8571b2a8b66f25a0d0ba81fd3b677ef45ee501cc7",
  "oap/strategic-instructions/OAP-COMMUNICATION-strategic.md": "e6d82a39f30c170ab58603991c89472e04d5b0dc9814d794a9cd303c6290bfa0",
  "oap/strategic-instructions/initial-orders/015-a-concentrated-oap-round-trip-canary.md": "2c33df6924ff21bd903fe5d72557172630b639dcf7bbe26821ca01efcc76c107",
  "oap/RECOVERY.md": "6e91b07f21d14e0889215dfe9c5328343b5210393b0747935c52aa4a2e5ac186"
 },
 "allowed_paths": [
  ".github/workflows/ci.yml",
  ".github/workflows/oap.yml",
  "MANIFEST.sha256",
  "TESTING.md",
  "oap/README.md",
  "oap/COMPLETENESS.md",
  "oap/bootstrap-sources.lock.json",
  "oap/bin/bootstrap-two-agent-oap.sh",
  "oap/bin/check_governance.py",
  "oap/bin/oap_doctor.py",
  "oap/bin/oap_materialize.py",
  "oap/bin/oaplib.py",
  "oap/bin/publish_order.py",
  "oap/bin/verify_report.py",
  "oap/coding-instructions/TESTING-CORE.md",
  "oap/governance/",
  "oap/audit/",
  "oap/templates/STRATEGIC-REVIEW-CHECKLIST.md",
  "oap/templates/HANDOFF-TEMPLATE.md",
  "oap/orders/015-a-simplify-canary.md",
  "oap/active",
  "oap/reports/015-a-simplify-canary.md",
  "docs/OAP-RUNBOOK.md",
  "docs/audit/",
  "docs/bootstrap/archive/",
  "tests/oap/"
 ],
 "forbidden_resources": [
  "product application code under src/, migrations, data/, and product test files outside tests/oap/",
  "dependency or tooling version changes (pyproject.toml, uv.lock)",
  "production databases, real lab/Neumann machines, real SmartScheduling data",
  "credentials, auth files, sessions, tokens, auth homes, or copied private exports",
  "DNS/TLS/firewall changes, public exposure, repository visibility or branch-protection changes",
  ".github/workflows files other than ci.yml and the new oap.yml",
  "merging or auto-merging any PR, approving checks, or any GitHub settings change",
  "model provider endpoints other than the configured qwen-neumann role profile"
 ],
 "decision_class": "D0",
 "expected_report_path": "oap/reports/015-a-simplify-canary.md",
 "tests": [
  "python3 -m unittest discover -s tests/oap -p 'test_*.py' -v",
  "python3 oap/bin/check_state.py --repo <actual> --strategic-home <actual>",
  "python3 oap/bin/verify_report.py --repo <actual> --id 015-a --pr <actual> --head <actual report head> --remote origin",
  "CI at the exact reviewed head: quality, test and container must PASS; security must show only the identical pre-existing pip-audit findings of main run 34783895298 (no dependency changes in this PR, no new findings)"
 ],
 "target_gate": "M-CONVERSION round-trip canary: strategic exact-head review plus round-trip canary evidence; development-merge delegation remains disabled so the human merges; ICA at exact merged revision and human M-CONVERSION acceptance remain separate gates"
}
-->

# 015-a — Simplify the Concentrated OAP orchestration layer (round-trip canary)

## Goal

One bounded, governance-only PR that shrinks the merged OAP conversion to the
smallest understandable orchestration layer, and proves the simplified
normal round end to end with a real round-trip canary test. The executed round
itself is the M-CONVERSION round-trip canary: it is published, consumed,
implemented, reported and reviewed through the simplified path. No product
behavior changes.

## Durable provenance and requirements

See OAP-META provenance (H/A/E/I/C) and requirements SAR-033, SAR-034, SAR-035,
SAR-037, SAR-038. The human approved the exact change set on 2026-09-14 in
session; this order fixes it.

## Current reconciled state and prerequisites

- Base main, local and remote: 14fc20b1ff52788974fd3f282322afc9d71362f9
  (WO0014 conversion adoption, PR #28, human-merged).
- Activation enabled for M-CONVERSION; target milestone 015-a; development
  merge delegation DISABLED (merge side effects not evidenced); ICA audit model
  unqualified. This PR is human-merged; coding never merges.
- No active pointer before this order; oap/orders and oap/reports empty; no
  prior round exists for this objective. Issue #29 created by strategy as the
  objective anchor (one objective = one issue = one branch/PR).
- Pre-existing security baseline (truthful, out of scope, no waiver): CI run
  34783895298 at this base — quality/test/container PASS, security FAIL in
  uv run pip-audit with 20 known vulnerabilities (django 5.2.15,
  djangorestframework 3.16.1, pip 26.1.2, sqlparse 0.5.5). This PR changes no
  dependencies. The security job is expected to keep failing with the same
  findings; that is reported, not fixed, not waived.

## Ordered read set

Standard compact read set (root router AGENTS.md ->
oap/coding-instructions/AGENTS.md -> ARCHITECTURE-for-agents.md ->
OAP-COMMUNICATION-coding-agent.md -> this order -> SECURITY-CORE.md +
TESTING-CORE.md), plus only the ordered excerpts of the files named in Scope
below. No full-source dumps.

## Scope and allowed paths

Exact changes (the approved proposal, §3):

1. .github/workflows/ci.yml: remove the sha256sum -c MANIFEST.sha256 step and
   the oap harness step from the quality job.
2. New .github/workflows/oap.yml: separate oap-harness job running
   python3 -m unittest discover -s tests/oap -p 'test_*.py' -v, path-gated to
   oap/, tests/oap/ and the workflow file itself (pull_request and push
   triggers).
3. oap/bin/oaplib.py + oap/bin/publish_order.py: slim the final order schema
   to exactly 10 fields — id, round, base_sha, issue_number, branch,
   pr_mode, previous_round, allowed_paths, forbidden_resources, DHA body
   declaration — keeping the two recoverable writes, dry-run zero-write,
   pointer atomicity and role/activation guards. The slim parser must accept
   already-published superset orders (including this 25-field order) as valid.
4. oap/bin/verify_report.py: reduce verification to exactly three checks —
   report-only changed path, literal implementation head as first parent,
   exact remote head plus PR/branch identity.
5. oap/bin/oap_doctor.py: keep structural and operational dimensions only
   (activation, pointer sanity, no foreign/conflicting state); remove the
   governance-identity and adoption dimensions. The operational gate must
   still block on merge side effects (not evidenced) and unqualified audit
   model.
6. Delete and move, byte-identical, into docs/bootstrap/archive/ (single
   archive commit note acceptable): MANIFEST.sha256, oap/governance/MANIFEST.json,
   oap/bootstrap-sources.lock.json, oap/governance/DISTILLATION-MAP.md,
   oap/governance/CONTEXT-BUDGET.md, oap/bin/check_governance.py,
   oap/bin/oap_materialize.py, oap/bin/bootstrap-two-agent-oap.sh,
   oap/COMPLETENESS.md, oap/templates/STRATEGIC-REVIEW-CHECKLIST.md,
   oap/templates/HANDOFF-TEMPLATE.md.
7. Move oap/audit/ (ICA protocol, templates, draft requests) to docs/audit/;
   oap/bin/check_ica.py stays in oap/bin (milestone-use, off the normal path).
8. tests/oap: per file, delete BA test files whose sole subject is removed
   machinery (candidate set ba00-ba15, ba38_39, ba46_48; trim ba42_45 to the
   surviving no-self-merge assertion), and update the surviving suites to the
   slim schema where they encode the old 25-field order shape. Keep the suites
   covering: state, orders, publish, fifo, wrapper, report, DHA, privacy,
   continuity. Remove fixture_digests entries that only pin deleted files.
9. New tests/oap/test_roundtrip_canary.py — the simplified round-trip
   acceptance test (fixture repo, explicit fake remote/client adapters, real
   temp POSIX FIFOs, finite timeouts; the content is specified in acceptance
   criterion 8).
10. Docs updated to the slim round with no stale references to removed files:
    oap/coding-instructions/TESTING-CORE.md (remove the manifest step from
    TC-04), TESTING.md, oap/README.md (layout and first-operational-round
    state), docs/OAP-RUNBOOK.md (slim round, installed-home refresh via one
    git show <rev>:path line, recovery pointer to oap/RECOVERY.md).
11. This order's exact bytes (oap/orders/015-a-simplify-canary.md), the
    oap/active pointer and the final report bytes are part of the round as
    before.

Everything else is protected. In particular: nothing under src/, data/,
migrations, product tests outside tests/oap/, pyproject.toml, uv.lock,
SECURITY.md, ARCHITECTURE.md, ARCHITECTURE-for-agents.md, PLAN.md,
CRITICAL.md, oap/strategic-instructions/, oap/coding-instructions/AGENTS.md,
oap/coding-instructions/SECURITY-CORE.md, oap/prompts/, oap/templates/
(surviving), oap/bin/oap_launch.py, oap/bin/oap_fifo.py, oap/bin/check_state.py,
oap/bin/append_critical.py, oap/RECOVERY.md.

## Non-goals

- No product behavior, API, data, migration, dependency or documentation-of-product change.
- No dependency upgrade or any repair of the pre-existing pip-audit failure;
  it stays red and reported until a separate human-directed action.
- No merge, auto-merge, check approval or repository settings change by coding.
- No authority expansion, active-order rewriting, DHA invention or visibility change.
- No real deployment, credentials, private data or lab access; no new gateway,
  OIDC, monitoring, public API surface.
- No renumbering of historical WOs, drafts 016-a..020-a or ID sequence.

## Numbered acceptance criteria

1. Product bytes unchanged: the complete base-to-head diff touches only the
   allowed paths; zero changes under src/, data/, migrations, product tests
   outside tests/oap/, pyproject.toml or uv.lock.
2. MANIFEST.sha256 deleted from the repository root with every reference
   removed (ci.yml, TESTING.md, TESTING-CORE.md, archive note); no manifest
   regeneration.
3. The product CI quality job no longer runs the oap harness; the new
   oap.yml job runs it path-gated; quality job steps otherwise unchanged.
4. The slim order schema has exactly the 10 fields listed in Scope 3, enforced
   by the publisher; the slim parser accepts this 25-field order as a valid
   superset (verified by a surviving test).
5. Report verification is exactly the three checks in Scope 4 and passes for
   this round on the real remote.
6. oap_doctor.py keeps structural and operational dimensions and still blocks
   operational launch on merge side effects (not evidenced) and unqualified
   audit model; governance-identity and adoption dimensions are gone.
7. Every file deleted in Scope 6 exists byte-identical under
   docs/bootstrap/archive/; oap/audit/ content exists byte-identical under
   docs/audit/; check_ica.py remains in oap/bin and still validates an ICA
   request fixture.
8. tests/oap/test_roundtrip_canary.py passes and proves, on a fixture repo
   with explicit fake adapters and a real temp FIFO: (a) publish dry-run
   performs zero writes; (b) real publication creates the immutable order then
   the exact ID+LF pointer; (c) one control OK consumes exactly one wake-up
   and launches exactly one fresh coding context; (d) the fake coding round
   commits order/pointer bytes, opens the PR before report composition, and
   appends a report-only commit with the literal implementation head as first
   parent; (e) verify_report passes; (f) check_state traces the state
   PUBLISHED to REPORT_PUBLISHED to inactive after pointer clear; (g) a
   duplicate wake-up reconciles and suppresses a second launch.
9. The surviving tests/oap suite passes fully (state, orders, publish, fifo,
   wrapper, report, DHA, privacy, continuity) against the slim schema; deleted
   BA files are gone and no test references a removed helper.
10. Documentation (Scope 10) matches the slim round; oap/README.md names this
    round as the first operational round and the round-trip canary.
11. The final report records actual measured canary evidence: wrapper
    single-consumption observation, exact FIFO OK bytes, real PR number,
    literal implementation head, report-head CI marked not-yet-observed at
    authoring, and the truthful pre-existing security baseline.

## Verification

- python3 -m unittest discover -s tests/oap -p 'test_*.py' -v (local, owned
  fixtures, finite timeouts; not-run or blocked limits stated truthfully).
- python3 oap/bin/check_state.py against repo and strategic home.
- python3 oap/bin/verify_report.py with actual PR and report head, real remote.
- CI at the exact reviewed head: quality, test and container must PASS.
  Security must show only the identical pre-existing pip-audit findings of
  main run 34783895298; any new finding or dependency change is a failure of
  this round. The pre-existing red state is reported truthfully and remains
  open; no waiver is implied.
- Strategy then performs the exact-head review: full diff, ordered scope,
  strongest concrete reason not to merge, combined risk, four jobs at the
  exact head, and the human merge.

## Negative paths

- Do not deliberately corrupt the real remote, FIFO or pointer to prove
  recovery; recovery semantics remain covered by the surviving fixture tests.
- If PR publication is blocked: retain truthful local evidence, emit no
  completion signal, never fabricate a PR/report remote identity.
- No regeneration of MANIFEST.sha256; no re-adding of removed helpers; no
  silent restoration of removed BA tests.
- No self-merge, auto-merge, check approval or protection bypass at any step.

## Documentation

Scope 10 documents plus this immutable order and the final immutable report.
No README production-status claim; no product documentation change.

## Recovery

Interrupted round: same ID 015-a, same branch codex/29-oap-015-a-simplify-canary,
same issue #29 and PR; resume does not renumber or duplicate. Preserve all
durable state; oap/RECOVERY.md state machine and check_state.py govern. A
lost response after remote report means strategic review, never rerun.

## Deferred human adjudication

- Decision: NONE

## Publication and reporting

PR created before report composition; literal implementation head; report-only
first-parent commit; Report publication commit SELF; truthful separation of
implementation-head CI from report-head CI; remote verification receipt; exact
two-byte response OK; then no further mutation this round. Coding never
merges. Strategy review and the M-CONVERSION target gate remain independent
of this report.
