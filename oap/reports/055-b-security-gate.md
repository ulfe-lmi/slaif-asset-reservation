<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "055-b",
  "order_path": "oap/orders/055-b-security-gate.md",
  "order_sha256": "f32e231b64eca766bb2268091f721466b29cfdbbf8aea7180973c3a9d38caa19",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 114,
  "pr_number": 115,
  "branch": "codex/114-oap-055-a-account-onboarding-contract",
  "implementation_head": "308f3b390d813d7316454051a769f98222134987",
  "base_sha": "1eade24e2032b8525d3b0151daaca38830e24d03",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "308f3b390d813d7316454051a769f98222134987",
    "runs": [
      {
        "run_id": 42879385729,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "test": "success",
          "security": "success",
          "container": "success"
        }
      },
      {
        "run_id": 42879385782,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ],
    "test_job_summary": "1300 passed, 1 warning in 612.67s (0:10:12)",
    "warning": "tests/test_product_entry.py:568 UserWarning: Overriding setting DATABASES can lead to unexpected behavior (pre-existing, intentional DB-unavailable negative test, unrelated)",
    "oap_harness_summary": "Ran 160 tests in 29.139s - OK"
  },
  "observed_prior_055a_ci": {
    "implementation_head": "81b68e3f8af435d8af9fc8c07e3865372d811fd2",
    "report_head": "6cb7ca14334bede2b247c1289641a349284c05ae",
    "implementation_runs": [
      {"run_id": 42864895997, "workflow": "CI", "jobs": {"quality": "success", "test": "success", "security": "failure", "container": "success"}},
      {"run_id": 42864896508, "workflow": "oap", "jobs": {"oap-harness": "success"}}
    ],
    "report_runs": [
      {"run_id": 42869237878, "workflow": "CI", "jobs": {"quality": "success", "test": "success", "security": "failure", "container": "success"}},
      {"run_id": 42869237777, "workflow": "oap", "jobs": {"oap-harness": "success"}}
    ],
    "note": "All four 055-a runs terminal; both security failures are the same 13-advisory pip-audit finding on the unchanged 055-a lockfile, repaired by this round."
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 055-b — execution report: repair security CI without broadening the product

Implementation head SHA: 308f3b390d813d7316454051a769f98222134987
Report publication commit: SELF

## Identity and result

COMPLETE for order 055-b (D0, `Decision: NONE`), a correction (AMEND) round on
objective 55 reusing issue #114 / PR #115 / branch
`codex/114-oap-055-a-account-onboarding-contract`, exactly as ordered. Before the
first write, all seven order `source_hashes` were verified
SHA-256-byte-identical (ARCHITECTURE.md `5ad0ab63...`, PLAN.md `f69a1a0c...`,
ARCHITECTURE-for-agents.md `3d1d618c...`,
docs/governance/ACCOUNT-ONBOARDING-PROJECTION-REVIEW.md `e6b55aa3...`,
README.md `e920cb6d...`, pyproject.toml `033a5cab...`, uv.lock
`7b4c1891...`); governance revision `14fc20b1ff52788974fd3f282322afc9d71362f9`
is in history; base `1eade24e2032b8525d3b0151daaca38830e24d03` equals the
055-a base and `origin/main`. The single implementation commit
`308f3b390d813d7316454051a769f98222134987` (first parent exactly the 055-a
report-only head `6cb7ca14334bede2b247c1289641a349284c05ae`, preserving the
055-a report-only ancestry) changes exactly the nine allowed paths:
`pyproject.toml`, `uv.lock`, `ARCHITECTURE.md`, `PLAN.md`,
`ARCHITECTURE-for-agents.md`, `README.md`,
`docs/governance/ACCOUNT-ONBOARDING-PROJECTION-REVIEW.md`,
`oap/orders/055-b-security-gate.md` (FINAL, SHA-256
`f32e231b64eca766bb2268091f721466b29cfdbbf8aea7180973c3a9d38caa19`) and the
`oap/active` pointer (exact `055-b` + LF, 6 bytes, verified with `od -c`).
PR #115 was amended (title/body now cover both rounds), not recreated. No
merge, self-approval or auto-merge; foreign PR113 untouched.

## Numbered acceptance evidence

### 1. Exact security finding — PASSED

**055-a five-job outcomes at both exact heads (all terminal, observed this
round):** implementation head `81b68e3f8af435d8af9fc8c07e3865372d811fd2`:
CI run 42864895997 — quality SUCCESS, test SUCCESS, container SUCCESS,
security **FAILED**; oap run 42864896508 — oap-harness SUCCESS. Report head
`6cb7ca14334bede2b247c1289641a349284c05ae`: CI run 42869237878 — quality
SUCCESS, test SUCCESS, container SUCCESS, security **FAILED**; oap run
42869237777 — oap-harness SUCCESS. The 055-a PARTIAL report is preserved
immutable.

**Root cause (CI logs, both heads, identical):** the security job failed at
`uv run pip-audit` with "Found 13 known vulnerabilities in 3 packages":
djangorestframework 3.17.2 — CVE-2026-114136, CVE-2026-114137, CVE-2026-114138
(fix 3.18.2); filelock 3.29.4 — CVE-2026-112907, CVE-2026-112909,
CVE-2026-112910, CVE-2026-112913, CVE-2026-112915, CVE-2026-112935,
CVE-2026-112936 (fix 4.0.9), CVE-2026-112939, CVE-2026-112940 (fix 4.2.1);
msgpack 1.2.1 — CVE-2026-114613 (fix 1.2.3). No advisory was ignored, waived
or masked, and none is attributed to the docs: the 055-a diff touched no
dependency bytes (`git diff base..81b68e3 -- pyproject.toml uv.lock` empty at
that head), so the failure is the externally published advisory set on the
unchanged lock, as the 055-a report recorded.

**Local reproduction before the repair:** `uv sync --locked --all-groups`
(clean) then `uv run pip-audit` on the pre-edit lock reproduced the same 13
advisories in the same three packages (exit 1 in CI; same table locally).

### 2. Bounded dependency repair — PASSED

- `pyproject.toml`: the only dependency-line change is
  `djangorestframework>=3.16,<3.18` -> `djangorestframework>=3.18.3,<3.19`
  (git diff: 1 line).
- `uv lock --upgrade-package djangorestframework --upgrade-package filelock
  --upgrade-package msgpack` resolved exactly three packages:
  djangorestframework 3.17.2 -> **3.18.3** (the order-named fixed line; 3.18.3
  carries the 3.18.2 security fixes plus the follow-up API correction),
  filelock 3.29.4 -> **4.2.10**, msgpack 1.2.1 -> **1.2.4** (exactly the
  order-named fixed version). Programmatic package-table diff of the lock:
  71 packages before and after, zero added, zero removed, and the ONLY changed
  entries are those three. filelock note (honest deviation from the order-time
  expectation): the order's I marker named 4.2.1 as the fixed version at
  drafting; the resolver selected 4.2.10, a later patch in the same fixed line
  (>= 4.2.1, advisory-clean), which is why 4.2.10 is locked. No transitive
  dependency changed, so no resolver-constraint widening occurred.
- `uv sync --locked --all-groups`: PASSED (re-verified at final state).
- `uv run pip-audit` with no ignore/waiver: PASSED — "No known vulnerabilities
  found", exit 0 (re-verified at final state).
- Production image evidence: an isolated `uv sync --locked --no-dev` in a
  throwaway directory (copy of the final pyproject/lock) installs
  djangorestframework 3.18.3 and does NOT install filelock, msgpack,
  cachecontrol or pip-audit — lock/pyproject group-graph evidence that
  filelock/msgpack remain dev-only transitives of pip-audit[filecache]. The
  `docker build` image at this head reports `djangorestframework 3.18.3` via
  in-image `uv pip list`.
- No other dependency family touched; no production dependency added.

### 3. Architecture/doc truth — PASSED

- `ARCHITECTURE.md` (controlled, bounded): A-03 declared stack now reads DRF
  `>=3.18.3,<3.19` (lock authoritative, resolves DRF 3.18.3) and records the
  OAP 055-b (2026-11-10) controlled security-maintenance evolution inside the
  same Django/DRF stack (no domain, protocol, stack or deployment change; the
  SAR-022 no-opportunistic-upgrade discipline applies unchanged); SAR-022 row
  version label DRF3.17 -> DRF3.18. No A/SAR ID added, removed, renumbered or
  otherwise changed; all A-17 selected meaning preserved byte-for-byte.
- `PLAN.md`: exactly the P-03 stack line (Django5.2/DRF3.17 -> DRF3.18); no
  other change.
- `ARCHITECTURE-for-agents.md` recomposed after the full source: header
  full-source SHA-256 refreshed to
  `f7b5c98876a40b052c2d2fe057e57281e917ac5a72508e98caca512c1f0d1286` with the
  pre-055-b identity `5ad0ab63...` preserved as historical provenance; baseline
  stack line (source `>=3.18.3,<3.19`, resolves 3.18.3); SAR-022 row
  (DRF3.18). Diff-verified: every other clause byte-identical, nothing deleted
  or renumbered.
- `docs/governance/ACCOUNT-ONBOARDING-PROJECTION-REVIEW.md`: after-055-b
  canonical/projection/PLAN/README identities recorded with the after-055-a
  identities preserved as historical (including an honest note that the 055-a
  report-time working-tree projection measurement 42676/`f0bc75ec...` differs
  by 2 bytes from the committed after-055-a projection
  42678/`3d1d618c...`); measured routine read set refreshed (projection 42869
  bytes; total 57792 bytes; overage 7792 bytes vs the archived ceiling,
  reported not hidden, disposition strategy-owned); 055-b semantic-comparison
  note (only the header digest/provenance line, baseline stack line and
  SAR-022 row changed; A-17 mapping and all other clauses unchanged);
  accepted-vs-candidate updated (all seven 055-b `source_hashes` verified
  byte-identical before any 055-b write; post-055-b candidate identities
  listed). Committed review byte count: 18911.
- `README.md`: supported-runtime line now "DRF (locked 3.18.3)".
- Markdown links: no link or anchor added or changed by any edit (grep of the
  full diff); every relative link in the five changed Markdown files resolves
  (checked programmatically). `git diff --check` clean, including staged.
- No A-17 onboarding contract weakening; no extra new SAR requirement; no
  unrelated governance change.

### 4. Compatibility and exact heads — PASSED

- Focused + full local suite at the working head against the owned local
  PostgreSQL 17 test database (127.0.0.1:54330, container slaif-054a-pg17),
  sequential, disposable: `uv run --env-file .env pytest --ds=
  slaif_reservation.config.settings.test` => **1290 passed, 9 skipped, 1
  failed** in 757.36s. The 9 skips are local-prerequisite conditional skips
  (Docker/PG-client/Caddy/HTTPS-rehearsal availability on this host); the
  single failure is the documented host-ambient OAP harness test
  `tests/oap/test_ba38_39_tmux_config.py::Ba39OperationPrereqs::
  test_ba39_strategic_same_prerequisites`, which requires the strategic
  role context and fails only while the wrapper's ambient `OAP_ROLE=CODING`
  is set (identical class documented in the 054-b and 055-a reports).
  Re-run of that file with `env -u OAP_ROLE`: **12 passed**. The CI test job
  (no ambient OAP_ROLE) at the exact implementation head is green.
- Quality/type/config at the working head: `uv run ruff check .` (All checks
  passed), `uv run ruff format --check .` (242 files already formatted),
  `uv run mypy src` (Success, 141 files), `uv run --env-file .env python
  manage.py check` (0 issues), `... manage.py makemigrations --check --dry-run`
  (No changes detected — no migration changes).
- Generated OpenAPI: `uv run --env-file .env python manage.py spectacular
  --file build/openapi/schema.yaml --validate --fail-on-warn` PASSED at this
  head, and the generated schema is **byte-identical** to the schema
  generated from the 055-a implementation head `81b68e3...` (DRF 3.17.2) in a
  throwaway worktree — direct evidence that the DRF minor update altered no
  API/auth/schema surface.
- Security job equivalents: `uv run pip-audit` PASSED (no ignore); production
  settings fail-closed negative (`DJANGO_SETTINGS_MODULE=
  slaif_reservation.config.settings.production` + `django.setup()` with no
  operator env) raised `ImproperlyConfigured: SLAIF_DJANGO_SECRET_KEY is
  required`, exit 1, as required.
- Container job equivalents: `docker compose config` OK;
  `deploy/rehearse_internal_alpha_deployment.sh --config-only` OK; production
  compose renders with the app healthcheck including
  `X-Forwarded-Proto: https`; `docker build` succeeded; image USER is
  10001:10001; static/bootstrap files present in the image
  (web/site.css, admin base.css, swagger-ui bundle, data/bootstrap
  assets.yaml + schema.json); image DRF 3.18.3 (see acceptance 2).
- **Normal five CI jobs at the exact implementation head
  `308f3b390d813d7316454051a769f98222134987` — 5/5 SUCCESS (observed, all
  terminal before this report was authored):** CI run 42879385729 — quality
  SUCCESS, test SUCCESS ("1300 passed, 1 warning in 612.67s (0:10:12)"; the
  single warning is the pre-existing `tests/test_product_entry.py:568`
  DATABASES-override UserWarning from the intentional DB-unavailable negative
  test), security SUCCESS, container SUCCESS; oap run 42879385782 —
  oap-harness SUCCESS ("Ran 160 tests in 29.139s - OK").
- **Report-head CI: NOT YET OBSERVED AT AUTHORING** — this report's commit
  does not exist while this report is being written; its five checks are
  recorded in the private execution receipt after publication, and no future
  push/check success is claimed here.
- PR/report mechanics: PR #115 (open, base main, exact branch) amended BEFORE
  this report; after publication the report commit's first parent is the
  implementation head and it changes ONLY
  `oap/reports/055-b-security-gate.md` (verified with
  `oap/bin/verify_report.py`; publication checks go to the private receipt,
  not a report rewrite). No second PR; no merge or auto-merge by CODING.
- All application, migration, Compose/proxy and SMTP behavior is
  byte-identical: `git diff 6cb7ca1..308f3b3 --stat` shows exactly the nine
  allowed files (4 governance docs + README + pyproject + lock + order +
  pointer); nothing under `src/`, `tests/`, `deploy/`, `compose*`, settings or
  migrations changed.

## Uncertainty and limits

- pip-audit's advisory database is time-dependent: the same 055-a lockfile was
  green on 2026-10-21 and flagged by 13 newer advisories by 2026-11-10. The
  locked filelock 4.2.10 is a later patch than the order-time-named fixed
  4.2.1, within the same advisory-clean line (recorded in acceptance 2 for
  strategy review; no behavioral difference expected for a dev-only cache
  lockfile).
- Local suite vs CI suite differ only by environment: 9 local prerequisite
  skips and the 1 ambient-`OAP_ROLE` harness failure (documented, reproduced
  green with the variable unset and green in CI). The CI test job at the exact
  implementation head (1300 passed) is the authoritative full-suite result.
- Report-head CI is NOT YET OBSERVED AT AUTHORING and is not claimed;
  publication verification results belong to the private execution receipt.
  No future push/check success is asserted.
- Tokens are UNMEASURED (no qualified tokenizer for the configured model);
  byte figures are exact UTF-8 bytes.
- This round is a security-maintenance dependency repair plus doc truth; it
  is not an ICA, a release, a deployment or a milestone claim. A-17 /
  SAR-054..SAR-056 remain UNPROVEN selected-target design; a fresh
  exact-revision independent ICA is required before any later
  M-ACCOUNT-ONBOARDING milestone-closure claim, and strategy starts the
  functional member password-change objective (056) after accepted merge.

## Privacy, dependencies and DHA

No credentials, tokens, pepper/verifiers, passwords, Authorization/cookie
material, CSRF tokens, raw request bodies, private exports, physical
locators, auth homes, traces or sidecar artifacts appear in the diff or this
report; no real SMTP account, recipient, relay or credential was contacted or
configured; no production DB, private data, DNS/TLS/firewall, identity
administration or deployment target was touched; foreign PR113 remains
untouched. Dependency change: bounded to the three ordered packages
(djangorestframework 3.18.3, filelock 4.2.10, msgpack 1.2.4) with the DRF
source constraint update; no other package name or version changed, no
dependency family added. DHA: the order declares `Decision: NONE`; no
CRITICAL entry was appended and none was needed.
