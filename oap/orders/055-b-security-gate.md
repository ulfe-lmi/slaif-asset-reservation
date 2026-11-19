<!-- OAP-META
{
  "schema_version": 1,
  "kind": "order",
  "id": "055-b",
  "objective": 55,
  "round": "b",
  "slug": "security-gate",
  "state": "FINAL",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "base_branch": "main",
  "base_sha": "1eade24e2032b8525d3b0151daaca38830e24d03",
  "issue_number": 114,
  "branch": "codex/114-oap-055-a-account-onboarding-contract",
  "pr_mode": "AMEND",
  "pr_number": 115,
  "previous_round": "055-a",
  "governance_revision": "14fc20b1ff52788974fd3f282322afc9d71362f9",
  "source_hashes": {
    "ARCHITECTURE.md": "5ad0ab631696213432c8f513a80b3481fa28a8b0ab89641195ad38725e07db38",
    "PLAN.md": "f69a1a0c52d35abf1f72ee48e25aa3c2fab23fb6470cf298fa2020ad41eea0da",
    "ARCHITECTURE-for-agents.md": "3d1d618cddcd079eefd78c462815ecf6210030508c1834baf306b2e5c1b8568e",
    "docs/governance/ACCOUNT-ONBOARDING-PROJECTION-REVIEW.md": "e6b55aa317e1c458ecc005caa11170f782eb8051b94bd2f4b7c358ab8e608766",
    "README.md": "e920cb6d6c403686982cd8aeeb1a60520063257d6922bbb85d998038b82f458a",
    "pyproject.toml": "033a5cabab0d0bca8ab53675e640dbbe568330095136964e9a5602dec34db16d",
    "uv.lock": "7b4c1891763f5a7667893cd4796fa44f0129a5a212d3249e1a7c00f8aab2dc9a"
  },
  "requirements": ["SAR-014", "SAR-022", "SAR-037", "SAR-038", "SAR-040", "SAR-054", "SAR-055", "SAR-056"],
  "allowed_paths": [
    "pyproject.toml", "uv.lock", "ARCHITECTURE.md", "PLAN.md", "ARCHITECTURE-for-agents.md", "README.md",
    "docs/governance/ACCOUNT-ONBOARDING-PROJECTION-REVIEW.md",
    "oap/active", "oap/orders/055-b-security-gate.md", "oap/reports/055-b-security-gate.md"
  ],
  "forbidden_resources": [
    "No application source, migrations, tests, API/auth/reservation behavior edits or new dependency families; only the three evidenced vulnerable existing packages and necessary DRF constraint/architecture truth may change.",
    "No rewrite of 055-a immutable order/report, prior audit/history, CRITICAL, role law/OAP helper/CI workflow, Gateway source, deploy/Compose/runtime settings or product onboarding implementation. Do not bypass/ignore advisories or alter branch protection.",
    "No real SMTP/recipient/secret, identity administration, host/exposure/DNS/TLS/firewall, production DB, private data, foreign PR113, merge/automerge by CODING."
  ],
  "provenance": [
    {"marker":"H","source":"Human 2026-11-09 request to plan AND implement account onboarding; later explicit urgency to start functional implementation; existing human authorization for development publication/merge in public repository","section_or_evidence":"This same-PR correction is only a mandatory CI/security prerequisite; immediately after accepted merge, strategy starts the member password-change coding objective, no further planning-only PR."},
    {"marker":"A","source":"ARCHITECTURE.md A-03/SAR-022 stable stack, A-17/SAR-054..056 selected target, S-16 exact-head CI gate","section_or_evidence":"Normal CI security and runtime compatibility cannot be waived. DRF remains same framework/major family; a controlled security-maintenance amendment is required because SAR-022 and docs currently name DRF3.17."},
    {"marker":"E","source":"Frozen 055-a implementation 81b68e3f8af435d8af9fc8c07e3865372d811fd2 / report 6cb7ca14334bede2b247c1289641a349284c05ae, issue114/PR115; CI run42864895997","section_or_evidence":"Quality/test/container/oap pass (1300 product/160 harness); security pip-audit FAIL: 13 advisories in DRF3.17.2, filelock3.29.4, msgpack1.2.1 on unchanged base uv.lock. DRF fix >=3.18.2 conflicts current pyproject <3.18; upstream DRF3.18.3 exists, filelock4.2.1 and msgpack1.2.4 available. Report-head checks must be observed before final acceptance. Original 055-a result remains PARTIAL, not rewritten."},
    {"marker":"I","source":"Direct current pyproject/uv.lock and uv tree --invert; official upstream DRF/filelock/msgpack advisories/releases","section_or_evidence":"DRF is production dependency; filelock and msgpack are transitive of pip-audit[filecache] in dev group. Minimal repair is DRF constraint >=3.18.3,<3.19 with locked3.18.3, filelock fixed4.2.1, msgpack fixed1.2.4; any resolver-induced additional change requires evidence and explicit scope review, not silent broad refresh."},
    {"marker":"C","source":"Strategic frozen 055-a whole-diff review; CRITICAL empty; user urgency","section_or_evidence":"D0/DHA NONE: security maintenance within existing framework/runtime, with controlled SAR-022/doc update and full API/product/container regression. Strongest objection: DRF minor update can alter serialization/auth/schema; exact-head full CI and focused API/schema tests are mandatory. No deployment claim."}
  ],
  "decision_class": "D0",
  "target_gate": "Close the existing account-onboarding contract PR security gate, then immediately start functional member password-change objective; no milestone/release/deployment claim",
  "expected_report_path": "oap/reports/055-b-security-gate.md",
  "tests": [
    "Observe and record all five terminal 055-a report-head CI outcomes; preserve prior PARTIAL report immutable.",
    "Change pyproject DRF constraint minimally to >=3.18.3,<3.19; resolve lock for only DRF/filelock/msgpack to nonvulnerable versions. Assert other package versions/names unchanged or report exact resolver necessity before widening. uv sync --locked --all-groups and uv run pip-audit without ignore must pass.",
    "Controlled ARCHITECTURE A-03/SAR-022 maintenance amendment and matching PLAN/projection/README exact locked-version truth; projection digest and semantic review updated after full source. Preserve existing stable requirements and all A-17 selected meaning.",
    "Focused DRF API/auth/schema positive+negative tests and generated OpenAPI validation, plus normal full quality/test/security/container/oap CI at exact implementation and report heads; container image builds, no migration changes, all changed Markdown links and git diff --check."
  ]
}
-->

# 055-b — repair security CI without broadening the product

## Goal

Same issue114/PR115/branch as 055-a, whose frozen doc contract/report is immutable and PARTIAL solely because current pip-audit flags thirteen advisories in three pre-existing locked packages. Repair that mandatory gate with the smallest compatible dependency update, keep the account-onboarding contract accurate, and move directly to functional objective056 after strategy accepts/merges. No additional planning-only round.

## Numbered acceptance

1. **Exact security finding.** Record actual 055-a implementation/report-head five job outcomes, confirm from CI logs and current local pip-audit the DRF3.17.2 / filelock3.29.4 / msgpack1.2.1 findings. No ignore, waiver, disabled security job, base-green inference or false claim that docs caused them. Official DRF release3.18.3 includes 3.18.2 security fixes and a follow-up API correction; filelock4.2.1 and msgpack1.2.4 are fixed versions. Preserve all unrelated package pins where the resolver permits.
2. **Bounded dependency repair.** Update only the direct DRF constraint to `>=3.18.3,<3.19` and resolve only DRF, filelock and msgpack in uv.lock. If a transitive dependency must change, identify its exact resolver constraint and verify compatibility before committing. `uv sync --locked --all-groups` and `uv run pip-audit` must pass. Check that the production image uses the new locked DRF and that filelock/msgpack remain dev-only transitive dependencies unless actual lock evidence says otherwise.
3. **Architecture/doc truth.** The full architecture currently says DRF3.17 is preserved in A-03/SAR-022. Record a small controlled security-maintenance evolution to DRF3.18.3 within the same Django/DRF stack, preserving SAR-022 identity and all domain/security invariants. Update PLAN P-03 if its exact stack statement would be false; recompose compact projection after full source and refresh its source digest; update the account projection review's hashes/measurement/semantic mapping. README's locked DRF version must be current. No A-17 onboarding contract weakening, no extra new SAR requirement or unrelated governance change.
4. **Compatibility and exact heads.** Focused API auth/reservation/availability/schema tests (positive and negative), generated OpenAPI validation, ruff/format/mypy/check/no-migrations/pip-audit, container build, normal five CI jobs at final implementation and report heads. No source/test edit to make the new dependency pass unless strategy explicitly orders it after an actual failure. All application, migration, Compose/proxy and SMTP behavior remains byte-identical apart from dependency behavior. Changed Markdown links/diff clean. Preserve 055-a report-only ancestry and publish one new immutable 055-b report-only child with literal first-parent implementation SHA/SELF. Amend PR115, never create a second PR or merge as CODING.

## Recovery / strongest objection

The 055-a report may be published while its report-head product CI remains pending; wait outside the model for terminal exact-head outcomes before review/activation. Once active, use a fresh CODING context through sourced `codex.sh`, `--yolo --profile early-beta` and the same right-pane wrapper. Preserve all foreign work/PR113 and do not contact real email, host, private data or deployment. Strongest objection is an untested DRF minor upgrade altering API behavior; the full existing API/product suite plus generated schema and container evidence must resolve it before strategic merge. No CRITICAL entry is admitted for this routine fixed-version security repair.

## Deferred human adjudication
- Decision: NONE
