<!-- OAP-META
{
  "schema_version": 1,
  "kind": "report",
  "id": "053-b",
  "order_path": "oap/orders/053-b-authorization-documentation-truth.md",
  "order_sha256": "1dd4ce00eedb89aa4ba0a69540e81d08f4ab157f6a59e57537dc69cc8c141397",
  "repo": "ulfe-lmi/slaif-asset-reservation",
  "issue_number": 109,
  "pr_number": 110,
  "branch": "codex/109-oap-053-a-authorization-audit-publication",
  "implementation_head": "9283009cd91bef88eb4d3d7c967da532ffc0074c",
  "base_sha": "bddda89a5ddb428c64a36c7c2bd1f35cab2acbba",
  "result": "COMPLETE",
  "observed_implementation_ci": {
    "observed_head": "9283009cd91bef88eb4d3d7c967da532ffc0074c",
    "runs": [
      {
        "run_id": 39188930623,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "security": "success",
          "container": "success",
          "test": "success"
        }
      },
      {
        "run_id": 39188930586,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ],
    "test_job_summary": "1254 passed, 1 warning in 551.20s (0:09:11)",
    "warning": "tests/test_product_entry.py:568 UserWarning: Overriding setting DATABASES can lead to unexpected behavior (pre-existing, intentional DB-unavailable negative test, unrelated)",
    "oap_harness_summary": "Ran 160 tests in 31.963s / OK (job success)"
  },
  "prior_053a_report_head_ci": {
    "observed_head": "1af3927c81ab21a7c574bcd95781ee919046cf23",
    "runs": [
      {
        "run_id": 39187158840,
        "workflow": "CI",
        "jobs": {
          "quality": "success",
          "security": "success",
          "container": "success",
          "test": "success"
        }
      },
      {
        "run_id": 39187158822,
        "workflow": "oap",
        "jobs": {
          "oap-harness": "success"
        }
      }
    ]
  },
  "report_head_ci": "NOT YET OBSERVED AT AUTHORING"
}
-->

# 053-b — execution report: correct current authorization documentation before acceptance

Implementation head SHA: 9283009cd91bef88eb4d3d7c967da532ffc0074c
Report publication commit: SELF

## Identity and result

COMPLETE for order 053-b (D0, `Decision: NONE`) as the AMEND round on the
SAME issue #109 / PR #110 / branch
`codex/109-oap-053-a-authorization-audit-publication` as frozen 053-a, base
main `bddda89a5ddb428c64a36c7c2bd1f35cab2acbba` (verified equal to
`origin/main` before editing; all 11 order base source hashes verified
against working-tree bytes; governance revision
`14fc20b1ff52788974fd3f282322afc9d71362f9` present in history; frozen 053-a
implementation `a06ff983c4bf1264f20ef53be788051624cf236e` and prior
immutable report `1af3927c81ab21a7c574bcd95781ee919046cf23` confirmed in
history and on the remote). One implementation commit
`9283009cd91bef88eb4d3d7c967da532ffc0074c` (first parent the 053-a report
commit `1af3927c81ab21a7c574bcd95781ee919046cf23`) contains exactly the
four ordered documentation corrections plus the order bytes
(`oap/orders/053-b-authorization-documentation-truth.md`, state FINAL,
SHA-256
`1dd4ce00eedb89aa4ba0a69540e81d08f4ab157f6a59e57537dc69cc8c141397`) and the
`oap/active` pointer (exact `053-b` + LF, 6 bytes, verified with `xxd`).
PR #110 (open, base main, `Closes #109` retained) was amended: its
description now reflects the final doc-only change set of both rounds. No
new issue/PR, no merge, self-approval or auto-merge.

## Numbered acceptance evidence

### 1. Security/privacy wording matches ALL existing authorized readers — PASSED

`docs/security-model.md` no longer claims the authorized cross-user read
surfaces are "exactly two" with "No other route, scope or capability
discloses another owner's reservations." The corrected paragraph keeps the
two SELECTED application read-all interfaces explicit (All reservations
browser requires the current `view_all_reservations` capability; the bearer
`all-reservations` list/detail requires the `reservations:read_all` scope
AND the owner's current `view_all_reservations`, dual gate rechecked per
request, minimal payload) and states that they are the only /manage/ routes
and the only bearer routes that widen reservation visibility across owners
— while naming the independently permissioned paths that can reveal
reservation records to their authorized principals: the existing
Administration Reservation model View permission (staff admission plus the
per-model permission, no `view_all_reservations` needed) and the separately
granted `view_audit_history`/`export_audit_history` capabilities. It states
those independent grants disclose only what their own permissions allow and
never grant the application read-all interfaces, and that ordinary member
pages and the owner-scoped bearer routes stay private to their owners in
every combination of grants. Source-verified (read-only):
`src/slaif_reservation/reservations/admin.py` `ReservationAdmin` is a
read-only `ModelAdmin` whose `readonly_fields` include `requested_by_user`,
times, `purpose`, `cancellation_reason` and lifecycle fields, so an active
human staff holder of the `reservations.view_reservation` model View
permission (and no `view_all_reservations`) inspects another owner's
booking in the Administration — the same fact the order's private real-PG
probe established (Admin list/detail 200 vs `/manage/reservations/` 403).
No code/permission/source change and no user-directory API was introduced:
the implementation diff touches no `src/` file (see criterion 5).

### 2. Operator grant guide is accurate and product-oriented — PASSED

`docs/authorization.md`: BOTH stale Staff-only-Administration sentences
were corrected. (a) In "Available now" the management-capability bullet
now reads that `is_staff` admits `/admin/` (staff admission with the
existing per-model permissions) and, for a current active
non-service-account human, the legacy staff-session asset list/detail API
and — when enabled in private mode — the OpenAPI schema/docs endpoints,
while by itself conferring no management-area access, no `book_assets` and
no application read-all, with Administration record viewing additionally
requiring the per-model permissions. (b) In "Setting up grants" the
sentence now reads that the staff flag is required for /admin/ admission
(plus the existing per-model permissions to view Administration records)
and, for a current active non-service-account human, for the legacy
staff-session asset list/detail API and the OpenAPI schema/docs endpoints
when enabled in private mode, and that staff alone grants no /manage/
access, no `book_assets` and no application read-all. This matches the
implemented permission classes: `IsActiveStaffHuman`
(`is_active_human` and `is_staff`) gates the asset list/detail API and
`ApiDocumentationPermission` falls back to it when `API_DOCS_PUBLIC` is
off (`src/slaif_reservation/config/urls.py`, read-only). The
ten-capability matrix, example group setup, upgrade procedure, asset
allowed-group section, route inventory and bearer contract are untouched
(the diff shows only the targeted paragraphs). The FIRST SCREEN no longer
leads with the exact commit SHA or 53-row audit counts: it now explains the
implemented permissions in operator product language (what is implemented,
who can use what, what staff status does and does not grant). An automatic
first-screen scan for `bddda89`, `53 canonical`, `ICA`, `IMPLEMENTED`
returned clean. The current qualification report and freshness links plus
the human milestone caveat were preserved under a new short specialist
note, "## Specialist qualification evidence", placed after the functional
guide (before the final deferrals section), with a forward reference from
the first screen. Canonical PLAN scope/history was not removed (PLAN.md is
byte-identical to the audited base state, untouched this round).

### 3. API client contract loses the last ledger phrases and names the scope exception — PASSED

`docs/api-contract.md`: the header now reads "**Status:** implemented
contract for the controlled authenticated pilot" (no development-status
chronology). The "Work Order 0007 adds `blackout_conflict`" historical
lead-in is gone; `blackout_conflict` is listed among the stable codes and
the current behavior is stated: a reservation creation attempt that
overlaps an active maintenance blackout returns `409 blackout_conflict`
(detail "The requested time is unavailable."); the blackout's operational
text is not disclosed. Source-verified (read-only):
`src/slaif_reservation/api/reservation_views.py` maps
`BLACKOUT_CONFLICT` to `status.HTTP_409_CONFLICT` and
`_detail_for_code(BLACKOUT_CONFLICT)` returns exactly
"The requested time is unavailable.". The `GET /api/v1/me/` section now
states the actual semantics of
`MeAPIView.required_scopes = ()`: a valid bearer token is required and NO
additional action scope applies (any valid token may call this identity
endpoint; anonymous requests are rejected with the standard authentication
failure) — stated without implying anonymous access. In
`docs/security-model.md` the inherited blanket claim "Every bearer
endpoint checks explicit scopes" was replaced by the actual per-operation
scope rule (`availability:read`; `reservations:read` owner-scoped
list/detail; `reservations:create`/`cancel`/`release` owner-scoped
mutations; the `reservations:read_all` dual gate on the cross-user
surface), with `/api/v1/me/` named as the single identity exception;
`read_all` still has both gates. All API endpoints, wire names, scopes,
representations and error codes are unchanged (no source change; no token
secret disclosure introduced).

### 4. Authority chronology in freshness is truthful — PASSED

`docs/audit/qualification/M-GROUP-AUTHORIZATION-FRESHNESS.md`, section
"Selected human scope and development authority": the conflated sentence
is replaced with the actual chronology — the human first selected the
M-GROUP-AUTHORIZATION feature; SEPARATELY, AFTER the repository was
independently found to be PUBLIC on GitHub, the human explicitly confirmed
continued development publication/merges in this public repository,
reconciling the older "private repository" shorthand in the
architecture/PLAN history. The record reaffirms that no agent changed any
repository visibility, protection or setting, and that real application
exposure and deployment remain D2 — a separate human decision, not granted
by that confirmation. Only this factual provenance sentence changed in the
file (diff-verified); the audited base, digests, source-neutrality
assessment, evidence/limits and documentation-publication assessment
paragraphs are untouched, and no ICA-GA-O1 architecture/private-history
rewrite was performed. No fake human disposition or application exposure
permission appears.

### 5. Prove bounded correction and publish — PASSED

Changed paths this round (implementation commit `9283009`, diff vs its
first parent): exactly the four ordered documents
(`docs/authorization.md`, `docs/api-contract.md`,
`docs/security-model.md`,
`docs/audit/qualification/M-GROUP-AUTHORIZATION-FRESHNESS.md`) plus
`oap/active` and the new order file — 6 files, +221/−37, nothing else.
`git diff --name-only bddda89… 9283009 -- src/ tests/ pyproject.toml
uv.lock manage.py Dockerfile .dockerignore data/ compose*.yaml deploy/
.github/ ARCHITECTURE.md ARCHITECTURE-for-agents.md` is EMPTY: all
application source, tests, migrations, lockfile, settings, Docker/Compose/
deploy/workflow bytes and the full architecture/projection remain
byte-identical from the audited base through the final implementation
(053-a's own doc/PLAN/README/audit-report paths from its ordered scope were
already committed and audited at `a06ff98`/`1af3927` and are untouched by
this round). Both ICA report files re-verified byte-identical at commit
time: `docs/audit/reports/M-GROUP-AUTHORIZATION-bddda89.md`
SHA-256 `574024e2511af121f4665a89fa53cdfd0eefb12c816e82697ed2b9f724cd4177`
and `docs/audit/reports/M-GROUP-AUTHORIZATION-1adf776.md`
SHA-256 `7b03025c4a4f2757b5a0d2e252878ed5f236594bdc2953e2bb57dd40a28c43f1`
(before and after). Root README, PLAN, docs/README, both ICA reports,
architecture/projection/law/CRITICAL and all OAP helper bytes are
unchanged this round; no visibility-history rewrite beyond the one
ordered chronology sentence. Source-neutrality reassessment: the revisions
clarify already-implemented permissions, already-enforced behavior and
factual provenance only — no selected product meaning, stable requirement,
deferral or normative deployment assumption changed; prior
independent/runtime evidence is reused only under this verified byte
identity plus current-head CI. Focused local doc/static checks (actual):
link/anchor checker over the four changed documents and the order file
(18 relative links: files and in-document anchors all resolve, including
`api-contract.md#dual-gate-for-reservationsread_all`,
`authorization.md#management-route-inventory-enforced` and the new
specialist-note audit/freshness links); `git diff --check` clean;
stale-phrase scan (`exactly two`, `No other route`, `Work Order`,
`internal-alpha`, `alone admits`, `flag is required only`,
`explicitly authorized public-repository`) clean in all four documents.
NO local whole product/browser/OAP/operational/rehearsal/HTTPS/Gunicorn/
restore sweep was run (forbidden by the order). Normal FIVE CI checks at
the exact corrective implementation head observed completed/success (see
below), no missing/pending/skipped/cancelled. PR #110 description was
amended (REST API; the GraphQL `gh pr edit` path failed on the
classic-projects deprecation — no repository setting changed by that
failed call) to describe the final doc-only change set of both rounds and
keeps `Closes #109`. No merge/self-approval/auto-merge. This immutable
report is the final commit with the implementation head as first parent
and changes only this report file.

## Commands and results (actual)

- `git fetch origin && git rev-parse origin/main main` — both
  `bddda89a5ddb428c64a36c7c2bd1f35cab2acbba` (base verified before edit).
- 11 order base source hashes vs working tree (`sha256sum`) — all MATCH
  (see order metadata `source_hashes`).
- `sha256sum oap/orders/053-b-authorization-documentation-truth.md` —
  `1dd4ce00eedb89aa4ba0a69540e81d08f4ab157f6a59e57537dc69cc8c141397`.
- `xxd oap/active` — exactly `30 35 33 2d 62 0a` (`053-b` + LF, 6 bytes).
- Read-only source verification: `reservations/admin.py`
  (ReservationAdmin read-only model View; owner/purpose/lifecycle fields
  in `readonly_fields`), `api/reservation_views.py`
  (`MeAPIView.required_scopes = ()`; `BLACKOUT_CONFLICT` → 409; detail
  string), `config/urls.py` (`ApiDocumentationPermission` →
  `IsActiveStaffHuman` when `API_DOCS_PUBLIC` off).
- Link/anchor checker over the 5 Markdown files above — 18 links, 0
  missing files/anchors.
- `git diff --check` — clean.
- Stale-phrase grep across the four documents — no hits.
- First-screen scan of `docs/authorization.md` (before first `##`) for
  SHA/audit-count/ICA terms — no hits.
- `git diff --name-only bddda89… HEAD -- <source/projection/test/build
  list>` — EMPTY (source-neutrality through final implementation).
- `sha256sum` both ICA reports — unchanged at
  `574024e2…` / `7b03025c…` (before and after the commit).
- `git commit` → `9283009cd91bef88eb4d3d7c967da532ffc0074c`;
  `git push origin codex/109-oap-053-a-authorization-audit-publication` —
  remote head updated `1af3927…9283009`.
- `gh api -X PATCH …/pulls/110 -F body=@…` — PR #110 description amended
  (final doc-only change set; `Closes #109` retained).
- CI observation at exact implementation head
  `9283009cd91bef88eb4d3d7c967da532ffc0074c` (see next section).

Not run (by order scope): local product/browser/OAP-harness/operational/
rehearsal/HTTPS/Gunicorn/restore sweeps, any destructive cleanup, any real
host/service/DNS/TLS/identity/secret action — none authorized by this
order.

## Implementation CI (observed at authoring, exact head)

All five required checks at exact implementation head
`9283009cd91bef88eb4d3d7c967da532ffc0074c`, observed completed/success at
authoring, no missing/pending/skipped/cancelled:

- CI run 39188930623: `quality` success, `test` success (1254 passed, 1
  pre-existing warning in 551.20s — identical suite count to the 053-a
  heads, confirming source neutrality), `security` success, `container`
  success.
- OAP run 39188930586: `oap-harness` success (160 tests, OK in 31.963s).

## Prior 053-a report-head CI (historical fact, observed honestly)

The 053-a report commit `1af3927c81ab21a7c574bcd95781ee919046cf23` (the
historical prior head of this same PR) completed with ALL checks
success: CI run 39187158840 (quality, test, security, container) and OAP
run 39187158822 (oap-harness), observed via `gh pr checks 110` /
`gh run list` at authoring. It is recorded as an observed fact, not
treated as automatic acceptance; STRATEGY performs exact-head review.

## Report-head CI

NOT YET OBSERVED AT AUTHORING. No report-head check result is claimed; the
post-publication checks at the report commit are reported only in the
private execution receipt and do not amend this immutable report.

## Privacy, dependencies, DHA, limits

No tokens, peppers, verifiers, passwords, Authorization/cookie/CSRF
material, raw requests, private exports, free text or physical locators
entered this report or any committed artifact. No new dependency,
migration, workflow, repository setting or visibility change. DHA: NONE —
the order's `## Deferred human adjudication` declares `Decision: NONE` and
no CRITICAL entry was appended or adjudicated. Strongest limitation
(self-identified, matching the order's objection): overstating cross-user
privacy could lead operators to assign Administration/Audit grants
believing only the read-all capability reveals another owner's bookings;
the corrected wording names those independent grants explicitly while
keeping the enforced code and existing grants unchanged, and the
public-repository publication authority is attributed to the later
separate human confirmation, not invented as an original condition or a
deployment grant. Pending human judgments: M-GROUP-AUTHORIZATION
milestone acceptance and all real D2 deployment decisions (host/proxy
trust, DNS/TLS/firewall, identities/secrets, private data, physical
allocation) remain with the human; the fresh independent ICA at
`bddda89` remains the software/synthetic closure evidence for that
judgment.

## OAP-META note

The OAP-META block above carries the actual order path/SHA, issue/PR/
branch, implementation head, base SHA, result, the observed
implementation CI runs, and the honestly observed prior 053-a report-head
CI runs; `Report publication commit: SELF` resolves to the containing
report-only commit (first parent
`9283009cd91bef88eb4d3d7c967da532ffc0074c`, changing only this file).
