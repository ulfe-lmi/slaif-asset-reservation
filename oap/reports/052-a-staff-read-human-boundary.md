<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "052-a",
  "order_path": "oap/orders/052-a-staff-read-human-boundary.md",
  "order_sha256": "ba3955178af9643548d5dc7fe80b75d3d93bbc00d34a76874452d8e1e7be8829",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 107,
  "pr_number": 108,
  "branch": "codex/107-oap-052-a-staff-read-human-boundary",
  "implementation_head": "69790665a827db9f214f469698048d262387d318",
  "base_sha": "1adf776e553bcd56cd0a7fa229c8eb0bcb56c1fe",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "69790665a827db9f214f469698048d262387d318",
    "runs": [
      {
        "run_id": 39181839836,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "security": "success",
          "container": "success",
          "test": "success"
        }
      },
      {
        "run_id": 39181839809,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ],
    "test_job_summary": "1254 passed, 1 warning in 569.02s (0:09:29)",
    "warning": "tests/test_product_entry.py:568 UserWarning: Overriding setting DATABASES can lead to unexpected behavior (pre-existing, intentional DB-unavailable negative test, unrelated)",
    "oap_harness_summary": "Ran 160 tests in 30.743s / OK (job success)"
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 052-a — execution report: close current-human admission at the four staff read surfaces

Implementation head SHA: 69790665a827db9f214f469698048d262387d318
Report publication commit: SELF

## Identity and result

COMPLETE for order 052-a (D0, `Decision: NONE`) on issue #107 / PR #108 /
branch `codex/107-oap-052-a-staff-read-human-boundary`, base main
`1adf776e553bcd56cd0a7fa229c8eb0bcb56c1fe` (verified equal to
`origin/main` before editing; all order base source hashes verified
against working-tree bytes; governance revision
`14fc20b1ff52788974fd3f282322afc9d71362f9` present). PR #108 was created
with `Closes #107`; no merge, self-approval or auto-merge was performed.
The order file (`oap/orders/052-a-staff-read-human-boundary.md`, state
FINAL, SHA-256
`ba3955178af9643548d5dc7fe80b75d3d93bbc00d34a76874452d8e1e7be8829`) and
the `oap/active` pointer (exact `052-a` + LF) were committed with the
implementation work as the order's allowed paths. Single implementation
commit `69790665a827db9f214f469698048d262387d318` (implementation head).

## Numbered acceptance evidence

### 1. One current-human + staff permission — PASSED

`src/slaif_reservation/api/permissions.py` gains
`IsActiveStaffHuman(BasePermission)`: it returns
`is_active_human(request.user) and bool(request.user.is_staff)`, reusing
the EXISTING `slaif_reservation.web.auth.is_active_human` predicate
(unmoved, unmodified) plus the staff flag — the same combination
`SlaifAdminSite.has_permission` already applies to Administration. No
hardcoded groups or model permissions, no grant checks, no superuser
bypass of service/inactive/staff status, no user caching, no
authentication backend changes. It is used for BOTH staff asset
inventory API classes (`src/slaif_reservation/assets/api.py`,
`AssetListAPIView` and `AssetDetailAPIView` replace
`permission_classes = [IsAdminUser]`) and the PRIVATE branch of
`ApiDocumentationPermission` (`src/slaif_reservation/config/urls.py`).
`HasApiTokenScope` is byte-unchanged. Denial occurs at DRF permission
admission, before serializer/query/filter/detail/schema work.

### 2. Existing contracts preserved — PASSED

The four GET routes are exactly `/api/v1/assets/`,
`/api/v1/assets/<uuid>/`, `/api/schema/` and `/api/docs/` with
`API_DOCS_PUBLIC=False`. Denials are generic DRF 403 bodies with no
private content (asserted per route in the new tests). Active human
staff and trusted active human staff superuser retain old read behavior
(new positive tests; existing staff tests unchanged and green).
Unrelated model or reservations permissions without staff confer no
admission (new `view_all_reservations` + `assets.view_asset` grants
test: 403). Inventory stays SESSION-only: a legitimately issued bearer
token for a staff SUPERUSER carrying `assets:read`,
`availability:read`, `reservations:read` and `reservations:read_all`
still gets 403 on all four routes; no bearer authentication class was
added and no schema field/route/filter/owner/member/read-all interface
changed. Generated OpenAPI is byte-identical to the base
`1adf776` schema (`manage.py spectacular --file` diff empty;
`--validate --fail-on-warn` clean). `API_DOCS_ENABLED` conditional route
registration and default production absence are untouched (no settings
edits); the deliberate explicit local `API_DOCS_PUBLIC=True`
public-metadata policy is preserved (new anonymous 200 positive under
test settings plus the pre-existing `test_api_schema.py` positives).
Admin/member/management behavior is unchanged (existing guard controls
green, criterion 5).

### 3. Durable meaningful regressions — PASSED

New `tests/test_staff_read_eligibility.py` (11 tests, all synthetic
users, legitimately issued token via `issue_api_token`, no global
fixtures/autogrants):

- Main transition proof (real HTTP, `live_server`,
  `transaction=True`): active staff human logs in through actual
  `/login/` with a valid CSRF exchange (never `force_login`), all four
  routes return 200 (asset slug present in the list, `openapi` in the
  schema), then ONLY `is_service_account=True` is changed with the SAME
  session/cookies, and all four return 403 with no asset/schema private
  data; a guessed detail UUID is indistinguishable (same 403, byte-
  identical body). The four REST gates are exercised BEFORE any
  member/Administration page; the Administration redirect control
  (`/admin/login/`) is asserted only afterward.
- Controls: service-account-superuser denial; inactive-staff denial;
  staff-flag removal transition (200 then 403, guessed-UUID parity);
  nonstaff-with-unrelated-grants denial; bearer-only inventory/private-
  docs denial; anonymous denial; active human staff/superuser positives;
  local public-docs anonymous positive.

Negative control of the regression itself: with the three base source
files temporarily restored in the owned execution copy, the main
transition test FAILED at exactly the ICA-GA-001 boundary
(`AssertionError: asset-list — assert 200 == 403` after the service
flag change), then the patched files were re-synced and all 11 tests
passed again. The frozen ICA copy and its database were not modified or
used.

### 4. Canonical status and original failed audit — PASSED

PLAN.md P-08 status-only correction: the original 2026-10-17 selection
is recorded as historical provenance ("selection is not completion"
remains binding); the original purpose table is retained verbatim as a
labelled scope/history map, not future work or a replay queue; the new
Current-state paragraph records purposes 048–051 as delivered at actual
merged evidence (PR100 `12947e9b…`, PR102 `b873f4cf…`, PR104
`3461fa01…`, PR106 `1adf776e…` and the immutable
`oap/reports/048-a…051-b` reports), states that hashes/reports alone do
not prove implementation, and records purpose 052's fresh full53 ICA at
`1adf776` as a FAILED closure (48 IMPLEMENTED / 5 PARTIAL: SAR-016,
SAR-037, SAR-039, SAR-048, SAR-053; required ICA-GA-001/002; optional
ICA-GA-O1 separately recorded, not ordered), with the ICA-GA-001/002
remediation under issue #107 (order 052-a) and the pending fresh
independent full-architecture re-audit plus human milestone judgment.
No human meaning, stable ID, deferral, prior milestone history or
pending human milestone/release/exposure gate was altered; no
ARCHITECTURE/projection/role-law/CRITICAL edit; no fresh ADR. The
frozen independent audit report was copied BYTE-IDENTICALLY to
`docs/audit/reports/M-GROUP-AUTHORIZATION-1adf776.md`; in-repo SHA-256
verified `7b03025c4a4f2757b5a0d2e252878ed5f236594bdc2953e2bb57dd40a28c43f1`
(equal to the frozen source), and it is linked from P-08 Current state.
No raw private logs/probes/screens were committed.

### 5. Focused verification and exact report — PASSED

All product commands ran in the already-owned execution copy
`~/codex-work/slaif-auth-048-922064` (receipt CID
`7680db038ecebff114a19a929c6b2e3800d7274b23254a41707c2873d7c4067d`,
loopback 22708 verified up) after byte-for-byte sync and hash
verification of the allowed files; the separately owned ICA DB was not
touched. Exact commands and observed results:

- `./run.sh run -m pytest tests/test_staff_read_eligibility.py --ds=slaif_reservation.config.settings.test -p no:cacheprovider --no-cov -v`
  → **11 passed** (3.65s; re-run after formatting: 11 passed, 3.38s).
- `./run.sh run -m pytest tests/test_staff_read_eligibility.py tests/test_assets_web_api.py tests/test_api_schema.py …` → **44 passed** (15.81s); per-file: new 11, `test_assets_web_api.py` 22, `test_api_schema.py` 11.
- `./run.sh run -m pytest tests/test_product_entry.py tests/test_read_all_api.py tests/test_token_scope_authority.py …` → **50 passed, 1 warning** (14.39s); per-file: `test_product_entry.py` 17 passed + pre-existing intentional DATABASES-override UserWarning, `test_read_all_api.py` 23 passed, `test_token_scope_authority.py` 10 passed.
- Negative control (base source in execution copy only): main transition test **FAILED** at the exact 403 boundary (expected defect reproduction), patched files re-synced, full new file **11 passed** again.
- `./run.sh run ruff check .` → **All checks passed!**; `./run.sh run ruff format --check .` → **240 files already formatted**; `./run.sh run mypy src` → **Success: no issues found in 141 source files**; `git diff --check` → clean.
- `./run.sh run python manage.py check` → **System check identified no issues (0 silenced)**; `./run.sh run python manage.py makemigrations --check --dry-run` → **No changes detected**; `./run.sh run python manage.py spectacular --validate --fail-on-warn` → **passed, no warnings**, generated schema byte-identical to base `1adf776`.
- Changed Markdown link verified: P-08 link target `docs/audit/reports/M-GROUP-AUTHORIZATION-1adf776.md` exists; the frozen report contains only absolute GitHub action URLs (no relative local links); diff scope limited to the eight allowed paths.

No in-scope failures were observed; nothing was weakened, skipped or
blindly rerun. No local whole pytest/browser/OAP/operational/rehearsal/
HTTPS/Gunicorn/restore sweeps were run, per the order. No visual
redesign: no new screenshots required (MAX 0).

## CI (implementation head, observed)

At implementation head `69790665a827db9f214f469698048d262387d318`, all
five checks completed/success: CI run 39181839836 (quality, security,
container, test — test job `1254 passed, 1 warning in 569.02s`, the
pre-existing intentional warning) and oap run 39181839809
(oap-harness `Ran 160 tests in 30.743s / OK`). CI at the report head is
NOT observed at authoring and is not claimed.

## Strongest objection, limits, privacy and DHA

Strongest objection to altering these older read gates: a possible
integration depending on a service-account browser session. That
behavior violates the already-selected active-human contract (SAR-048/
SAR-053); proper human staff sessions and the explicit local public-docs
policy remain supported and are pinned by tests. This is a narrow D0
defect repair, not a new risk or product choice.

Limits: focused verification only, per the order's forbidden-sweep
list; full exact-head qualification is the normal five CI jobs (observed
green at the implementation head; report-head CI unobserved at
authoring). The repaired source still requires the fresh independent
full53 architecture-to-new-main re-audit and human milestone judgment;
nothing here closes the milestone, releases, deploys or authorizes any
real exposure. ICA-GA-O1 remains separately recorded and not ordered.

Privacy: synthetic users/tokens only; no credentials, verifiers,
peppers, cookies, CSRF values, bearer tokens, raw transcripts or private
artifacts appear in this report. The published audit report is the
frozen, strategically reviewed artifact, unchanged.

DHA: `Decision: NONE` — no CRITICAL entry created, appended or
disposed; no human adjudication performed.
