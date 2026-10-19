<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "053-a",
  "order_path": "oap/orders/053-a-authorization-audit-publication.md",
  "order_sha256": "649f43d9ec27cf898e3ec4e74d7b799aaaa1a5215bdaf5343a3de15239caac4a",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 109,
  "pr_number": 110,
  "branch": "codex/109-oap-053-a-authorization-audit-publication",
  "implementation_head": "a06ff983c4bf1264f20ef53be788051624cf236e",
  "base_sha": "bddda89a5ddb428c64a36c7c2bd1f35cab2acbba",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "a06ff983c4bf1264f20ef53be788051624cf236e",
    "runs": [
      {
        "run_id": 39186120497,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "security": "success",
          "container": "success",
          "test": "success"
        }
      },
      {
        "run_id": 39186120550,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ],
    "test_job_summary": "1254 passed, 1 warning in 572.62s (0:09:32)",
    "warning": "tests/test_product_entry.py:568 UserWarning: Overriding setting DATABASES can lead to unexpected behavior (pre-existing, intentional DB-unavailable negative test, unrelated)",
    "oap_harness_summary": "Ran 160 tests in 31.721s / OK (job success)"
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 053-a — execution report: publish current authorization audit and documentation state

Implementation head SHA: a06ff983c4bf1264f20ef53be788051624cf236e
Report publication commit: SELF

## Identity and result

COMPLETE for order 053-a (D0, `Decision: NONE`) on issue #109 / PR #110 /
branch `codex/109-oap-053-a-authorization-audit-publication`, base main
`bddda89a5ddb428c64a36c7c2bd1f35cab2acbba` (verified equal to
`origin/main` before editing; all 14 order base source hashes verified
against working-tree bytes; governance revision
`14fc20b1ff52788974fd3f282322afc9d71362f9` present in history). PR #110 was
created with `Closes #109`; no merge, self-approval or auto-merge was
performed. The order file (`oap/orders/053-a-authorization-audit-publication.md`,
state FINAL, SHA-256
`649f43d9ec27cf898e3ec4e74d7b799aaaa1a5215bdaf5343a3de15239caac4a`) and the
`oap/active` pointer (exact `053-a` + LF) were committed with the
implementation work as the order's allowed paths. Single implementation
commit `a06ff983c4bf1264f20ef53be788051624cf236e` (implementation head,
first parent the audited base `bddda89a5ddb428c64a36c7c2bd1f35cab2acbba`).

The order's one purpose — publish the FROZEN fresh independent full-53 ICA
at the exact merged base and align canonical/user/operator documentation
with the already-implemented authorization boundary — is complete. The
auditor result is software/synthetic 53-IMPLEMENTED closure evidence
presented for HUMAN milestone judgment; nothing here claims human
acceptance, release, deployment or real exposure.

## Numbered acceptance evidence

### 1. Publish exact independent report — PASSED

`~/codex-work/slaif-auth-ica-7d85666bc6/recheck/REPORT.md` was copied
BYTE-IDENTICALLY (`cmp` clean) to
`docs/audit/reports/M-GROUP-AUTHORIZATION-bddda89.md`; SHA-256 of the
published file is exactly
`574024e2511af121f4665a89fa53cdfd0eefb12c816e82697ed2b9f724cd4177`.
Actual command:
`python3 oap/bin/check_ica.py --repo . --file docs/audit/reports/M-GROUP-AUTHORIZATION-bddda89.md --kind report --requirements-json ~/codex-work/slaif-auth-ica-7d85666bc6/recheck/input/requirements.json --json`
returned `ok: true` (PASS-STRUCTURAL-ONLY): human_scope, architecture_hash,
architecture_hash_current (current full-architecture digest
`4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd` is
referenced in the report), exact_revision (`Audited revision:
bddda89a5ddb428c64a36c7c2bd1f35cab2acbba`), requirement_matrix_complete
(all 53 SAR IDs from the requirements inventory re-derived dynamically,
missing list empty), classifications_present, auditor_provenance,
negative_paths, findings_section and structural_only_disclaimer all ok.
No matrix drift, no forged model identity (the report itself asserts no
observable provider/model variant) and no substantive self-certification —
the validator is structural only. The prior failed ICA
`docs/audit/reports/M-GROUP-AUTHORIZATION-1adf776.md` was re-verified
unchanged at SHA-256
`7b03025c4a4f2757b5a0d2e252878ed5f236594bdc2953e2bb57dd40a28c43f1` with its
48/5 failed closure intact (re-hashed before and after the publication
commit; not staged, not modified). Raw private audit logs, probes,
one-time tokens, credentials and screenshot files remain outside Git; the
published report carries its complete inline 53-row matrix.

### 2. Specialist state current without a product ledger — PASSED

`PLAN.md` P-08 retains the original human selection (2026-10-17, request
sections 1–11), the stable rows SAR-048–SAR-053, the deferral
reconciliation, the original purpose map table as labelled history and the
prior failed ICA record verbatim. The `Current state` heading and the 052
entry now record the fresh exact `bddda89` full-53 assessment (53
IMPLEMENTED, 0 PARTIAL/ABSENT/UNPROVEN, no mandatory finding) with links to
the published report and its freshness record, and state that the
software/synthetic closure evidence supports presentation to HUMAN
milestone judgment only — no HUMAN milestone acceptance, real
deployment/exposure, DNS/TLS/firewall, identity/secret administration,
private/lab data access or release is inferred. `docs/README.md` keeps the
task-oriented Start/Users/Operators/Developers sections first; its
Governance/history section now points to the current group-authorization
audit and freshness, with the Internet/UX audit and the failed
group-authorization closure explicitly historical/specialist. No audit
counts were promoted into README as product marketing.

### 3. Current user/operator/API/security wording — PASSED

- `docs/authorization.md` first screen now states the Book/exact-asset,
  management and read-all group/token controls are IMPLEMENTED and names
  the fresh full-53 ICA at `bddda89` (software/synthetic scope) — no stale
  all-UNPROVEN/pending-fresh-ICA claim. The complete permission matrix,
  example groups, migration/setup instructions and bearer/external-enforcer
  contract are preserved. The Admin-vs-staff statement was corrected: a
  current active human staff session is also required by the legacy
  staff-session asset list/detail API and, when enabled, the private
  schema/docs endpoints; staff status or unrelated Administration
  permissions alone still confer no /manage/, no `book_assets`, no
  read-all and no protected/domain bypass, and per-model Administration
  permissions stay separate. Source-verified against
  `src/slaif_reservation/api/permissions.py`
  (`IsActiveStaffHuman.has_permission` = `is_active_human(user) and
  bool(user.is_staff)`, `is_active_human` = authenticated + active +
  non-service-account), `src/slaif_reservation/assets/api.py`
  (`AssetListAPIView`/`AssetDetailAPIView` `permission_classes =
  [IsActiveStaffHuman]`) and `src/slaif_reservation/config/urls.py`
  (`ApiDocumentationPermission` falls back to `IsActiveStaffHuman` when
  `API_DOCS_PUBLIC` is off).
- `docs/api-contract.md` names the current active human staff session for
  the legacy asset reads (Principles bullet and scope section), keeps the
  bearer `assets:read` refusal of those endpoints, and removes the obsolete
  `Work Order 0006 uses:` lead-in (replaced by `Current scope usage:`).
- `docs/security-model.md` describes the same staff-read/private-doc
  boundary and distinguishes the two authorized cross-user read surfaces —
  the session-based All reservations browser under /manage/ and the
  separate dual-gated minimal read-all bearer surface — replacing the
  incorrect "bearer is the only cross-user read exception" paragraph.
- `README.md` capability/API-doc entries now read `current active human
  staff session` for the asset list/detail endpoints and the private
  schema/docs; production docs remain described as disabled by default.
  The product-first first-100 lines were re-read as a new user: no
  `Work Order 000`/historical SHA ledger or OAP chronology near the top.
  No operational command, deployment assumption or trust topology was
  changed.

### 4. Source/evidence freshness explicit — PASSED

`docs/audit/qualification/M-GROUP-AUTHORIZATION-FRESHNESS.md` records the
exact audited base `bddda89a5ddb428c64a36c7c2bd1f35cab2acbba`, the full
current architecture digest
`4566e797b709b71f13b2929572a2d1145d15a5a7ab8b41db50ebfdab962628cd`, the
projection digest `41c32e0b0d6427a173dfe0b722446ae8ee311f3880929db65ed0245309b3a59e`,
the ICA report digest
`574024e2511af121f4665a89fa53cdfd0eefb12c816e82697ed2b9f724cd4177`, the
selected human scope/public-development authority (with the explicit human
authorization of public-repository development publication/merges, and no
visibility/protection change by this publication) and the original failed
report. The actual audited-base-to-implementation diff
(`git diff --name-only bddda89... HEAD`) contains ONLY the ordered
docs/evidence/pointer paths: `PLAN.md`, `README.md`, `docs/README.md`,
`docs/api-contract.md`, `docs/authorization.md`, `docs/security-model.md`,
`docs/audit/reports/M-GROUP-AUTHORIZATION-bddda89.md`,
`docs/audit/qualification/M-GROUP-AUTHORIZATION-FRESHNESS.md`,
`oap/active`, `oap/orders/053-a-authorization-audit-publication.md` (10
files, +408/−31). `git diff --name-only bddda89... HEAD -- src/ tests/
pyproject.toml uv.lock manage.py Dockerfile .dockerignore data/
compose*.yaml deploy/ .github/ ARCHITECTURE.md ARCHITECTURE-for-agents.md
CONTRIBUTING.md QUICKSTART.md INSTALL.md SECURITY.md` returned EMPTY: all
application source, tests, lockfile, Dockerfile/.dockerignore and every
Docker COPY input (`pyproject.toml`, `uv.lock`, `manage.py`, `src/`,
`data/bootstrap/`), deployment/config/runtime/workflow bytes and the full
architecture/projection are byte-identical to the audited revision. Product
runtime behavior, authorization rules and normative deployment assumptions
are unchanged; the new active-human staff and separate read-surface prose
explains already-audited, already-enforced behavior. No future merged
publication SHA is invented in any committed document; strategy will
assess the actual post-merge diff/head and record one exact immutable
post-publication candidate after merge.

### 5. One clean PR, focused checks, full CI — PASSED (CI observed; see below)

Every new/changed local Markdown link and anchor was checked across the 8
changed/new Markdown files (relative file targets and in-document anchors,
including the staff permission matrix
`docs/authorization.md#management-route-inventory-enforced`, the read-all
dual-gate anchor and all audit links): all resolve. `git diff --check`
passed (no whitespace errors). Both frozen report hashes re-verified
unchanged at commit time. Focused doc/static checks only were run locally
(link/anchor checker, `git diff --check`, `git diff` scope/neutrality,
`sha256sum`/`cmp` byte checks, `check_ica.py`, README first-100 review);
NO local full pytest/browser/OAP/operational/rehearsal/HTTPS/Gunicorn/
restore sweep was run. Full normal FIVE CI checks at the exact frozen
implementation head `a06ff983c4bf1264f20ef53be788051624cf236e` (CI run 39186120497: quality, test, security, container; OAP run 39186120550: oap-harness) observed completed/success at authoring, no missing/pending/skipped/cancelled. PR #110 body is product/qualification-first with
`Closes #109`; no self-approval or merge/auto-merge was performed or
enabled. Implementation head commits only ordered docs/pointer/order
files; this immutable report is the final commit with the implementation
head as first parent and changes only this report file.

## Commands and results (actual)

- `git fetch origin && git rev-parse origin/main main` — both
  `bddda89a5ddb428c64a36c7c2bd1f35cab2acbba` (base verified before edit).
- 14 order base source hashes vs working tree (`sha256sum`) — all MATCH.
- `sha256sum ~/codex-work/slaif-auth-ica-7d85666bc6/recheck/REPORT.md` —
  `574024e2511af121f4665a89fa53cdfd0eefb12c816e82697ed2b9f724cd4177`
  (MATCH order).
- `cp` + `cmp` to
  `docs/audit/reports/M-GROUP-AUTHORIZATION-bddda89.md` — BYTE-IDENTICAL;
  published file re-hashed `574024e2…` (MATCH).
- `python3 oap/bin/check_ica.py --repo . --file docs/audit/reports/M-GROUP-AUTHORIZATION-bddda89.md --kind report --requirements-json ~/codex-work/slaif-auth-ica-7d85666bc6/recheck/input/requirements.json --json`
  — ok=true (10/10 structural checks; 53/53 SAR rows present).
- `sha256sum docs/audit/reports/M-GROUP-AUTHORIZATION-1adf776.md` —
  `7b03025c4a4f2757b5a0d2e252878ed5f236594bdc2953e2bb57dd40a28c43f1`
  (MATCH, before and after; file untouched).
- Link/anchor checker over the 8 changed/new Markdown files — OK (0
  missing files/anchors).
- `git diff --check` — clean.
- `git diff --name-only bddda89… HEAD` (and the source-neutrality path
  filter above) — only ordered paths; EMPTY for all source/build/test
  paths.
- `grep` of README first 100 lines for work-order/OAP/SHA-ledger terms —
  no hits (product-first preserved).
- `gh pr create` — PR #110 created (`Closes #109`), no merge performed.
- `gh run watch 39186120497 / 39186120550 --exit-status` at head
  `a06ff983c4bf1264f20ef53be788051624cf236e` — both watches exited 0; all five jobs completed/success at the literal head.

Not run (by order scope): local product/browser/OAP-harness/operational/
rehearsal/HTTPS/Gunicorn/restore sweeps, any destructive cleanup, any real
host/service/DNS/TLS/identity/secret action — none authorized by this
order.

## Implementation CI (observed at authoring, exact head)

All five required checks at exact implementation head `a06ff983c4bf1264f20ef53be788051624cf236e`, observed completed/success at authoring:

- CI run 39186120497: `quality` success, `test` success (1254 passed, 1 pre-existing warning in 572.62s), `security` success, `container` success.
- OAP run 39186120550: `oap-harness` success (160 tests, OK).

The report commit lands after this observation; its own head checks are NOT YET OBSERVED AT AUTHORING and are not claimed here.

## Report-head CI

NOT YET OBSERVED AT AUTHORING. No report-head check result is claimed; the
post-publication checks at the report commit are reported only in the
private execution receipt and do not amend this immutable report.

## Privacy, dependencies, DHA, limits

No tokens, peppers, verifiers, passwords, Authorization/cookie/CSRF
material, raw requests, private exports, free text or physical locators
entered this report or any committed artifact; the published ICA report
contains no credential material (auditor-attested). No new dependency,
migration, workflow or repository setting. DHA: NONE — the order's
`## Deferred human adjudication` declares `Decision: NONE` and no CRITICAL
entry was appended or adjudicated. Strongest limitation: the 53-row
software/synthetic closure could be misread as production/public-exposure
certification; it is scoped to software/development with disposable
synthetic qualification, bound to revision `bddda89`, and explicitly not
human acceptance, release or deployment authority. Pending human
judgments: M-GROUP-AUTHORIZATION milestone acceptance and all real D2
deployment decisions (host/proxy trust, DNS/TLS/firewall, identities/
secrets, private data, physical allocation) remain with the human.

## OAP-META note

The OAP-META block above carries the actual order path/SHA, issue/PR/branch,
implementation head, base SHA, result and the observed implementation CI
runs; `Report publication commit: SELF` resolves to the containing
report-only commit (first parent
`a06ff983c4bf1264f20ef53be788051624cf236e`, changing only this file).
